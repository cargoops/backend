import os, json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb        = boto3.resource('dynamodb')
storing_table   = dynamodb.Table(os.environ['STORING_ORDERS_TABLE'])
packages_table  = dynamodb.Table(os.environ['PACKAGES_TABLE'])
api_keys_table  = dynamodb.Table(os.environ['API_KEYS_TABLE'])

def get_api_key_record(api_key: str):
    resp = api_keys_table.get_item(Key={'api_key': api_key})
    return resp.get('Item')

def respond(status_code: int, body: dict):
    print(body)
    return {
        'statusCode': status_code,
        'headers': {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"
        },
        'body': json.dumps(body, default=str)
    }
