import json
import os
import boto3
from boto3.dynamodb.conditions import Attr
from datetime import datetime
from operator import itemgetter
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
        employee_id = authorizer_context.get('employee_id')
        role = authorizer_context.get('role')

        if not employee_id or not role:
            return {
                'statusCode': 401,
                'body': json.dumps({'message': 'Unauthorized: Missing authentication details.'})
            }

        if role != 'packer':
            return {
                'statusCode': 403,
                'body': json.dumps({'message': f"Forbidden: Role '{role}' is not authorized."})
            }
        
        body = json.loads(event.get('body', '{}'))
        packing_zone = body.get('packing_zone')

        if not packing_zone:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Bad Request: packing_zone is required.'})
            }

        # Scan for slips ready for packing in the given zone
        scan_response = pick_slips_table.scan(
            FilterExpression=Attr('packing_zone').eq(packing_zone) & Attr('pick_slip_status').eq('READY-FOR-PACKING')
        )

        ready_slips = scan_response.get('Items', [])

        if not ready_slips:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': f'Not Found: No pick slips ready for packing in zone {packing_zone}.'})
            }

        # Find the oldest slip based on pick_slip_created_date
        oldest_slip = sorted(ready_slips, key=itemgetter('pick_slip_created_date'))[0]
        pick_slip_id = oldest_slip['pick_slip_id']
        
        # Update the slip to start packing
        timestamp = datetime.now().isoformat()
        update_response = pick_slips_table.update_item(
            Key={'pick_slip_id': pick_slip_id},
            UpdateExpression="SET pick_slip_status = :status, packing_start_date = :date, packer_id = :packer",
            ExpressionAttributeValues={
                ':status': 'PACKING-IN-PROGRESS',
                ':date': timestamp,
                ':packer': employee_id
            },
            ReturnValues="ALL_NEW"
        )

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps(update_response.get('Attributes'), cls=DecimalEncoder)
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        } 