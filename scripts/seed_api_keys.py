# seed_api_keys.py
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ApiKeys')

items = [
    {
        'api_key': 'rcv-7fa3d1b2',     # 실제 환경에선 UUID 등 충분히 랜덤한 값을 사용하세요
        'employee_id': 'RCV2054',
        'role': 'receiver'
    },
    {
        'api_key': 'tq-4c9d8e2f',
        'employee_id': 'TQ3101',
        'role': 'tq_employee'
    },
    {
        'api_key': 'adm-12345678',
        'employee_id': 'ADMIN01',
        'role': 'admin'
    },
    {
        'api_key': 'adm',
        'employee_id': 'ADMIN02',
        'role': 'admin'
    }
]

for item in items:
    table.put_item(Item=item)

print("Seed complete.")
