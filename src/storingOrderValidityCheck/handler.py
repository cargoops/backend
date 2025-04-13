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

logger = logging.getLogger()
logger.setLevel(logging.INFO)


dynamodb = boto3.resource('dynamodb')
# 🔧 로거 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

table = dynamodb.Table(os.environ['STORING_ORDERS_TABLE'])

def convert_decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(i) for i in obj]
    return obj

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        storing_order_id = body.get("storingOrderId")
        input_awb = body.get("airwayBillNumber")
        input_boe = body.get("billOfEntryId")

        if not storing_order_id or not input_awb or not input_boe:
            logger.warning("⚠️ 필수 입력값 누락")  # 🟡 필수값 누락 경고 로그
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'Missing required fields'
                })
            }

        # 1. 테이블에서 Get
        logger.info(f"🔎 storingOrderId: {storing_order_id} 조회 시작")  # 🔵 DynamoDB 조회 로그
        response = table.get_item(Key={'storingOrderId': storing_order_id})
        item = response.get('Item')

        if not item:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
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
            logger.info("✅ 값 일치 - 상태를 'TQ'로 업데이트")  # 🟢 상태 변경 로그
            table.update_item(
                Key={'storingOrderId': storing_order_id},
                UpdateExpression="SET #st = :tqStatus",
                ExpressionAttributeValues={":tqStatus": "TQ"},
                ExpressionAttributeNames={"#st": "status"}
            )
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'StoringOrder status updated to TQ'
                })
            }
        else:
            logger.warning("❌ 값 불일치 - 상태 변경되지 않음")  # 🟡 값 불일치 로그
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'airwayBillNumber or billOfEntryId mismatch'
                })
            }

    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"🚨 예외 발생: {e}")  # 🔴 예외 발생 로그
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Internal Server Error'
            })
        }
