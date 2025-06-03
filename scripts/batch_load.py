# scripts/batch_load.py
import os
import csv
import boto3
from decimal import Decimal

# --- CONFIGURE THESE PATHS AS NEEDED ---
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
REGION = 'us-east-2'

def cast_value(val):
    """Convert to int or Decimal, else leave as str (treat empty as None)."""
    if val == '':
        return None
    # try int first
    try:
        return int(val)
    except ValueError:
        pass
    # then Decimal for floats
    try:
        return Decimal(val)
    except Exception:
        # fallback to original string
        return val

def batch_load(table_name, csv_path):
    print(f"> Loading {csv_path} → {table_name}...")
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table(table_name)

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        with table.batch_writer() as batch:
            for row in reader:
                item = {k: cast_value(v) for k, v in row.items() if cast_value(v) is not None}
                batch.put_item(Item=item)

    print(f"✔ Done: {table_name}")

if __name__ == '__main__':
    # data 디렉토리의 모든 csv 파일에 대해 처리
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.csv'):
            table_name = os.path.splitext(filename)[0]  # 확장자 제외한 파일명
            csv_path = os.path.join(DATA_DIR, filename)
            batch_load(table_name, csv_path)
