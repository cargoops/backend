# scripts/batch_load.py
import os
import csv
import boto3
from decimal import Decimal

# --- CONFIGURE THESE PATHS AS NEEDED ---
STORING_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'StoringOrders.csv')
PACKAGES_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'Packages.csv')
ITEMS_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'Items.csv')
REGION       = 'us-east-2'

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
    batch_load('StoringOrders', STORING_CSV)
    batch_load('Packages',      PACKAGES_CSV)
    batch_load('Items',      ITEMS_CSV)
