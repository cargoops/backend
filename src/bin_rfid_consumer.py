import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
items_table = dynamodb.Table(os.environ['ITEMS_TABLE'])
packages_table = dynamodb.Table(os.environ['PACKAGES_TABLE'])

def lambda_handler(event, context):
    print("Lambda function has started.")
    print(f"Received event: {event}")
    
    for record in event['Records']:
        print(f"Processing record: {record}")
        body = json.loads(record['body'])
        rfid_id = body['rfid_id']
        bin_id = body['bin_id']
        binned_date = body['binned_date']
        package_id = body['package_id']
        print(f"RFID ID: {rfid_id}, Bin ID: {bin_id}, Binned Date: {binned_date}, Package ID: {package_id}")
        
        # 1. Query Packages table with package_id
        package_resp = packages_table.get_item(Key={'package_id': package_id}, ConsistentRead=True)
        package = package_resp.get('Item')
        if not package:
            print(f"Package {package_id} not found.")
            continue
        
        # 2. bin_current and bin_allocation (e.g., "{""BIN1"":1,""BIN2"":2}")
        bin_current = package.get('bin_current')
        # Handle bin_current safely as it can be None, empty string, dict, str, etc.
        if not bin_current or bin_current == "{}":
            bin_current = {}
        elif isinstance(bin_current, str):
            try:
                bin_current = json.loads(bin_current)
            except Exception as e:
                print(f"bin_current parsing error: {e}")
                bin_current = {}
        if not isinstance(bin_current, dict):
            print(f"bin_current is not a dict type: {bin_current}")
            bin_current = {}
        # Convert value to int if it's a string
        for k, v in bin_current.items():
            if not isinstance(v, int):
                try:
                    bin_current[k] = int(v)
                except Exception as e:
                    print(f"bin_current value conversion error: {e}")
                    bin_current[k] = 0

        bin_allocation = package.get('bin_allocation')
        if not bin_allocation or bin_allocation == "{}":
            print(f"Package {package_id} has no bin_allocation.")
            continue
        if isinstance(bin_allocation, str):
            try:
                bin_allocation = json.loads(bin_allocation)
            except Exception as e:
                print(f"bin_allocation parsing error: {e}")
                continue
        if not isinstance(bin_allocation, dict):
            print(f"bin_allocation is not a dict type: {bin_allocation}")
            continue
        for k, v in bin_allocation.items():
            if not isinstance(v, int):
                try:
                    bin_allocation[k] = int(v)
                except Exception as e:
                    print(f"bin_allocation value conversion error: {e}")
                    bin_allocation[k] = 0

        bin_current[bin_id] = bin_current.get(bin_id, 0) + 1
        
        # 3. Determine status
        if bin_current == bin_allocation:
            new_status = 'BINNED'
        else:
            new_status = 'BINNING'
        
        # Convert bin_current to string
        bin_current_str = json.dumps(bin_current)

        # 4. Update Packages table
        packages_table.update_item(
            Key={'package_id': package_id},
            UpdateExpression="SET bin_current = :bc, #s = :s",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':bc': bin_current_str, ':s': new_status}
        )
        print(f"Updated package {package_id}'s bin_current to {bin_current} and status to {new_status}.")
        
        # Add additional fields if needed
        items_table.put_item(Item={
            'rfid_id': rfid_id,
            'package_id': package_id,
            'status': 'BINNED',
            'bin_id': bin_id,
            'binned_date': binned_date
        })
        print(f"Item saved to DynamoDB: {rfid_id}")
    
    print("All records processing completed.")
    return {"statusCode": 200}
