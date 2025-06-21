# Backend API Documentation

## Overview

This backend provides APIs for managing storing orders, package inspections, bin allocation, and user authentication/authorization.  
It uses AWS Lambda, DynamoDB, and a custom API key-based authorization system.

---

## Base URL

```
https://ozw3p7h26e.execute-api.us-east-2.amazonaws.com/Prod
```

---

## Authentication

- **Type:** Custom API Key
- **How to authenticate:**  
  Obtain an API key and include it in the `Authorization` header for each request:
  ```
  Authorization: <api_key>
  ```
  The authorizer Lambda validates the key and injects `employee_id` and `role` into the request context.

---

## API Endpoints

### 1. Get API Key Record

- **Path:** `/api-key`
- **Method:** `POST` or `GET`
- **Parameters:**  
  - `api_key` (in query string or JSON body)
- **Response:**
  - `200 OK`: API key record (JSON)
  - `400 Bad Request`: Missing api_key
  - `404 Not Found`: Invalid api_key

---

### 2. Read Storing Orders

- **Path:** `/storing-orders`
- **Method:** `GET`
- **Authorization:** `Authorization` header with api_key required
- **Behavior:**
  - If `role` is `receiver`: Returns only orders assigned to the receiver.
  - If `role` is `admin`: Returns all orders.
  - Otherwise: `403 Forbidden`
- **Response:**
  - `200 OK`: `{ "data": [ ...orders ] }`
  - `403 Forbidden`: Unauthorized role

---

### 3. Receive Order

- **Path:** `/storing-orders/receive`
- **Method:** `POST`
- **Authorization:** `Authorization` header with api_key required (`role` must be `receiver`)
- **Body:**
  ```json
  {
    "storing_order_id": "string",
    "invoice_number": "string",
    "bill_of_entry_id": "string",
    "airway_bill_number": "string",
    "quantity": number,
    "employee_id": "string"
  }
  ```
- **Behavior:**
  - Checks for mismatches between input and order data.
  - If mismatches: Marks order and packages as `INSPECTION-FAILED`.
  - If no mismatches: Marks order as `RECEIVED` and packages as `READY-FOR-TQ`.
- **Response:**
  - `200 OK`: Order received
  - `400 Bad Request`: Inspection failed or invalid input
  - `403 Forbidden`: Unauthorized role
  - `404 Not Found`: Order not found

---

### 4. Update Discrepancy

- **Path:** `/storing-orders/discrepancy`
- **Method:** `PUT`
- **Authorization:** `Authorization` header with api_key required (`role` must be `receiver`)
- **Body:**                                                                                                                                                                                                                         
  ```json
  {
    "storing_order_id": "string",
    "discrepancy_detail": "string"
  }
  ```
- **Behavior:**
  - Can only update if order status is `INSPECTION-FAILED`.
  - Updates discrepancy detail and sets inspection result to `Failure`.
- **Response:**
  - `200 OK`: Discrepancy updated
  - `400 Bad Request`: Invalid input or wrong status
  - `403 Forbidden`: Unauthorized role
  - `404 Not Found`: Order not found

---

### 5. TQ Quality Check

- **Path:** `/tq-quality-check`
- **Method:** `POST`
- **Authorization:** `Authorization` header with api_key required (`role` must be `tq_employee`)
- **Body:**
  ```json
  {
    "package_id": "string",
    "employee_id": "string",
    "flag": "pass | fail"
  }
  ```
- **Behavior:**
  - 인증 및 권한(`role == tq_employee`) 확인
  - 입력값으로 flag(`pass` 또는 `fail`)를 받음
  - 해당 `package_id`의 패키지 status가 `READY-FOR-TQ`일 때만 동작
    - flag가 `pass`이면 status를 `READY-FOR-RFID-ATTACH`로 변경
    - flag가 `fail`이면 status를 `TQ-QUALITY-CHECK-FAILED`로 변경
    - 두 경우 모두 tq_staff_id, tq_quality_check_date를 함께 기록
  - status가 다르거나 인증 실패 시, 적절한 에러 메시지 반환
  - flag가 pass, fail이 아니면 에러 반환
- **Response:**
  - `200 OK`: 
    - flag가 pass: 패키지 상태가 READY-FOR-RFID-ATTACH로 변경됨
    - flag가 fail: 패키지 상태가 TQ-QUALITY-CHECK-FAILED로 변경됨
  - `400 Bad Request`: 패키지 상태가 READY-FOR-TQ가 아님, 입력값 오류, flag 오류
  - `403 Forbidden`: 인증/권한 오류
  - `404 Not Found`: package_id 없음

---

### 6. Bin Allocation

- **Path:** `/bin-allocation`
- **Method:** `POST`
- **Authorization:** `Authorization` header with api_key required (`role` must be `binner`)
- **Body:**
  ```json
  {
    "package_id": "string",
    "employee_id": "string"
  }
  ```
- **Behavior:**
  - 인증 및 권한(`role == binner`) 확인
  - 해당 `package_id`의 패키지 status가 `READY-FOR-BIN-ALLOCATION`일 때만 동작
  - quantity가 50 이상이면 공간 부족 에러 반환
  - 그렇지 않으면 1~5 중 랜덤 BIN 할당, bin_allocation, binner_id, bin_allocation_date, status(`READY-FOR-BINNING`) 업데이트
  - rfid_ids(세미콜론 구분 리스트) 내 각 RFID에 대해 Items 테이블의 status를 `READY-FOR-BINNING`으로 변경
- **Response:**
  - `200 OK`: Bin allocation 완료, bin_id, quantity 반환
  - `400 Bad Request`: 패키지 상태/quantity 오류, 공간 부족 등
  - `403 Forbidden`: 인증/권한 오류
  - `404 Not Found`: package_id 없음

---

### 7. Authorizer (Lambda)

- **Path:** Used as a Lambda authorizer for API Gateway
- **Behavior:**  
  Validates API key and injects `employee_id` and `role` into request context.

---

### 8. Get Package

- **Path:** `/package/{package_id}`
- **Method:** `GET`
- **Authorization:** `Authorization` header with api_key required
- **Parameters:**
  - `package_id` (URL path parameter)
- **Response:**
  - `200 OK`: 패키지 정보 (JSON)
  - `400 Bad Request`: package_id 누락
  - `404 Not Found`: 해당 package_id 없음

**예시 요청:**
```
GET /package/PACK38627
Authorization: <api_key>
```

**예시 응답:**
```json
{
  "package_id": "PACK001",
  "name": "샘플 패키지",
  "status": "배송중"
}
```

---

### 9. Read Pick Slips

- **Path:** `/pick-slips`
- **Method:** `GET`
- **Authorization:** `Authorization` header with api_key required (`role` must be `admin`)
- **Behavior:**
  - Returns all pick slips.
  - Only accessible to users with the `admin` role.
- **Response:**
  - `200 OK`: JSON array of all pick slips.
  - `403 Forbidden`: Unauthorized role.

**Example Request:**
```
GET /pick-slips
Authorization: <api_key>
```

**Example Response:**
```json
[
  {
    "pick_slip_id": "PSLIP001",
    "details": "[{'product_id': 'PROD1', 'quantity': 5}, {'product_id': 'PROD2', 'quantity': 2}]",
    "status": "NEW"
  }
]
```

---

### 10. Read Pick Orders

- **Path:** `/pick-orders`
- **Method:** `GET`
- **Authorization:** `Authorization` header with api_key required (`role` must be `admin`)
- **Behavior:**
  - Returns all pick orders.
  - Only accessible to users with the `admin` role.
- **Response:**
  - `200 OK`: JSON array of all pick orders.
  - `403 Forbidden`: Unauthorized role.

**Example Request:**
```
GET /pick-orders
Authorization: <api_key>
```

**Example Response:**
```json
[
  {
    "pick_order_id": "PORD001",
    "pick_slip_id": "PSLIP001",
    "product_id": "PROD1",
    "quantity": 5,
    "status": "PENDING"
  }
]
```

---

### 11. Get Next Pick Order

- **Path:** `/next-pick-order`
- **Method:** `GET`
- **Authorization:** `Authorization` header with api_key required (`role` must be `picker`)
- **Behavior:**
  - Authenticates and authorizes the user, checking if the `role` is `picker`.
  - Finds all pick orders assigned to the picker (`employee_id` from context) with `pick_order_status` as `READY-FOR-PICKING`.
  - Returns the one with the earliest `order_created_date`.
- **Response:**
  - `200 OK`: The next pick order object (JSON).
  - `403 Forbidden`: Unauthorized role.
  - `404 Not Found`: No pick orders are ready for picking.

**Example Request:**
```
GET /next-pick-order
Authorization: <api_key_with_picker_role>
```

**Example Response (Success):**
```json
{
    "pick_order_id": "PO0006",
    "pick_slip_id": "PS0005",
    "picking_zone": "RACK_A",
    "pick_task": "[{'bin_id': 'BIN1', 'product_id': 'PROD13', 'quantity': 2}, {'bin_id': 'BIN2', 'product_Id': 'PROD14', 'quantity': 3}]",
    "picker_id": "PICK9999",
    "order_created_date": "2025-06-20",
    "pick_order_status": "READY-FOR-PICKING",
    "picked_date": ""
}
```

**Example Response (Not Found):**
```json
{
    "message": "No pick orders are currently ready for picking."
}
```

---

### 12. Close Pick Order

- **Path:** `/pick-orders/{pick_order_id}/close`
- **Method:** `POST`
- **Authorization:** `Authorization` header with api_key required (`role` must be `picker`)
- **Behavior:**
  - Authenticates and authorizes the user, checking if the `role` is `picker` and if the picker is assigned to the specified `pick_order_id`.
  - Validates that the pick order's status is `READY-FOR-PICKING`.
  - Updates the pick order's status to `CLOSE` and records the `picked_date` as the current timestamp.
  - After closing, it checks all other pick orders associated with the same `pick_slip_id`.
  - If all related pick orders are `CLOSE`, it updates the corresponding `PickSlips` table record's status to `READY-FOR-PACKING` and records the `packing_start_date`.
- **Response:**
  - `200 OK`: Confirmation message. If the pick slip was updated, it will be noted in the response.
  - `400 Bad Request`: Invalid status or missing parameters.
  - `403 Forbidden`: Unauthorized role or not assigned to the order.
  - `404 Not Found`: Pick order not found.

**Example Request:**
```
POST /pick-orders/PO0006/close
Authorization: <api_key_for_PICK9999>
```

**Example Response (Success, Pick Slip Not Updated):**
```json
{
    "message": "Pick order closed successfully."
}
```

**Example Response (Success, Pick Slip Updated):**
```json
{
    "message": "Pick order closed successfully.",
    "pick_slip_status": "READY-FOR-PACKING"
}
```

---

### 13. Start Packing

- **Path:** `/packing/start`
- **Method:** `POST`
- **Authorization:** `Authorization` header with api_key required (`role` must be `packer`)
- **Body:**
  ```json
  {
    "packing_zone": "string"
  }
  ```
- **Behavior:**
  - Authenticates and authorizes the user, checking if the `role` is `packer`.
  - Scans for pick slips that are in the specified `packing_zone` and have a `pick_slip_status` of `READY-FOR-PACKING`.
  - If multiple slips are found, it selects the one with the earliest `pick_slip_created_date`.
  - It updates the selected pick slip's status to `PACKING-IN-PROGRESS`, sets the `packing_start_date` to the current time, and assigns the `packer_id`.
  - Returns the full, updated pick slip record.
- **Response:**
  - `200 OK`: The updated pick slip object (JSON).
  - `400 Bad Request`: Missing `packing_zone` in the request body.
  - `403 Forbidden`: Unauthorized role.
  - `404 Not Found`: No pick slips are ready for packing in the specified zone.

**Example Request:**
```
POST /packing/start
Authorization: <api_key_with_packer_role>
Content-Type: application/json

{
    "packing_zone": "ZONE-A"
}
```

**Example Response (Success):**
```json
{
    "pick_slip_id": "PS0005",
    "packing_zone": "ZONE-A",
    "pick_slip_status": "PACKING-IN-PROGRESS",
    "packer_id": "packer-007",
    "pick_slip_created_date": "2025-06-20",
    "packing_start_date": "2025-06-21T10:00:00.123456"
}
```

---

### 14. Close Packing

- **Path:** `/packing/{pick_slip_id}/close`
- **Method:** `POST`
- **Authorization:** `Authorization` header with api_key required (`role` must be `packer`)
- **Behavior:**
  - Authenticates and authorizes the user, checking if the `role` is `packer`.
  - Updates the specified `pick_slip_id`'s status to `READY-FOR-DISPATCH` and records the current timestamp in the `packed_date` field.
- **Response:**
  - `200 OK`: Confirmation message.
  - `403 Forbidden`: Unauthorized role.
  - `404 Not Found`: The specified `pick_slip_id` does not exist.

**Example Request:**
```
POST /packing/PS0005/close
Authorization: <api_key_with_packer_role>
```

**Example Response (Success):**
```json
{
    "message": "Pick slip PS0005 has been closed and is ready for dispatch."
}
```

---

## Error Handling

All endpoints return errors in the following format:
```