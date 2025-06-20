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
        authorizer_context = event.get('requestContext', {}).get('authorizer', {})
        employee_id = authorizer_context.get('employee_id')
        role = authorizer_context.get('role')

        if not employee_id or not role:
            return {
                'statusCode': 401,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,GET'
                },
                'body': json.dumps({'message': 'Unauthorized: Missing employee_id or role from authorizer.'})
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

        response = table.query(
            IndexName=GSI_NAME,
            KeyConditionExpression=Key('picker_id').eq(employee_id),
            FilterExpression=Key('pick_order_status').eq('READY-FOR-PICKING'),
            ScanIndexForward=True,
            Limit=1
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

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps(items[0], cls=DecimalEncoder)
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