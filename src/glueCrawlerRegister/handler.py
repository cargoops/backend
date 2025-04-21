import boto3
from botocore.exceptions import ClientError

REGION = "us-west-2"
CRAWLER_NAME = "dynamodb_crawler_all"
ROLE_ARN = "arn:aws:iam::120569602527:role/GlueDynamoDBCrawlerRole"
DATABASE_NAME = "my_dynamodb_catalog"

def list_dynamodb_tables():
    dynamodb = boto3.client('dynamodb', region_name=REGION)
    try:
        response = dynamodb.list_tables()
        return response.get('TableNames', [])
    except Exception as e:
        print(f"❌ Failed to list DynamoDB tables: {e}")
        return []

def crawler_exists(glue, name):
    try:
        glue.get_crawler(Name=name)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityNotFoundException':
            return False
        raise e

def handler(event, context):
    glue = boto3.client('glue', region_name=REGION)

    # Step 1: Get all DynamoDB table names
    table_names = list_dynamodb_tables()
    dynamodb_targets = [{'Path': name} for name in table_names]

    print(f"📦 Found {len(table_names)} DynamoDB tables.")

    # Step 2: Ensure database exists
    try:
        glue.get_database(Name=DATABASE_NAME)
        print(f"📊 Glue database '{DATABASE_NAME}' already exists.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityNotFoundException':
            glue.create_database(DatabaseInput={'Name': DATABASE_NAME})
            print(f"✅ Created Glue database '{DATABASE_NAME}'.")

    # Step 3: Create or update crawler
    try:
        if crawler_exists(glue, CRAWLER_NAME):
            glue.update_crawler(
                Name=CRAWLER_NAME,
                Role=ROLE_ARN,
                DatabaseName=DATABASE_NAME,
                Targets={'DynamoDBTargets': dynamodb_targets},
                TablePrefix='dynamodb_',
                SchemaChangePolicy={
                    'UpdateBehavior': 'UPDATE_IN_DATABASE',
                    'DeleteBehavior': 'DEPRECATE_IN_DATABASE'
                }
            )
            print(f"🔄 Updated Glue crawler '{CRAWLER_NAME}'.")
        else:
            glue.create_crawler(
                Name=CRAWLER_NAME,
                Role=ROLE_ARN,
                DatabaseName=DATABASE_NAME,
                Targets={'DynamoDBTargets': dynamodb_targets},
                TablePrefix='dynamodb_',
                SchemaChangePolicy={
                    'UpdateBehavior': 'UPDATE_IN_DATABASE',
                    'DeleteBehavior': 'DEPRECATE_IN_DATABASE'
                },
                Description="Auto crawler for all DynamoDB tables"
            )
            print(f"✅ Created Glue crawler '{CRAWLER_NAME}'.")

        glue.start_crawler(Name=CRAWLER_NAME)
        print(f"▶️ Crawler '{CRAWLER_NAME}' started.")

    except Exception as e:
        print(f"❌ Failed to create/update/start crawler: {e}")
        raise e
