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
    try:
        if isinstance(event, dict) and 'body' in event:
            body = json.loads(event['body'])  # API Gateway 호출 시
        else:
            body = event  # AWS IoT 메시지 또는 기타 직접 전달
        storing_order_id = body.get("storingOrderId")
        input_awb = body.get("airwayBillNumber")
        input_boe = body.get("billOfEntryId")

        if not storing_order_id or not input_awb or not input_boe:
            logger.warning("⚠️ 필수 입력값 누락")  # 🟡 필수값 누락 경고 로그
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, x-api-key'
                },
                'body': json.dumps({
                    'message': 'Missing required fields'
                })
            }

        # 1. 테이블에서 Get
        logger.info(f"🔎 storingOrderId: {storing_order_id} 조회 시작")  # 🔵 DynamoDB 조회 로그
        response = storing_orders_table.get_item(Key={'storingOrderId': storing_order_id})
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
                    'message': 'StoringOrder not found'
                })
            }
        
        # 2. 데이터 비교
        db_awb = item.get("airwayBillNumber")
        db_boe = item.get("billOfEntryId")
        logger.info(f"📦 DB값: AWB={db_awb}, BOE={db_boe} / 입력값: AWB={input_awb}, BOE={input_boe}")

        if db_awb == input_awb and db_boe == input_boe:
            # 3. 상태 업데이트 (status -> 'TQ')
            storing_orders_table.update_item(
                Key={'storingOrderId': storing_order_id},
                UpdateExpression="SET #st = :tqStatus",
                ExpressionAttributeValues={":tqStatus": "TQ"},
                ExpressionAttributeNames={"#st": "status"}
            )

            # 4. 연결된 모든 패키지들의 상태도 TQ로 업데이트
            packages = item.get('packages', [])
            for package_id in packages:
                try:
                    packages_table.update_item(
                        Key={'packageId': package_id},
                        UpdateExpression="SET #st = :tqStatus",
                        ExpressionAttributeValues={":tqStatus": "TQ"},
                        ExpressionAttributeNames={"#st": "status"}
                    )
                except Exception as e:
                    print(f"Error updating package {package_id}: {e}")
                    # 개별 패키지 업데이트 실패는 전체 작업을 중단하지 않음
            # 👉 MQTT 요청인 경우에만 응답 발행
            if not ('body' in event and isinstance(event['body'], str)):
                publish_response_to_iot({
                    'message': '✅ StoringOrder status updated to TQ',
                    'storingOrderId': storing_order_id
            })



            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, x-api-key'
                },
                'body': json.dumps({
                    'message': 'StoringOrder and related packages status updated to TQ'
                })
            }
        else:
            logger.warning("❌ 값 불일치 - 상태 변경되지 않음")  # 🟡 값 불일치 로그
            
            # ❗ 여기 추가
            publish_response_to_iot({
                'message': '❌ airwayBillNumber or billOfEntryId mismatch',
                'storingOrderId': storing_order_id
            })
            
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, x-api-key'
                },
                'body': json.dumps({
                    'message': 'airwayBillNumber or billOfEntryId mismatch'
                })
            }

    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"🚨 예외 발생!: {e}")  # 🔴 예외 발생 로그
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
