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
        print(f"Lambda function started - Request ID: {context.aws_request_id}")
        
        authorizer_context = event.get('requestContext', {}).get('authorizer', {})
        employee_id = authorizer_context.get('employee_id')
        role = authorizer_context.get('role')
        
        print(f"Authentication details - Employee ID: {employee_id}, Role: {role}")

        if not employee_id or not role:
            print("Unauthorized: Missing authentication details")
            return {
                'statusCode': 401,
                'body': json.dumps({'message': 'Unauthorized: Missing authentication details.'})
            }

        if role != 'packer':
            print(f"Forbidden: Role '{role}' is not authorized")
            return {
                'statusCode': 403,
                'body': json.dumps({'message': f"Forbidden: Role '{role}' is not authorized."})
            }
        
        body = json.loads(event.get('body', '{}'))
        packing_zone = body.get('packing_zone')
        
        print(f"Request body - Packing zone: {packing_zone}")

        if not packing_zone:
            print("Bad Request: packing_zone is required")
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Bad Request: packing_zone is required.'})
            }

        # Scan for slips ready for packing in the given zone
        print(f"Scanning for pick slips ready for packing in zone: {packing_zone}")
        scan_response = pick_slips_table.scan(
            FilterExpression=Attr('packing_zone').eq(packing_zone) & Attr('pick_slip_status').eq('READY-FOR-PACKING')
        )

        ready_slips = scan_response.get('Items', [])
        print(f"Found {len(ready_slips)} pick slips ready for packing")

        if not ready_slips:
            print(f"No pick slips ready for packing in zone {packing_zone}")
            return {
                'statusCode': 404,
                'body': json.dumps({'message': f'Not Found: No pick slips ready for packing in zone {packing_zone}.'})
            }

        # Find the oldest slip based on pick_slip_created_date
        oldest_slip = sorted(ready_slips, key=itemgetter('pick_slip_created_date'))[0]
        pick_slip_id = oldest_slip['pick_slip_id']
        
        print(f"Selected oldest pick slip: {pick_slip_id}")
        
        # Update the slip to start packing
        timestamp = datetime.now().isoformat()
        print(f"Updating pick slip {pick_slip_id} to PACKING-IN-PROGRESS status")
        
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

        print(f"Successfully updated pick slip {pick_slip_id} - Status: PACKING-IN-PROGRESS, Packer: {employee_id}")
        
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
        print(f"Error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        } 