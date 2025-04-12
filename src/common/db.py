import boto3
from . import config

dynamodb = boto3.resource('dynamodb', region_name=config.AWS_REGION)

def get_item(table_name: str, key: dict):
    table = dynamodb.Table(table_name)
    response = table.get_item(Key=key)
    return response.get('Item')

def scan_table(table_name: str):
    table = dynamodb.Table(table_name)
    response = table.scan()
    return response.get('Items', [])

def update_item(table_name: str, key: dict, update_expression: str, expression_values: dict, expression_names: dict = None):
    table = dynamodb.Table(table_name)
    params = {
        'Key': key,
        'UpdateExpression': update_expression,
        'ExpressionAttributeValues': expression_values,
        'ReturnValues': "ALL_NEW"
    }
    if expression_names:
        params['ExpressionAttributeNames'] = expression_names
    return table.update_item(**params)
