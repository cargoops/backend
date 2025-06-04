import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
items_table = dynamodb.Table(os.environ['ITEMS_TABLE'])
packages_table = dynamodb.Table(os.environ['PACKAGES_TABLE'])

def lambda_handler(event, context):
    print("Lambda 함수가 시작되었습니다.")
    print(f"받은 이벤트: {event}")
    
    for record in event['Records']:
        print(f"처리 중인 레코드: {record}")
        body = json.loads(record['body'])
        rfid_id = body['rfid_id']
        package_id = body['package_id']
        tq_date = body['tq_date']
        print(f"RFID ID: {rfid_id}, 패키지 ID: {package_id}, TQ 날짜: {tq_date}")
        
        # 1. package_id로 Packages 테이블 조회
        package_resp = packages_table.get_item(Key={'package_id': package_id})
        package = package_resp.get('Item')
        if not package:
            print(f"패키지 {package_id}를 찾을 수 없습니다.")
            continue
        
        # 2. tq_scanned_quantity + 1
        tq_scanned_quantity = package.get('tq_scanned_quantity', 0) + 1
        quantity = package.get('quantity', 0)
        
        # 3. 상태 결정
        if tq_scanned_quantity == quantity:
            new_status = 'READY-FOR-BIN-ALLOCATION'
        else:
            new_status = 'TQ-CHECKING'
        
        # 4. Packages 테이블 업데이트
        packages_table.update_item(
            Key={'package_id': package_id},
            UpdateExpression="SET tq_scanned_quantity = :q, #s = :s",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':q': tq_scanned_quantity, ':s': new_status}
        )
        print(f"패키지 {package_id}의 tq_scanned_quantity를 {tq_scanned_quantity}로, status를 {new_status}로 업데이트했습니다.")
        
        # 필요한 추가 필드가 있다면 여기에 추가
        items_table.put_item(Item={
            'rfid_id': rfid_id,
            'package_id': package_id,
            'status': 'READY-FOR-BIN-ALLOCATION',
            'tq_date': tq_date
        })
        print(f"DynamoDB에 항목이 저장되었습니다: {rfid_id}")
    
    print("모든 레코드 처리가 완료되었습니다.")
    return {"statusCode": 200}
