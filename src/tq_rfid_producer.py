import os
import boto3
import json

sqs = boto3.client('sqs')
QUEUE_URL = os.environ['TQ_RFID_SQS_QUEUE_URL']

def lambda_handler(event, context):
    # IoT Core Rule에서 전달된 메시지(event)는 기본적으로 JSON
    print("Received event:", event)
    # IoT Core Rule에서 Lambda로 넘길 때, event['rfid_id'] 형태로 오도록 설정
    rfid_id = event.get('rfid_id')
    package_id = event.get('package_id')
    tq_date = event.get('tq_date')
    
    if not rfid_id:
        return {"statusCode": 400, "body": "rfid_id missing"}
    message = json.dumps({"rfid_id": rfid_id, "package_id": package_id, "tq_date": tq_date})
    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=message)
    return {"statusCode": 200, "body": "Message sent to SQS"}
