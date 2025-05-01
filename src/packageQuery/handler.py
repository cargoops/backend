import json
import os
import boto3
from decimal import Decimal
from common.middleware.api_key_middleware import require_api_key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PACKAGES_TABLE'])

def convert_decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(i) for i in obj]
    return obj

@require_api_key('package:read')
def lambda_handler(event, context):
    try:
        params = event.get("queryStringParameters") or {}
        package_id = params.get("packageId")

        if not package_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, x-api-key'
                },
                'body': json.dumps({
                    'message': 'Missing packageId'
                })
            }

        response = table.get_item(Key={'packageId': package_id})
        item = response.get('Item')

        if not item:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, x-api-key'
                },
                'body': json.dumps({
                    'message': 'Package not found'
                })
            }

        item = convert_decimal_to_float(item)
        json = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, x-api-key'
            },
            'body': json.dumps({
                'data': item
            })
        }
        print("응답 결과: ", json)
        return json

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, x-api-key'
            },
            'body': json.dumps({
                'message': 'Internal Server Error'
            })
        }
