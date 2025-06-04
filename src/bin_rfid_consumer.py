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
        bin_id = body['bin_id']
        binned_date = body['binned_date']
        package_id = body['package_id']
        print(f"RFID ID: {rfid_id}, Bin ID: {bin_id}, Binned Date: {binned_date}, Package ID: {package_id}")
        
        # 1. package_id로 Packages 테이블 조회
        package_resp = packages_table.get_item(Key={'package_id': package_id})
        package = package_resp.get('Item')
        if not package:
            print(f"패키지 {package_id}를 찾을 수 없습니다.")
            continue
        
        # 2. bin_current and bin_allocation (e.g., "{""BIN1"":1,""BIN2"":2}")
        bin_current = package.get('bin_current')
        # bin_current가 None, 빈 문자열, dict, str 등 다양한 타입일 수 있으니 안전하게 처리
        if not bin_current or bin_current == "{}":
            bin_current = {}
        elif isinstance(bin_current, str):
            try:
                bin_current = json.loads(bin_current)
            except Exception as e:
                print(f"bin_current 파싱 에러: {e}")
                bin_current = {}
        if not isinstance(bin_current, dict):
            print(f"bin_current가 dict 타입이 아닙니다: {bin_current}")
            bin_current = {}
        # value가 str이면 int로 변환
        for k, v in bin_current.items():
            if not isinstance(v, int):
                try:
                    bin_current[k] = int(v)
                except Exception as e:
                    print(f"bin_current value 변환 에러: {e}")
                    bin_current[k] = 0

        bin_allocation = package.get('bin_allocation')
        if not bin_allocation or bin_allocation == "{}":
            print(f"패키지 {package_id}의 bin_allocation이 없습니다.")
            continue
        if isinstance(bin_allocation, str):
            try:
                bin_allocation = json.loads(bin_allocation)
            except Exception as e:
                print(f"bin_allocation 파싱 에러: {e}")
                continue
        if not isinstance(bin_allocation, dict):
            print(f"bin_allocation이 dict 타입이 아닙니다: {bin_allocation}")
            continue
        for k, v in bin_allocation.items():
            if not isinstance(v, int):
                try:
                    bin_allocation[k] = int(v)
                except Exception as e:
                    print(f"bin_allocation value 변환 에러: {e}")
                    bin_allocation[k] = 0

        bin_current[bin_id] = bin_current.get(bin_id, 0) + 1
        
        # 3. 상태 결정
        if bin_current == bin_allocation:
            new_status = 'BINNED'
        else:
            new_status = 'BINNING'
        
        # bin_current 문자열로 변환
        bin_current_str = json.dumps(bin_current)

        # 4. Packages 테이블 업데이트
        packages_table.update_item(
            Key={'package_id': package_id},
            UpdateExpression="SET bin_current = :bc, #s = :s",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':bc': bin_current_str, ':s': new_status}
        )
        print(f"패키지 {package_id}의 bin_current를 {bin_current}로, status를 {new_status}로 업데이트했습니다.")
        
        # 필요한 추가 필드가 있다면 여기에 추가
        items_table.put_item(Item={
            'rfid_id': rfid_id,
            'package_id': package_id,
            'status': 'BINNED',
            'bin_id': bin_id,
            'binned_date': binned_date
        })
        print(f"DynamoDB에 항목이 저장되었습니다: {rfid_id}")
    
    print("모든 레코드 처리가 완료되었습니다.")
    return {"statusCode": 200}
