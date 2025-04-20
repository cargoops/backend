# {
#   "storingOrderId": "SO1234",
#   "airwayBillNumber": "AWB0001",
#   "billOfEntryId": "BOE0001"
# }

import json
import os
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
storing_orders_table = dynamodb.Table(os.environ['STORING_ORDERS_TABLE'])
packages_table = dynamodb.Table(os.environ['PACKAGES_TABLE'])

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
        response = storing_orders_table.get_item(Key={'storingOrderId': storing_order_id})
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

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'StoringOrder and related packages status updated to TQ'
                })
            }
        else:
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
