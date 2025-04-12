import os

AWS_REGION = os.environ.get("MY_REGION", "us-east-2")

# 테이블 이름들도 환경변수로 빼두면 나중에 쉽게 변경 가능
STORING_ORDERS_TABLE = os.environ.get("STORING_ORDERS_TABLE", "StoringOrders")
PACKAGES_TABLE = os.environ.get("PACKAGES_TABLE", "Packages")
PICKSLIPS_TABLE = os.environ.get("PICKSLIPS_TABLE", "PickSlips")