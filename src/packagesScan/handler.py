import json
import os
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PACKAGES_TABLE'])

def lambda_handler(event, context):
    try:
        # DynamoDB에서 모든 패키지를 스캔
        response = table.scan()
        
        # 응답 형식 설정
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully retrieved packages',
                'packages': response.get('Items', [])
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error retrieving packages',
                'error': str(e)
            })
        } 