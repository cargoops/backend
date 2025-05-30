import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['ITEMS_TABLE'])  # 환경변수로 테이블명 전달 추천

def lambda_handler(event, context):
    print("Lambda 함수가 시작되었습니다.")
    print(f"받은 이벤트: {event}")
    
    for record in event['Records']:
        print(f"처리 중인 레코드: {record}")
        body = json.loads(record['body'])
        rfid_id = body['rfid_id']
        timestamp = body.get('timestamp')
        print(f"RFID ID: {rfid_id}, 타임스탬프: {timestamp}")
        
        # 필요한 추가 필드가 있다면 여기에 추가
        table.put_item(Item={
            'rfid_id': rfid_id,
            'timestamp': timestamp
        })
        print(f"DynamoDB에 항목이 저장되었습니다: {rfid_id}")
    
    print("모든 레코드 처리가 완료되었습니다.")
    return {"statusCode": 200}
