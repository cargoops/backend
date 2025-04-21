import boto3
import os

REGION = os.environ.get("MY_REGION", "us-west-2")
GLUE_JOB_NAME = os.environ.get("GLUE_JOB_NAME", "dynamodb_to_s3_etl")

def handler(event, context):
    glue = boto3.client('glue', region_name=REGION)
    
    try:
        print(f"▶️ Starting Glue ETL job: {GLUE_JOB_NAME}")
        response = glue.start_job_run(JobName=GLUE_JOB_NAME)
        job_run_id = response['JobRunId']
        print(f"✅ Glue ETL Job started. Run ID: {job_run_id}")
        return {
            "statusCode": 200,
            "body": f"Glue ETL job started successfully. Run ID: {job_run_id}"
        }
    except Exception as e:
        print(f"❌ Failed to start Glue ETL job: {e}")
        return {
            "statusCode": 500,
            "body": f"Error: {str(e)}"
        }
