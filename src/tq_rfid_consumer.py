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
        package_id = body['package_id']
        tq_date = body['tq_date']
        print(f"RFID ID: {rfid_id}, Package ID: {package_id}, TQ Date: {tq_date}")
        
        # 1. Query Packages table with package_id
        package_resp = packages_table.get_item(Key={'package_id': package_id})
        package = package_resp.get('Item')
        if not package:
            print(f"Package {package_id} not found.")
            continue
        
        # 2. tq_scanned_quantity + 1
        tq_scanned_quantity = package.get('tq_scanned_quantity', 0) + 1
        quantity = package.get('quantity', 0)
        
        # 3. Determine status
        if tq_scanned_quantity == quantity:
            new_status = 'READY-FOR-BIN-ALLOCATION'
        else:
            new_status = 'TQ-CHECKING'
        
        # 4. Update Packages table
        packages_table.update_item(
            Key={'package_id': package_id},
            UpdateExpression="SET tq_scanned_quantity = :q, #s = :s",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':q': tq_scanned_quantity, ':s': new_status}
        )
        print(f"Updated package {package_id}'s tq_scanned_quantity to {tq_scanned_quantity} and status to {new_status}.")
        
        # Add additional fields if needed
        items_table.put_item(Item={
            'rfid_id': rfid_id,
            'package_id': package_id,
            'status': 'READY-FOR-BIN-ALLOCATION',
            'tq_date': tq_date
        })
        print(f"Item saved to DynamoDB: {rfid_id}")
    
    print("All records processing completed.")
    return {"statusCode": 200}
