# scripts/batch_load.py
import os
import csv
import boto3
from decimal import Decimal
import ast

# --- CONFIGURE THESE PATHS AS NEEDED ---
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
REGION = 'us-east-2'

def cast_value(key, val):
    """Convert to int/Decimal, list/dict, else leave as str (empty as None)."""
    if val == '':
        return None
    if key and key.endswith('_id'):
        return str(val)
    # _date로 끝나는 필드는 .000000이 없으면 붙여줌
    if key and key.endswith('_date') and isinstance(val, str):
        # ISO8601 기본형: YYYY-MM-DDTHH:MM:SS 또는 YYYY-MM-DDTHH:MM:SS.000000
        if len(val) == 19 and val.count('-') == 2 and val.count(':') == 2 and 'T' in val:
            # 초단위까지만 있을 때
            return val + '.000000'
        # 이미 .000000이 붙어있으면 그대로 반환
        if len(val) > 19 and val[19:26] == '.00000':
            return val
    # 문자열일 때만 파싱 시도
    if isinstance(val, str):
        # Try to evaluate as a Python literal (for lists/dicts)
        if (val.startswith('[') and val.endswith(']')) or \
           (val.startswith('{') and val.endswith('}')):
            try:
                return ast.literal_eval(val)
            except (ValueError, SyntaxError):
                pass  # Not a valid literal, proceed to other checks

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
    # 이미 리스트/딕트 등은 그대로 반환
    return val

def batch_load(table_name, csv_path):
    print(f"> Loading {csv_path} → {table_name}...")
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table(table_name)

    # 테이블별 primary key 지정 (필요시 확장)
    primary_keys = {
        'PickSlips': 'pick_slip_id',
        'PickOrders': 'pick_order_id',
        # 다른 테이블도 필요시 추가
    }
    pk = primary_keys.get(table_name)
    seen_keys = set()

    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        with table.batch_writer() as batch:
            for row in reader:
                # PickOrders의 picker_id가 비어있으면 'PICK9999' 할당
                if table_name == 'PickOrders' and ('picker_id' not in row or row['picker_id'] == ''):
                    row['picker_id'] = 'PICK9999'
                item = {k: cast_value(k, v) for k, v in row.items() if k is not None and cast_value(k, v) is not None}
                # primary key가 없으면 skip
                if pk and (pk not in item or not item[pk]):
                    continue
                # 중복된 primary key는 skip
                if pk and item[pk] in seen_keys:
                    continue
                if pk:
                    seen_keys.add(item[pk])
                if item:
                    batch.put_item(Item=item)
    print(f"✔ Done: {table_name}")

if __name__ == '__main__':
    # data 디렉토리의 모든 csv 파일에 대해 처리
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.csv'):
            table_name = os.path.splitext(filename)[0]  # 확장자 제외한 파일명
            csv_path = os.path.join(DATA_DIR, filename)
            batch_load(table_name, csv_path)
