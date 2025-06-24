import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('PICK_ORDERS_TABLE')
table = dynamodb.Table(table_name)
GSI_NAME = 'PickerStatusDateIndex'

def lambda_handler(event, context):
    try:
        params = event.get('queryStringParameters') or {}
        employee_id = params.get('employee_id')
        role = params.get('role')
        if not employee_id or not role:
            return {
                'statusCode': 401,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,GET'
                },
                'body': json.dumps({'message': 'Unauthorized: Missing employee_id or role.'})
            }
        if role != 'picker':
            return {
                'statusCode': 403,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,GET'
                },
                'body': json.dumps({'message': f"Forbidden: Role '{role}' is not authorized."})
            }

        # Use scan for testing purposes
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('picker_id').eq(employee_id) & boto3.dynamodb.conditions.Attr('pick_order_status').eq('READY-FOR-PICKING')
        )

        items = response.get('Items', [])

        if not items:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,GET'
                },
                'body': json.dumps({'message': 'No pick orders are currently ready for picking.'})
            }

        # Sort by order_created_date to find the oldest one
        items.sort(key=lambda x: x['order_created_date'])
        
        oldest_item = items[0]

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps(oldest_item, cls=DecimalEncoder)
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps({'message': 'Internal server error'})
        } 