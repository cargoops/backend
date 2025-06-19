import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['PICK_SLIPS_TABLE']
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    # Extract claims from the authorizer context
    claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    role = claims.get('custom:role')

    # Check if the user role is admin
    if role != 'admin':
        return {
            'statusCode': 403,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps({'message': 'Forbidden: You do not have permission to access this resource.'})
        }

    try:
        response = table.scan()
        items = response.get('Items', [])
        
        # Handle pagination if the table is large
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps(items)
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps({'message': 'Internal Server Error'})
        } 