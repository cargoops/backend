import os
import boto3
import json

sqs = boto3.client('sqs')
QUEUE_URL = os.environ['BIN_RFID_SQS_QUEUE_URL']

def lambda_handler(event, context):
    # IoT Core Rule에서 전달된 메시지(event)는 기본적으로 JSON
    print("Received event:", event)
    # IoT Core Rule에서 Lambda로 넘길 때, event['rfid_id'] 형태로 오도록 설정
    rfid_id = event.get('rfid_id')
    bin_id = event.get('bin_id')
    binned_date = event.get('binned_date')
    package_id = event.get('package_id')
    
    if not rfid_id:
        return {"statusCode": 400, "body": "rfid_id missing"}
    message = json.dumps({"rfid_id": rfid_id, "bin_id": bin_id, "binned_date": binned_date, "package_id": package_id})
    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=message)
    return {"statusCode": 200, "body": "Message sent to SQS"}
