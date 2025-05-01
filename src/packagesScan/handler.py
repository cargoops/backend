import json
import os
import boto3
from decimal import Decimal
from common.middleware.api_key_middleware import require_api_key
from common.utils import make_response, handle_options

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

@require_api_key('packages:scan')
def lambda_handler(event, context):
    # OPTIONS 요청 처리
    if event.get('httpMethod') == 'OPTIONS':
        return handle_options()
        
    try:
        response = table.scan()
        items = convert_decimal_to_float(response.get('Items', []))
        return make_response(200, {'data': items})
        
    except Exception as e:
        print(f"Error: {e}")
        return make_response(500, {'message': 'Internal Server Error'}) 