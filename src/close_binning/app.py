import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
packages_table_name = os.environ.get('PACKAGES_TABLE')
packages_table = dynamodb.Table(packages_table_name)

def lambda_handler(event, context):
    print(f"Lambda function started - Event: {json.dumps(event)}")
    try:
        authorizer_context = event.get('requestContext', {}).get('authorizer', {})
        role = authorizer_context.get('role')
        print(f"User role: {role}")

        if role != 'binner':
            print(f"Authorization failed - Role '{role}' is not authorized for this operation")
            return {
                'statusCode': 403,
                'body': json.dumps({'message': f"Forbidden: Role '{role}' is not authorized."})
            }

        path_params = event.get('pathParameters', {})
        package_id = path_params.get('package_id')
        print(f"Processing package_id: {package_id}")

        if not package_id:
            print("Bad Request: package_id is missing")
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Bad Request: package_id is required.'})
            }

        # Check if the package exists
        print(f"Checking if package {package_id} exists in DynamoDB")
        item_response = packages_table.get_item(Key={'package_id': package_id})
        if 'Item' not in item_response:
            print(f"Package {package_id} not found in database")
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Not Found: Package not found.'})
            }

        print(f"Package {package_id} found, updating status to BINNED")
        # Update the package status to BINNED
        timestamp = datetime.now().isoformat()
        packages_table.update_item(
            Key={'package_id': package_id},
            UpdateExpression="SET #status_attr = :status, binned_date = :date",
            ExpressionAttributeNames={'#status_attr': 'status'},
            ExpressionAttributeValues={
                ':status': 'BINNED',
                ':date': timestamp
            }
        )
        print(f"Successfully updated package {package_id} to BINNED status at {timestamp}")

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({'message': f'Package {package_id} has been binned successfully.'})
        }

    except Exception as e:
        print(f"Error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        } 