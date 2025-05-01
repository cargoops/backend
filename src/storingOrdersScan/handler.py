import json
import os
import boto3
from decimal import Decimal
from common.middleware.api_key_middleware import require_api_key
from common.utils import make_response, handle_options

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['STORING_ORDERS_TABLE'])

def convert_decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(i) for i in obj]
    return obj

@require_api_key('storing:scan')
def lambda_handler(event, context):
    print("=== 요청 정보 ===")
    print(f"HTTP Method: {event.get('httpMethod')}")
    print(f"Path: {event.get('path')}")
    print(f"Headers: {json.dumps(event.get('headers', {}), indent=2)}")
    print(f"Query Parameters: {json.dumps(event.get('queryStringParameters', {}), indent=2)}")
    
    # OPTIONS 요청 처리
    if event.get('httpMethod') == 'OPTIONS':
        print("OPTIONS 요청 처리")
        response = handle_options()
        print("=== OPTIONS 응답 ===")
        print(json.dumps(response, indent=2))
        return response
        
    try:
        print("DynamoDB scan 시작")
        response = table.scan()
        items = convert_decimal_to_float(response.get('Items', []))
        print(f"조회된 아이템 수: {len(items)}")
        print("첫 번째 아이템 샘플:", json.dumps(items[0] if items else {}, indent=2))
        
        api_response = make_response(200, {'data': items})
        print("=== 성공 응답 ===")
        print(json.dumps(api_response, indent=2))
        return api_response
        
    except Exception as e:
        print("=== 에러 발생 ===")
        print(f"에러 타입: {type(e).__name__}")
        print(f"에러 메시지: {str(e)}")
        import traceback
        print("스택 트레이스:")
        print(traceback.format_exc())
        
        error_response = make_response(500, {'message': 'Internal Server Error'})
        print("=== 에러 응답 ===")
        print(json.dumps(error_response, indent=2))
        return error_response
