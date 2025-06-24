import json, datetime
from boto3.dynamodb.conditions import Key
from common.utils import storing_table, packages_table, respond

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    role = body.get('role')
    employee_id = body.get('employee_id')
    if role != 'receiver':
        return respond(403, {'message':'Forbidden'})
    try:
        sid = body['storing_order_id']
        inv = body['invoice_number']
        bill= body['bill_of_entry_id']
        awb = body['airway_bill_number']
        qty = body['quantity']
    except Exception:
        return respond(400, {'message':'Invalid input'})

    # fetch order
    r = storing_table.get_item(Key={'storing_order_id': sid}, ConsistentRead=True)
    order = r.get('Item')
    if not order:
        return respond(404, {'message':'Order not found'})

    # check mismatches
    mismatches = []
    if order.get('invoice_number')    != inv:  mismatches.append('invoice_number')
    if order.get('bill_of_entry_id')  != bill: mismatches.append('bill_of_entry_id')
    if order.get('airway_bill_number')!= awb:  mismatches.append('airway_bill_number')
    if order.get('package_quantity')  != qty:  mismatches.append('package_quantity')

    if mismatches:
        detail = f"Mismatches: {','.join(mismatches)}"
        # mark FAILED
        storing_table.update_item(
            Key={'storing_order_id': sid},
            UpdateExpression="SET #s=:s, discrepancy_detail=:d, doc_inspection_result=:f, receiver_id=:e",
            ExpressionAttributeNames={'#s':'status'},
            ExpressionAttributeValues={':s':'INSPECTION-FAILED', ':d': detail, ':f': 'Failure', ':e': employee_id}
        )
        # update all packages
        packages_str = order.get('packages', '[]')
        package_ids = packages_str.strip('[]').split(';')
        for package_id in package_ids:
            if package_id:  # 빈 문자열이 아닌 경우에만 처리
                packages_table.update_item(
                    Key={'package_id': package_id},
                    UpdateExpression="SET #s=:s",
                    ExpressionAttributeNames={'#s':'status'},
                    ExpressionAttributeValues={':s':'INSPECTION-FAILED'}
                )
        return respond(400, {'message':'Inspection failed','discrepancy_detail': detail})

    # mark RECEIVED
    now = datetime.datetime.utcnow().isoformat()
    storing_table.update_item(
        Key={'storing_order_id': sid},
        UpdateExpression="SET #s=:s, received_date=:r, doc_inspection_result=:f, discrepancy_detail=:d, receiver_id=:e",
        ExpressionAttributeNames={'#s':'status'},
        ExpressionAttributeValues={':s':'RECEIVED', ':r': now, ':f': 'Success', ':d': '', ':e': employee_id}
    )
    # update packages → READY-FOR-TQ
    packages_str = order.get('package_ids', '[]')
    package_ids = packages_str.strip('[]').split(';')
    for package_id in package_ids:
        if package_id:  # 빈 문자열이 아닌 경우에만 처리
            packages_table.update_item(
                Key={'package_id': package_id},
                UpdateExpression="SET #s=:s",
                ExpressionAttributeNames={'#s':'status'},
                ExpressionAttributeValues={':s':'READY-FOR-TQ'}
            )
    return respond(200, {'message':'Order received'})