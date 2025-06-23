import os, json
import boto3
from boto3.dynamodb.conditions import Key

print("Initializing DynamoDB resources...")
dynamodb        = boto3.resource('dynamodb')
storing_table   = dynamodb.Table(os.environ['STORING_ORDERS_TABLE'])
packages_table  = dynamodb.Table(os.environ['PACKAGES_TABLE'])
items_table     = dynamodb.Table(os.environ['ITEMS_TABLE'])
api_keys_table  = dynamodb.Table(os.environ['API_KEYS_TABLE'])
bins_table      = dynamodb.Table(os.environ['BINS_TABLE'])
products_table  = dynamodb.Table(os.environ['PRODUCTS_TABLE'])
inventory_table = dynamodb.Table(os.environ['INVENTORY_TABLE'])

print("DynamoDB resources initialized successfully")

def get_api_key_record(api_key: str):
    print(f"Fetching API key record for key: {api_key}")
    resp = api_keys_table.get_item(Key={'api_key': api_key}, ConsistentRead=True)
    return resp.get('Item')

def respond(status_code: int, body: dict):
    print(f"Responding with status code: {status_code}")
    print(f"Response body: {body}")
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
