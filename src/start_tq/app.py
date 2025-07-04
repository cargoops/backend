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
        else:
            body = json.loads(event.get('body', '{}'))
            role = body.get('role')
            employee_id = body.get('employee_id')
            path_params = event.get('pathParameters', {})
        package_id = path_params.get('package_id')
        if not all([employee_id, role, package_id]):
            return respond(400, {'message': 'Bad Request: Missing required parameters.'})

        # 패키지 조회
        package_response = packages_table.get_item(Key={'package_id': package_id}, ConsistentRead=True)
        package = package_response.get('Item')
        if not package:
            return respond(404, {'message': 'Package not found.'})

        # tq_start_date 업데이트
        timestamp = datetime.now().isoformat()
        packages_table.update_item(
            Key={'package_id': package_id},
            UpdateExpression="SET tq_start_date = :date",
            ExpressionAttributeValues={':date': timestamp}
        )

        # 최신 정보 다시 조회
        updated = packages_table.get_item(Key={'package_id': package_id}, ConsistentRead=True)
        return respond(200, {'data': updated.get('Item')})

    except Exception as e:
        print(f"Error: {e}")
        return respond(500, {'message': 'Internal server error'})
