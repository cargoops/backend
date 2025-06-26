# scripts/single_table_load.py
import os
import csv
import boto3
from decimal import Decimal
import ast

# --- CONFIGURE THESE PATHS AS NEEDED ---
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
REGION = 'us-east-2'

def cast_value(val):
    """Convert to int/Decimal, list/dict, else leave as str (empty as None)."""
    if val == '':
        return None

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

def load_single_table(table_name, csv_filename=None):
    """
    특정 테이블에 해당하는 CSV 파일을 DynamoDB에 업로드합니다.
    
    Args:
        table_name (str): DynamoDB 테이블 이름
        csv_filename (str, optional): CSV 파일명. 지정하지 않으면 table_name.csv를 사용
    
    Returns:
        bool: 성공 여부
    """
    # CSV 파일명이 지정되지 않은 경우 테이블명.csv 사용
    if csv_filename is None:
        csv_filename = f"{table_name}.csv"
    
    csv_path = os.path.join(DATA_DIR, csv_filename)
    
    # 파일 존재 여부 확인
    if not os.path.exists(csv_path):
        print(f"❌ Error: CSV file not found: {csv_path}")
        return False
    
    print(f"> Loading {csv_filename} → {table_name}...")
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        table = dynamodb.Table(table_name)

        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            with table.batch_writer() as batch:
                for row in reader:
                    item = {k: cast_value(v) for k, v in row.items() if k is not None and cast_value(v) is not None}
                    if item:
                        batch.put_item(Item=item)

        print(f"✔ Done: {table_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error loading {table_name}: {str(e)}")
        return False

def load_multiple_tables(table_list):
    """
    여러 테이블을 순차적으로 업로드합니다.
    
    Args:
        table_list (list): 테이블명 리스트 또는 (테이블명, CSV파일명) 튜플 리스트
    
    Returns:
        dict: 각 테이블별 성공/실패 결과
    """
    results = {}
    
    for table_info in table_list:
        if isinstance(table_info, tuple):
            table_name, csv_filename = table_info
        else:
            table_name = table_info
            csv_filename = None
            
        results[table_name] = load_single_table(table_name, csv_filename)
    
    return results

def list_available_csvs():
    """
    data 디렉토리에 있는 모든 CSV 파일 목록을 반환합니다.
    
    Returns:
        list: CSV 파일명 리스트
    """
    if not os.path.exists(DATA_DIR):
        print(f"❌ Error: Data directory not found: {DATA_DIR}")
        return []
    
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
    return sorted(csv_files)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python single_table_load.py <table_name> [csv_filename]")
        print("  python single_table_load.py --list  # 사용 가능한 CSV 파일 목록")
        print("\n예시:")
        print("  python single_table_load.py Items")
        print("  python single_table_load.py Items Items.csv")
        print("  python single_table_load.py Products custom_products.csv")
        sys.exit(1)
    
    if sys.argv[1] == '--list':
        print("사용 가능한 CSV 파일:")
        for csv_file in list_available_csvs():
            table_name = os.path.splitext(csv_file)[0]
            print(f"  {csv_file} → {table_name}")
        sys.exit(0)
    
    table_name = sys.argv[1]
    csv_filename = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = load_single_table(table_name, csv_filename)
    sys.exit(0 if success else 1)