from ..common import db, config, utils

def lambda_handler(event, context):
    try:
        items = db.scan_table(config.PICKSLIPS_TABLE)
        return utils.make_response(200, {"data": items})
    except Exception as e:
        print(f"Error: {e}")
        return utils.make_response(500, {"message": "Internal Server Error"})
