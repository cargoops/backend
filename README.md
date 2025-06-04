# Backend API Documentation

## Overview

This backend provides APIs for managing storing orders, package inspections, bin allocation, and user authentication/authorization.  
It uses AWS Lambda, DynamoDB, and a custom API key-based authorization system.

---

## Base URL

```
https://t4hw5tf1ye.execute-api.us-east-2.amazonaws.com/Prod
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

- **Path:** `/get_api_key_record`
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

### 3. Receive

- **Path:** `/receive`
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

- **Path:** `/discrepancy`
- **Method:** `POST`
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

## Error Handling

All endpoints return errors in the following format:
```json
{
  "message": "Error description"
}
```

---

## Contact

For questions or support, contact your backend team.
