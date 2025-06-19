import json, datetime
from common.utils import packages_table, respond
from boto3.dynamodb.conditions import Attr

def lambda_handler(event, context):
    # Authentication and Authorization Check
    auth = event['requestContext'].get('authorizer', {})
    if auth.get('role') != 'tq_employee':
        return respond(403, {'message': 'Unauthorized. (role != tq_employee)'})

    # Change all records with status TQ-CHECKING to TQ-FAILED
    scan_kwargs = {
        'FilterExpression': Attr('status').eq('TQ-CHECKING')
    }
    done = False
    start_key = None
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        response = packages_table.scan(**scan_kwargs)
        for item in response.get('Items', []):
            packages_table.update_item(
                Key={'package_id': item['package_id']},
                UpdateExpression="SET #s=:s",
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':s': 'TQ-FAILED'}
            )
        start_key = response.get('LastEvaluatedKey', None)
        done = start_key is None

    # Parse Input
    try:
        body = json.loads(event['body'])
        package_id = body['package_id']
        employee_id = body['employee_id']
        flag = body['flag']
    except Exception:
        return respond(400, {'message': 'Invalid input values.'})

    # Retrieve Package Record
    r = packages_table.get_item(Key={'package_id': package_id})
    package = r.get('Item')
    if not package:
        return respond(404, {'message': 'Package with this package_id not found.'})

    # Status Check and Change
    if package.get('status') != 'READY-FOR-TQ':
        return respond(400, {'message': f"Package status is not READY-FOR-TQ. (Current status: {package.get('status')})"})

    now = datetime.datetime.utcnow().isoformat()

    # Status Update
    if flag == 'pass':
        packages_table.update_item(
            Key={'package_id': package_id},
            UpdateExpression="SET #s=:s, #t=:t, #d=:d",
            ExpressionAttributeNames={'#s': 'status', '#t': 'tq_staff_id', '#d': 'tq_quality_check_date'},
            ExpressionAttributeValues={':s': 'READY-FOR-RFID-ATTACH', ':t': employee_id, ':d': now}
        )
        return respond(200, {'message': 'Package status changed to READY-FOR-RFID-ATTACH.'})
    elif flag == 'fail':
        packages_table.update_item(
            Key={'package_id': package_id},
            UpdateExpression="SET #s=:s, #t=:t, #d=:d",
            ExpressionAttributeNames={'#s': 'status', '#t': 'tq_staff_id', '#d': 'tq_quality_check_date'},
            ExpressionAttributeValues={':s': 'TQ-QUALITY-CHECK-FAILED', ':t': employee_id, ':d': now}
        )
        return respond(200, {'message': 'Package status changed to TQ-QUALITY-CHECK-FAILED.'})
    else:
        return respond(400, {'message': 'Flag must be either pass or fail.'})
