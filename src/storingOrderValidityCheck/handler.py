# {
#   "storingOrderId": "SO1234",
#   "airwayBillNumber": "AWB0001",
#   "billOfEntryId": "BOE0001"
# }

import json
import os
import boto3
from decimal import Decimal
import logging
from common.middleware.api_key_middleware import require_api_key
from common.utils import make_response, handle_options

logger = logging.getLogger()
logger.setLevel(logging.INFO)


dynamodb = boto3.resource('dynamodb')

storing_orders_table = dynamodb.Table(os.environ['STORING_ORDERS_TABLE'])
packages_table = dynamodb.Table(os.environ['PACKAGES_TABLE'])

# 🔧 로거 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# AWS IoT 클라이언트 설정 (응답용)
iot_client = boto3.client('iot-data', region_name='us-east-2')

def publish_response_to_iot(payload):
    try:
        iot_client.publish(
            topic='scanner/response',
            qos=0,
            payload=json.dumps(payload)
        )
    except Exception as e:
        logger.error(f"🚨 응답 publish 실패: {e}")


def convert_decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(i) for i in obj]
    return obj

@require_api_key('storing:check')
def lambda_handler(event, context):
    # OPTIONS 요청 처리
    if event.get('httpMethod') == 'OPTIONS':
        return handle_options()

    try:
        # 요청 바디 파싱
        body = json.loads(event.get('body', '{}'))
        
        # 필수 필드 검증
        required_fields = ['storing_order_id', 'package_id', 'quantity']
        for field in required_fields:
            if field not in body:
                return make_response(400, {'message': f'Missing required field: {field}'})
        
        # 입고 주문 ID로 기존 주문 조회
        response = storing_orders_table.get_item(
            Key={
                'storing_order_id': body['storing_order_id']
            }
        )
        
        # 입고 주문이 존재하지 않는 경우
        if 'Item' not in response:
            return make_response(404, {'message': 'Storing order not found'})
            
        storing_order = response['Item']
        
        # 패키지 ID 검증
        if storing_order['package_id'] != body['package_id']:
            return make_response(400, {'message': 'Package ID does not match'})
            
        # 수량 검증
        if storing_order['quantity'] != Decimal(str(body['quantity'])):
            return make_response(400, {'message': 'Quantity does not match'})
            
        # 모든 검증 통과
        return make_response(200, {'message': 'Valid storing order'})
        
    except json.JSONDecodeError:
        return make_response(400, {'message': 'Invalid JSON in request body'})
        
    except Exception as e:
        print(f"Error: {e}")
        return make_response(500, {'message': 'Internal Server Error'})
