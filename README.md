# Backend API Documentation

---

## CI/CD 배포 예시 (SAM)

```bash
# 빌드
sam build
# 배포 (스택명: cargoops-backend)
sam deploy --stack-name cargoops-backend --resolve-s3 --capabilities CAPABILITY_IAM --region us-east-2
```

---

## Overview

이 백엔드는 storing orders, package inspections, bin allocation 등을 관리하는 API를 제공합니다. 
AWS Lambda, DynamoDB를 사용하며, **이제 별도의 인증 없이 모든 요청에서 employee_id와 role을 직접 전달해야 합니다.**

---

## Base URL

```
https://ozw3p7h26e.execute-api.us-east-2.amazonaws.com/Prod
```

---

## 인증 및 권한 안내 (2024-06 기준)

- **더 이상 API Key, Authorizer, Authorization 헤더를 사용하지 않습니다.**
- 모든 요청에서 `employee_id`와 `role`을 직접 전달해야 하며, 서버는 이 값만으로 권한을 판단합니다.
- **POST/PUT 등 body가 있는 요청:**
  - body(JSON)에 반드시 `employee_id`와 `role`을 포함해야 합니다.
- **GET 등 body가 없는 요청:**
  - query string에 반드시 `employee_id`와 `role`을 포함해야 합니다.
  - 예시: `/inventory?employee_id=admin001&role=admin`
- 권한이 필요한 엔드포인트는 role 값으로만 판단합니다.

---

## API Endpoints

### 1. Get API Key Record (테스트용, 인증 없음)

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
- **Parameters (query string):**
  - `employee_id`, `role` (필수)
- **예시:**
```
GET /storing-orders?employee_id=admin001&role=admin
```

---

### 3. Receive Order

- **Path:** `/storing-orders/receive`
- **Method:** `POST`
- **Body:**
```json
{
  "storing_order_id": "string",
  "invoice_number": "string",
  "bill_of_entry_id": "string",
  "airway_bill_number": "string",
  "quantity": number,
  "employee_id": "string",
  "role": "receiver"
}
```

---

### 4. Update Discrepancy

- **Path:** `/storing-orders/discrepancy`
- **Method:** `PUT`
- **Body:**
```json
{
  "storing_order_id": "string",
  "discrepancy_detail": "string",
  "employee_id": "string",
  "role": "receiver"
}
```

---

### 5. TQ Quality Check

- **Path:** `/tq-quality-check`
- **Method:** `POST`
- **Body:**
```json
{
  "package_id": "string",
  "employee_id": "string",
  "role": "tq_employee",
  "flag": "pass | fail"
}
```

---

### 6. Bin Allocation

- **Path:** `/bin-allocation`
- **Method:** `POST`
- **Body:**
```json
{
  "package_id": "string",
  "employee_id": "string",
  "role": "binner"
}
```

---

### 7. Get Package

- **Path:** `/package/{package_id}`
- **Method:** `GET`
- **Parameters (query string):**
  - `employee_id`, `role` (필수)
- **예시:**
```
GET /package/PACK38627?employee_id=admin001&role=admin
```

---

### 8. Read Inventory

- **Path:** `/inventory`
- **Method:** `GET`
- **Parameters (query string):**
  - `employee_id`, `role` (필수, role=admin만 허용)
- **예시:**
```
GET /inventory?employee_id=admin001&role=admin
```

---

### 9. Read Pick Slips

- **Path:** `/pick-slips`
- **Method:** `GET`
- **Parameters (query string):**
  - `employee_id`, `role` (필수, role=admin만 허용)
- **예시:**
```
GET /pick-slips?employee_id=admin001&role=admin
```

---

### 10. Read Pick Orders

- **Path:** `/pick-orders`
- **Method:** `GET`
- **Parameters (query string):**
  - `employee_id`, `role` (필수, role=admin만 허용)
- **예시:**
```
GET /pick-orders?employee_id=admin001&role=admin
```

---

### 11. Get Next Pick Order

- **Path:** `/next-pick-order`
- **Method:** `GET`
- **Parameters (query string):**
  - `employee_id`, `role` (필수, role=picker만 허용)
- **예시:**
```
GET /next-pick-order?employee_id=picker001&role=picker
```

---

### 12. Close Pick Order

- **Path:** `/pick-orders/{pick_order_id}/close`
- **Method:** `POST`
- **Body:**
```json
{
  "employee_id": "string",
  "role": "picker"
}
```

---

### 13. Start Packing

- **Path:** `/packing/start`
- **Method:** `POST`
- **Body:**
```json
{
  "packing_zone": "string",
  "employee_id": "string",
  "role": "packer"
}
```

---

### 14. Close Packing

- **Path:** `/packing/{pick_slip_id}/close`
- **Method:** `POST`
- **Body:**
```json
{
  "employee_id": "string",
  "role": "packer"
}
```

---

### 15. Dispatch Pick Slip

- **Path:** `/pick-slips/{pick_slip_id}/dispatch`
- **Method:** `POST`
- **Body:**
```json
{
  "employee_id": "string",
  "role": "dispatcher"
}
```

---

### 16. Close Binning

- **Path:** `/packages/{package_id}/close-binning`
- **Method:** `POST`
- **Body:**
```json
{
  "employee_id": "string",
  "role": "binner"
}
```

---

## Error Handling

모든 엔드포인트는 다음과 같은 형식으로 에러를 반환합니다:
```