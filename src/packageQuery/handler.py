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

@require_api_key('package:query')
def lambda_handler(event, context):
    # OPTIONS 요청 처리
    if event.get('httpMethod') == 'OPTIONS':
        return handle_options()

    try:
        # 쿼리 파라미터에서 package_id 가져오기
        query_parameters = event.get('queryStringParameters', {})
        if not query_parameters or 'package_id' not in query_parameters:
            return make_response(400, {'message': 'package_id is required'})

        package_id = query_parameters['package_id']

        # DynamoDB에서 패키지 정보 조회
        response = table.get_item(
            Key={
                'package_id': package_id
            }
        )

        # 패키지가 존재하지 않는 경우
        if 'Item' not in response:
            return make_response(404, {'message': 'Package not found'})

        # Decimal 타입을 float로 변환
        item = convert_decimal_to_float(response['Item'])
        
        return make_response(200, {'data': item})

    except Exception as e:
        print(f"Error: {e}")
        return make_response(500, {'message': 'Internal Server Error'})
