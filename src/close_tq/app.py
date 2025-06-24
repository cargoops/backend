import json
from datetime import datetime
from common.utils import packages_table, respond

def lambda_handler(event, context):
    try:
        if event.get('httpMethod', 'POST') == 'GET':
            params = event.get('queryStringParameters') or {}
            role = params.get('role')
            employee_id = params.get('employee_id')
            path_params = event.get('pathParameters', {})
            flag = params.get('flag')
            description = params.get('description', '')
        else:
            body = json.loads(event.get('body', '{}'))
            role = body.get('role')
            employee_id = body.get('employee_id')
            path_params = event.get('pathParameters', {})
            flag = body.get('flag')
            description = body.get('description', '')
        package_id = path_params.get('package_id')
        if not all([employee_id, role, package_id]):
            return respond(400, {'message': 'Bad Request: Missing required parameters.'})
        if role != 'tq_employee':
            return respond(403, {'message': f"Forbidden: Role '{role}' is not authorized."})

        # 1. Fetch the package and check its status
        package_response = packages_table.get_item(Key={'package_id': package_id}, ConsistentRead=True)
        package = package_response.get('Item')
        if not package:
            return respond(404, {'message': 'Package not found.'})

        timestamp = datetime.now().isoformat()
        if flag == 'fail':
            update_expr = "SET #s = :status, tq_fail_description = :desc, tq_close_date = :close_date, tq_date = :tq_date"
            expr_attr_names = {'#s': 'status'}
            expr_attr_values = {':status': 'TQ-QUALITY-CHECK-FAILED', ':desc': description, ':close_date': timestamp, ':tq_date': timestamp}
            packages_table.update_item(
                Key={'package_id': package_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values
            )
            return respond(200, {'message': f'Package {package_id} is now TQ-QUALITY-CHECK-FAILED.'})
        else:
            packages_table.update_item(
                Key={'package_id': package_id},
                UpdateExpression="SET #s = :status, ready_for_bin_allocation_date = :date, tq_date = :tq_date",
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':status': 'READY-FOR-BIN-ALLOCATION', ':date': timestamp, ':tq_date': timestamp}
            )
            return respond(200, {'message': f'Package {package_id} is now READY-FOR-BIN-ALLOCATION.'})

    except Exception as e:
        print(f"Error: {e}")
        return respond(500, {'message': 'Internal server error'})
