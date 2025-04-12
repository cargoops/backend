from src.common import db, config, utils
import urllib.parse

def lambda_handler(event, context):
    try:
        # queryStringParameters에서 packageId를 가져온다고 가정
        params = event.get("queryStringParameters") or {}
        package_id = params.get("packageId")

        if not package_id:
            return utils.make_response(400, {"message": "Missing packageId"})

        # DynamoDB에서 get
        item = db.get_item(
            table_name=config.PACKAGES_TABLE,
            key={"packageId": package_id}
        )

        if not item:
            return utils.make_response(404, {"message": "Package not found"})

        return utils.make_response(200, {"data": item})

    except Exception as e:
        print(f"Error: {e}")
        return utils.make_response(500, {"message": "Internal Server Error"})
