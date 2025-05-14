import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

# 초기화
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# ✅ 실제 DynamoDB 기반 Glue 테이블 목록
tables = [
    "dynamodb_bins",
    "dynamodb_inventory",
    "dynamodb_items",
    "dynamodb_packages",
    "dynamodb_phonitale_user_responses",
    "dynamodb_pickorders",
    "dynamodb_pickslips",
    "dynamodb_products",
    "dynamodb_receivingpackages",
    "dynamodb_storingorders"
]

# 출력 버킷 설정
output_bucket = "cargoops-glue-etl-output"

# 각 테이블 처리
for table in tables:
    try:
        print(f"📊 {table} 테이블 처리 시작...")
        
        # Glue 데이터 카탈로그에서 데이터 프레임 생성
        dyf = glueContext.create_dynamic_frame.from_catalog(
            database="my_dynamodb_catalog",
            table_name=table
        )
        
        # 레코드 수 확인
        count = dyf.count()
        if count == 0:
            print(f"⚠️ 테이블 '{table}'은 비어 있어서 건너뜁니다.")
            continue
        
        print(f"🔢 {table} 레코드 수: {count}")
        
        # 스키마 최적화 (선택사항)
        # dyf = ResolveChoice.apply(dyf, specs = [("someField", "cast:string")])
        
        # S3에 Parquet 형식으로 저장
        output_path = f"s3://{output_bucket}/{table}/"
        
        # Parquet 형식으로 저장 (압축 및 파티션 최적화)
        dyf.toDF().write \
           .mode("overwrite") \
           .option("compression", "snappy") \
           .parquet(output_path)
        
        print(f"✅ {table} 저장 완료 → {output_path}")
        
    except Exception as e:
        print(f"❌ 테이블 '{table}' 처리 중 오류 발생: {e}")
        # 선택적으로 실패 처리 로직 추가

print("🎉 모든 테이블 처리 완료!")

job.commit()