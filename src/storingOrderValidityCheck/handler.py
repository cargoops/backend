# {
#   "storingOrderId": "SO1234",
#   "airwayBillNumber": "AWB0001",
#   "billOfEntryId": "BOE0001"
# }

import json
from src.common import db, config, utils

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        storing_order_id = body.get("storingOrderId")
        input_awb = body.get("airwayBillNumber")
        input_boe = body.get("billOfEntryId")

        if not storing_order_id or not input_awb or not input_boe:
            return utils.make_response(400, {"message": "Missing required fields"})

        # 1. 테이블에서 Get
        item = db.get_item(
            table_name=config.STORING_ORDERS_TABLE,
            key={"storingOrderId": storing_order_id}
        )

        if not item:
            return utils.make_response(404, {"message": "StoringOrder not found"})
        
        # 2. 데이터 비교
        db_awb = item.get("airwayBillNumber")
        db_boe = item.get("billOfEntryId")

        if db_awb == input_awb and db_boe == input_boe:
            # 3. 상태 업데이트 (status -> 'TQ')
            db.update_item(
                table_name=config.STORING_ORDERS_TABLE,
                key={"storingOrderId": storing_order_id},
                update_expression="SET #st = :tqStatus",
                expression_values={":tqStatus": "TQ"},
                expression_names={"#st": "status"}
            )
            return utils.make_response(200, {"message": "StoringOrder status updated to TQ"})
        else:
            return utils.make_response(400, {"message": "airwayBillNumber or billOfEntryId mismatch"})

    except Exception as e:
        print(f"Error: {e}")
        return utils.make_response(500, {"message": "Internal Server Error"})
