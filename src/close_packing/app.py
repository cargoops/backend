import json
import os
import boto3
from datetime import datetime
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)

dynamodb = boto3.resource('dynamodb')
pick_slips_table_name = os.environ.get('PICK_SLIPS_TABLE')
pick_slips_table = dynamodb.Table(pick_slips_table_name)

def lambda_handler(event, context):
    try:
        authorizer_context = event.get('requestContext', {}).get('authorizer', {})
        role = authorizer_context.get('role')

        if role != 'packer':
            return {
                'statusCode': 403,
                'body': json.dumps({'message': f"Forbidden: Role '{role}' is not authorized."})
            }

        path_params = event.get('pathParameters', {})
        pick_slip_id = path_params.get('pick_slip_id')

        if not pick_slip_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Bad Request: pick_slip_id is required.'})
            }

        # Check if the pick slip exists first
        item_response = pick_slips_table.get_item(Key={'pick_slip_id': pick_slip_id})
        if 'Item' not in item_response:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Not Found: Pick slip not found.'})
            }

        # Update the slip status to READY-FOR-DISPATCH
        timestamp = datetime.now().isoformat()
        pick_slips_table.update_item(
            Key={'pick_slip_id': pick_slip_id},
            UpdateExpression="SET pick_slip_status = :status, packed_date = :date",
            ExpressionAttributeValues={
                ':status': 'READY-FOR-DISPATCH',
                ':date': timestamp
            }
        )

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({'message': f'Pick slip {pick_slip_id} has been closed and is ready for dispatch.'})
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        } 