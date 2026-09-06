# SIH26034 Legal Metrology Compliance Checker — API Contract v1.0

> **LOCKED CONTRACT**: This document is the single source of truth for the REST API interface between the FastAPI backend (`backend/`) and React frontend (`frontend/`).
> Changes to these endpoints or schemas require team notification.

---

## 1. Core Contract Principles

1. **Three-State Compliance Verdict**:
   - `PASS`: Compliant with rule, confidence $\ge 0.75$.
   - `FAIL`: Non-compliant violation detected, confidence $\ge 0.75$.
   - `REVIEW_REQUIRED`: Low confidence ($< 0.75$) or ambiguous image/detection requiring human inspector verification.
   - *Never collapse this into a boolean pass/fail.*

2. **Rule Version Stamping**:
   - Every scan response and compliance check object carries `rule_version` (e.g. `"LMPC-2011-v1.0"`).

3. **Fallback-First & No Raw 500s**:
   - `/api/v1/scan` degrades to low-confidence `REVIEW_REQUIRED` rather than crashing on bad/blurry input.

4. **Base URL**:
   - `http://localhost:8000/api/v1`

---

## 2. Authentication (`/api/v1/auth`)

### 2.1 Login
- **Endpoint**: `POST /api/v1/auth/login`
- **Request Body** (`application/json`):
```json
{
  "username": "inspector",
  "password": "inspector123"
}
```
- **Response** (`200 OK`):
```json
{
  "access_token": "demo-token-inspector-uuid",
  "token_type": "bearer",
  "role": "inspector",
  "username": "inspector",
  "full_name": "Field Inspector Sharma"
}
```
- **Error Responses**:
  - `401 Unauthorized`: `{"detail": "Invalid username or password"}`

### 2.2 Get Current User
- **Endpoint**: `GET /api/v1/auth/me`
- **Headers**: `Authorization: Bearer <access_token>`
- **Response** (`200 OK`):
```json
{
  "id": 1,
  "username": "inspector",
  "role": "inspector",
  "full_name": "Field Inspector Sharma"
}
```

---

## 3. Product Scanning (`/api/v1/scan`) — Owner: Shubh

### 3.1 Upload & Scan Image
- **Endpoint**: `POST /api/v1/scan`
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file`: Image file (required, PNG/JPEG/WEBP)
  - `known_object_size_mm`: Optional float (fallback calibration if ArUco tag is absent)
  - `product_category`: Optional string (`standard_retail`, `food_expiry`, `medical_device`, `bulk_exempt`)
- **Response** (`200 OK`):
```json
{
  "scan_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "product_id": 1,
  "product_name": "Sunfeast Dark Fantasy Choco Fills",
  "brand_name": "Sunfeast",
  "category": "food_expiry",
  "overall_status": "PASS",
  "overall_confidence": 0.94,
  "calibrated_scale_factor": 0.082,
  "calibration_method": "aruco",
  "rule_version": "LMPC-2011-v1.0",
  "original_image_url": "/static/scans/3fa85f64_orig.jpg",
  "evidence_image_url": "/static/scans/3fa85f64_annotated.jpg",
  "created_at": "2026-09-06T12:00:00Z",
  "extracted_fields": {
    "mrp": {
      "raw_text": "MRP Rs 40.00 (incl. of all taxes)",
      "normalized_value": 40.0,
      "unit": "INR",
      "confidence": 0.96,
      "bounding_box": [120, 45, 150, 280]
    },
    "net_quantity": {
      "raw_text": "Net Weight: 75 g",
      "normalized_value": 75.0,
      "unit": "g",
      "confidence": 0.95,
      "bounding_box": [160, 45, 185, 210]
    },
    "mfg_date": {
      "raw_text": "Mfg: 01/26",
      "normalized_value": "2026-01-01",
      "confidence": 0.92,
      "bounding_box": [190, 45, 210, 160]
    },
    "expiry_date": {
      "raw_text": "Best Before 6 Months from Mfg",
      "normalized_value": "6 Months",
      "confidence": 0.89,
      "bounding_box": [215, 45, 235, 270]
    },
    "manufacturer": {
      "raw_text": "Mfd by: ITC Limited, Virginia House, 37 J.L. Nehru Road, Kolkata 700071",
      "normalized_value": "ITC Limited, Virginia House, Kolkata 700071",
      "confidence": 0.91,
      "bounding_box": [240, 45, 280, 520]
    },
    "consumer_care": {
      "raw_text": "Consumer Care: 1800-425-4444 / itccares@itc.in",
      "normalized_value": "1800-425-4444 / itccares@itc.in",
      "confidence": 0.93,
      "bounding_box": [285, 45, 310, 480]
    }
  },
  "compliance_results": [
    {
      "rule_id": "RULE_6_MANDATORY_DECLARATIONS",
      "rule_name": "Mandatory Declarations Completeness",
      "field_name": "all_mandatory_fields",
      "status": "PASS",
      "confidence": 0.94,
      "measured_value": "6/6 mandatory fields identified",
      "expected_value": "All Rule 6 declarations present",
      "violation_reason": null,
      "rule_version": "LMPC-2011-v1.0"
    },
    {
      "rule_id": "RULE_6_PANEL_PLACEMENT",
      "rule_name": "Principal Display Panel Grouping",
      "field_name": "pdp_grouping",
      "status": "PASS",
      "confidence": 0.91,
      "measured_value": "100% fields enclosed within PDP boundary",
      "expected_value": "All mandatory declarations on Principal Display Panel",
      "violation_reason": null,
      "rule_version": "LMPC-2011-v1.0"
    },
    {
      "rule_id": "RULE_7_FONT_HEIGHT",
      "rule_name": "Minimum Character Height",
      "field_name": "net_quantity_numeral",
      "status": "PASS",
      "confidence": 0.88,
      "measured_value": "3.2 mm",
      "expected_value": "Min 2.0 mm for net weight 50g-100g (Table-I)",
      "violation_reason": null,
      "rule_version": "LMPC-2011-v1.0"
    }
  ]
}
```

---

## 4. Inspection History & Retrieval (`/api/v1/history`) — Owner: Aditya

### 4.1 List Scans (Paginated & Filterable)
- **Endpoint**: `GET /api/v1/history`
- **Query Parameters**:
  - `page`: int (default: 1)
  - `page_size`: int (default: 10, max: 100)
  - `status`: Optional string (`PASS`, `FAIL`, `REVIEW_REQUIRED`)
  - `product_name`: Optional string filter
  - `from_date`: Optional ISO date (`YYYY-MM-DD`)
  - `to_date`: Optional ISO date (`YYYY-MM-DD`)
- **Response** (`200 OK`):
```json
{
  "total": 45,
  "page": 1,
  "page_size": 10,
  "total_pages": 5,
  "items": [
    {
      "scan_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "product_name": "Sunfeast Dark Fantasy Choco Fills",
      "brand_name": "Sunfeast",
      "category": "food_expiry",
      "overall_status": "PASS",
      "overall_confidence": 0.94,
      "rule_version": "LMPC-2011-v1.0",
      "evidence_image_url": "/static/scans/3fa85f64_annotated.jpg",
      "violations_count": 0,
      "created_at": "2026-09-06T12:00:00Z"
    }
  ]
}
```

### 4.2 Get Scan Detail
- **Endpoint**: `GET /api/v1/history/{scan_id}`
- **Response** (`200 OK`):
  - Full `ScanResponse` JSON object (matching Section 3.1).
- **Error Responses**:
  - `404 Not Found`: `{"detail": "Scan record not found"}`

---

## 5. Universal Search (`/api/v1/search`) — Owner: Aditya

- **Endpoint**: `GET /api/v1/search`
- **Query Parameters**:
  - `q`: string (search term for product name, brand, scan UUID, or manufacturer)
  - `status`: Optional string (`PASS`, `FAIL`, `REVIEW_REQUIRED`)
  - `limit`: int (default: 20)
- **Response** (`200 OK`):
```json
{
  "query": "Sunfeast",
  "count": 2,
  "results": [
    {
      "scan_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "product_name": "Sunfeast Dark Fantasy Choco Fills",
      "brand_name": "Sunfeast",
      "overall_status": "PASS",
      "overall_confidence": 0.94,
      "rule_version": "LMPC-2011-v1.0",
      "created_at": "2026-09-06T12:00:00Z"
    }
  ]
}
```

---

## 6. Monitoring Dashboard (`/api/v1/dashboard`) — Owner: Aditya

- **Endpoint**: `GET /api/v1/dashboard/stats`
- **Response** (`200 OK`):
```json
{
  "total_scans": 128,
  "pass_count": 84,
  "fail_count": 28,
  "review_required_count": 16,
  "compliance_rate_pct": 65.6,
  "most_common_violations": [
    {
      "rule_id": "RULE_7_FONT_HEIGHT",
      "label": "Numeral font size below Table-I threshold",
      "count": 17
    },
    {
      "rule_id": "RULE_6_MANDATORY_DECLARATIONS",
      "label": "Missing Consumer Care contact",
      "count": 9
    },
    {
      "rule_id": "RULE_6_PANEL_PLACEMENT",
      "label": "MRP outside Principal Display Panel",
      "count": 6
    }
  ],
  "recent_activity": [
    {
      "scan_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "product_name": "Sunfeast Dark Fantasy Choco Fills",
      "overall_status": "PASS",
      "created_at": "2026-09-06T12:00:00Z"
    }
  ]
}
```

---

## 7. Compliance Reports Export (`/api/v1/reports`) — Owner: Aditya

- **PDF Export**: `GET /api/v1/reports/{scan_id}/pdf`
  - Returns `application/pdf` binary stream with embedded evidence photo, bounding boxes, rule version stamp, and inspector declaration.
- **DOCX Export**: `GET /api/v1/reports/{scan_id}/docx`
  - Returns `application/vnd.openxmlformats-officedocument.wordprocessingml.document` editable format.
- **JSON Export**: `GET /api/v1/reports/{scan_id}/json`
  - Returns standard `application/json` structured audit packet.
