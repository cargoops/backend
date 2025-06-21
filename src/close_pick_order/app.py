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
pick_orders_table_name = os.environ.get('PICK_ORDERS_TABLE')
pick_slips_table_name = os.environ.get('PICK_SLIPS_TABLE')
pick_orders_table = dynamodb.Table(pick_orders_table_name)
pick_slips_table = dynamodb.Table(pick_slips_table_name)
GSI_NAME = 'PickSlipIdIndex'

def lambda_handler(event, context):
    try:
        authorizer_context = event.get('requestContext', {}).get('authorizer', {})
        employee_id = authorizer_context.get('employee_id')
        role = authorizer_context.get('role')
        
        path_params = event.get('pathParameters', {})
        pick_order_id = path_params.get('pick_order_id')

        if not all([employee_id, role, pick_order_id]):
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Bad Request: Missing required parameters.'})
            }

        if role != 'picker':
            return {
                'statusCode': 403,
                'body': json.dumps({'message': f"Forbidden: Role '{role}' is not authorized."})
            }

        # 1. Fetch the pick order and check its status and owner
        order_response = pick_orders_table.get_item(Key={'pick_order_id': pick_order_id}, ConsistentRead=True)
        order = order_response.get('Item')

        if not order:
            return {'statusCode': 404, 'body': json.dumps({'message': 'Pick order not found.'})}

        if order.get('picker_id') != employee_id:
            return {'statusCode': 403, 'body': json.dumps({'message': 'Forbidden: You are not assigned to this pick order.'})}
            
        if order.get('pick_order_status') != 'READY-FOR-PICKING':
            return {'statusCode': 400, 'body': json.dumps({'message': f"Bad Request: Pick order status is '{order.get('pick_order_status')}', not 'READY-FOR-PICKING'."})}

        # 2. Update the pick order status to CLOSE
        timestamp = datetime.now().isoformat()
        update_response = pick_orders_table.update_item(
            Key={'pick_order_id': pick_order_id},
            UpdateExpression="SET pick_order_status = :status, picked_date = :date",
            ExpressionAttributeValues={':status': 'CLOSE', ':date': timestamp},
            ReturnValues="ALL_NEW"
        )
        updated_order = update_response.get('Attributes', {})
        pick_slip_id = updated_order.get('pick_slip_id')

        # 3. Check if all orders for the same pick slip are closed
        # Use scan for simplicity and to ensure data consistency after update
        related_orders_response = pick_orders_table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('pick_slip_id').eq(pick_slip_id)
        )
        related_orders = related_orders_response.get('Items', [])
        
        all_closed = all(o.get('pick_order_status') == 'CLOSE' for o in related_orders)

        response_message = {'message': 'Pick order closed successfully.'}

        # 4. If all are closed, update the pick slip status
        if all_closed and related_orders:
            pick_slips_table.update_item(
                Key={'pick_slip_id': pick_slip_id},
                UpdateExpression="SET pick_slip_status = :status, ready_for_packing_date = :date",
                ExpressionAttributeValues={':status': 'READY-FOR-PACKING', ':date': timestamp}
            )
            response_message['pick_slip_status'] = 'READY-FOR-PACKING'

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps(response_message, cls=DecimalEncoder)
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        } 