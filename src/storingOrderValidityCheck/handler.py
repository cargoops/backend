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

        if db_awb == input_awb and db_boe == input_boe:
            # 3. 상태 업데이트 (status -> 'TQ')
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
