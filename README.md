# Backend API Documentation


## Overview

This backend provides APIs for managing storing orders, package inspections, bin allocation, and other warehouse operations.

---

## Base URL

```
https://ozw3p7h26e.execute-api.us-east-2.amazonaws.com/Prod
```

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

### 17. Close TQ

- **Path:** `/packages/{package_id}/close-tq`
- **Method:** `POST`
- **Body:**
```json
{
  "employee_id": "string",
  "role": "tq_employee"
}
```

---

### 18. Start TQ

- **Path:** `/packages/{package_id}/start-tq`
- **Method:** `POST`
- **Body:**
```json
{
  "employee_id": "string",
  "role": "any"
}
```
- **Response:**
  - `200 OK`: 패키지의 최신 정보(JSON)
  - `400 Bad Request`: 필수값 누락
  - `404 Not Found`: 패키지 없음

**예시 curl:**
```bash
curl -X POST "https://ozw3p7h26e.execute-api.us-east-2.amazonaws.com/Prod/packages/PACK12345/start-tq" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "tq001",
    "role": "tq_employee"
  }'
```