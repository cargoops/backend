import json
import random
import datetime
from common.utils import packages_table, items_table, bins_table, products_table, respond
import os
import boto3

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    
    # 1. Authentication and Authorization Check
    auth = event['requestContext'].get('authorizer', {})
    print(f"Auth Info: {auth}")
    if auth.get('role') != 'binner':
        print(f"Authorization Error: role={auth.get('role')}")
        return respond(403, {'message': 'Unauthorized. (role != binner)'})

    employee_id = auth.get('employee_id')
    if not employee_id:
        return respond(403, {'message': 'Unauthorized. (employee_id not found in token)'})

    # 2. Parse Input Values
    try:
        body = json.loads(event['body'])
        package_id = body['package_id']
        print(f"Input Values: package_id={package_id}, employee_id={employee_id}")
    except Exception as e:
        print(f"Input Parsing Error: {str(e)}")
        return respond(400, {'message': 'Invalid input values.'})

    # 3. Retrieve Package Record
    print(f"Retrieving Package: package_id={package_id}")
    r = packages_table.get_item(Key={'package_id': package_id})
    package = r.get('Item')
    if not package:
        print("Package Not Found")
        return respond(404, {'message': 'Package with this package_id not found.'})

    quantity = package.get('quantity')
    product_id = package.get('product_id')
    print(f"Package Info: quantity={quantity}, product_id={product_id}")
    
    product = products_table.get_item(Key={'product_id': product_id})
    if not product:
        print(f"Product Not Found: product_id={product_id}")
        return respond(404, {'message': 'Product with this product_id not found.'})
    
    product_volume = product.get('Item', {}).get('volume')
    if product_volume is None:
        print("Product Volume Info Missing")
        return respond(400, {'message': 'Product volume information is missing.'})
    total_volume = product_volume * quantity
    print(f"Volume Info: product_volume={product_volume}, total_volume={total_volume}")

    rfid_ids_str = package.get('rfid_ids', '').strip('[]')
    rfid_ids = [x for x in rfid_ids_str.split(';') if x]
    status = package.get('status')
    print(f"RFID and Status: rfid_ids={rfid_ids}, status={status}")

    # 4. Status Check
    if status != 'READY-FOR-BIN-ALLOCATION':
        print(f"Status Error: current status={status}")
        return respond(400, {'message': f"Package status is not READY-FOR-BIN-ALLOCATION. (Current status: {status})"})

    # 5. Space Availability Check
    if quantity is None:
        print("Quantity Info Missing")
        return respond(400, {'message': 'Package quantity information is missing.'})

    # 6. BIN Allocation
    bins_response = bins_table.scan()
    bins = bins_response.get('Items', [])
    bins.sort(key=lambda x: x.get('availability_vol', 0), reverse=True)
    bin_allocation = {}
    remaining_quantity = int(quantity)
    # Check if entire quantity can fit in a single bin
    for bin in bins:
        if bin.get('availability_vol', 0) >= total_volume:
            bin_id = bin['bin_id']
            bin_allocation = {bin_id: remaining_quantity}
            print(f"Single BIN Allocation: bin_id={bin_id}, quantity={remaining_quantity}")
            remaining_quantity = 0
            break
    else:
        print("Starting Distribution Across Multiple BINs")
        # Distribute across multiple bins
        for bin in bins:
            if remaining_quantity <= 0:
                break
            bin_id = bin['bin_id']
            bin_volume = bin.get('availability_vol', 0)
            max_items = min(remaining_quantity, int(bin_volume / product_volume))
            if max_items > 0:
                bin_allocation[bin_id] = max_items
                remaining_quantity -= max_items
    if remaining_quantity > 0:
        print(f"Insufficient Space: remaining_quantity={remaining_quantity}")
        return respond(400, {'message': 'Not enough space for bin allocation.'})
    
    bin_allocation_str = json.dumps(bin_allocation)
    now = datetime.datetime.utcnow().isoformat()
    # Update availability_vol for each BIN
    for bin_id, allocated_qty in bin_allocation.items():
        used_volume = allocated_qty * product_volume
        bins_table.update_item(
            Key={'bin_id': bin_id},
            UpdateExpression="SET availability_vol = availability_vol - :used",
            ExpressionAttributeValues={':used': used_volume}
        )

    # Update Package Table
    packages_table.update_item(
        Key={'package_id': package_id},
        UpdateExpression="SET bin_allocation=:ba, binner_id=:bid, bin_allocation_date=:dt, #s=:s",
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={
            ':ba': bin_allocation_str,
            ':bid': employee_id,
            ':dt': now,
            ':s': 'READY-FOR-BINNING'
        }
    )

    # 7. Update Items Table Status for Each RFID
    print(f"Updating RFID Status... (Total: {len(rfid_ids)})")
    for rfid_id in rfid_ids:
        items_table.update_item(
            Key={'rfid_id': rfid_id},
            UpdateExpression="SET #s=:s",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'READY-FOR-BINNING'}
        )

    print("=== Bin Allocation Lambda Completed ===")
    return respond(200, {'message': 'Bin allocation completed', 'bin_allocation': bin_allocation})
