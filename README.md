# Backend API Documentation

## Overview

This backend provides APIs for managing storing orders, package inspections, and user authentication/authorization.  
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

- **Path:** `/read_storing_orders`
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

- **Path:** `/receive_order`
- **Method:** `POST`
- **Authorization:** `Authorization` header with api_key required (`role` must be `receiver`)
- **Body:**
  ```json
  {
    "storing_order_id": "string",
    "invoice_number": "string",
    "bill_of_entry_id": "string",
    "airway_bill_number": "string",
    "quantity": number
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

- **Path:** `/update_discrepancy`
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

### 5. Authorizer (Lambda)

- **Path:** Used as a Lambda authorizer for API Gateway
- **Behavior:**  
  Validates API key and injects `employee_id` and `role` into request context.

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