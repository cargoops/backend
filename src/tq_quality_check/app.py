import json
from common.utils import packages_table, respond

def lambda_handler(event, context):
    # 인증 및 권한 체크
    auth = event['requestContext'].get('authorizer', {})
    if auth.get('role') != 'tq_employee':
        return respond(403, {'message': '권한이 없습니다. (role != tq_employee)'})

    # 인풋 파싱
    try:
        body = json.loads(event['body'])
        package_id = body['package_id']
    except Exception:
        return respond(400, {'message': '입력값이 올바르지 않습니다.'})

    # 패키지 레코드 조회
    r = packages_table.get_item(Key={'package_id': package_id})
    package = r.get('Item')
    if not package:
        return respond(404, {'message': '해당 package_id의 패키지를 찾을 수 없습니다.'})

    # 상태 확인 및 변경
    if package.get('status') != 'READY-FOR-TQ':
        return respond(400, {'message': f"패키지 상태가 READY-FOR-TQ가 아닙니다. (현재 상태: {package.get('status')})"})

    # 상태 업데이트
    packages_table.update_item(
        Key={'package_id': package_id},
        UpdateExpression="SET #s=:s",
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':s': 'READY-FOR-RFID-ATTACH'}
    )
    return respond(200, {'message': '패키지 상태가 READY-FOR-RFID-ATTACH로 변경되었습니다.'})
