// Owner: Keshav
// High-fidelity mock data strictly conforming to docs/API_CONTRACT.md and backend schemas.

function createSvgEvidence(productName, status, statusColor) {
  const svg = `
  <svg xmlns="http://www.w3.org/2000/svg" width="600" height="420" viewBox="0 0 600 420" style="background:#1e293b; font-family: sans-serif;">
    <defs>
      <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
        <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#334155" stroke-width="0.5"/>
      </pattern>
    </defs>
    <rect width="600" height="420" fill="#0f172a"/>
    <rect width="600" height="420" fill="url(#grid)"/>

    <!-- Package Outline -->
    <rect x="50" y="30" width="500" height="360" rx="12" fill="#1e293b" stroke="#64748b" stroke-width="2"/>

    <!-- PDP Boundary (Detected) -->
    <rect x="80" y="60" width="440" height="300" rx="8" fill="#0f172a" fill-opacity="0.6" stroke="#38bdf8" stroke-width="2" stroke-dasharray="6,4"/>
    <text x="90" y="80" fill="#38bdf8" font-size="12" font-weight="bold">PDP BOUNDARY [YOLOv8: 94%]</text>

    <!-- Product Title -->
    <text x="100" y="120" fill="#f8fafc" font-size="18" font-weight="bold">${productName}</text>

    <!-- Extracted Field: MRP -->
    <rect x="100" y="150" width="180" height="38" rx="4" fill="#10b981" fill-opacity="0.15" stroke="#10b981" stroke-width="1.5"/>
    <text x="110" y="174" fill="#34d399" font-size="13" font-weight="600">MRP: Rs. 149.00 (incl. taxes)</text>

    <!-- Extracted Field: Net Qty -->
    <rect x="300" y="150" width="180" height="38" rx="4" fill="#10b981" fill-opacity="0.15" stroke="#10b981" stroke-width="1.5"/>
    <text x="310" y="174" fill="#34d399" font-size="13" font-weight="600">Net Wt: 400 g</text>

    <!-- Extracted Field: Mfg Date -->
    <rect x="100" y="205" width="180" height="38" rx="4" fill="#10b981" fill-opacity="0.15" stroke="#10b981" stroke-width="1.5"/>
    <text x="110" y="229" fill="#34d399" font-size="13" font-weight="600">MFD: 08/2026</text>

    <!-- Extracted Field: Manufacturer / Consumer Care -->
    ${
      status === "FAIL"
        ? `
      <!-- Missing Consumer Care (Violation BBox) -->
      <rect x="100" y="260" width="380" height="42" rx="4" fill="#ef4444" fill-opacity="0.15" stroke="#ef4444" stroke-width="2" stroke-dasharray="4,2"/>
      <text x="110" y="286" fill="#f87171" font-size="13" font-weight="bold">MISSING: Consumer Care Toll-free / Email</text>
    `
        : status === "REVIEW_REQUIRED"
        ? `
      <!-- Review Required Font Height -->
      <rect x="100" y="260" width="380" height="42" rx="4" fill="#f59e0b" fill-opacity="0.15" stroke="#f59e0b" stroke-width="2"/>
      <text x="110" y="286" fill="#fbbf24" font-size="13" font-weight="bold">REVIEW: Font Height ~1.8mm (Req: 2.0mm ±0.2mm)</text>
    `
        : `
      <!-- Compliant Manufacturer Details -->
      <rect x="100" y="260" width="380" height="42" rx="4" fill="#10b981" fill-opacity="0.15" stroke="#10b981" stroke-width="1.5"/>
      <text x="110" y="286" fill="#34d399" font-size="12">Mfd by: Apex Foods Pvt Ltd, Plot 14, Okhla Ind Area</text>
    `
    }

    <!-- ArUco Marker Stamp (Top Right) -->
    <rect x="440" y="70" width="60" height="60" fill="#ffffff" stroke="#000000" stroke-width="2"/>
    <rect x="450" y="80" width="20" height="20" fill="#000000"/>
    <rect x="480" y="80" width="10" height="20" fill="#000000"/>
    <rect x="460" y="110" width="30" height="10" fill="#000000"/>
    <text x="440" y="142" fill="#94a3b8" font-size="10">ArUco #42 [30mm]</text>

    <!-- Watermark / Status Stamp -->
    <g transform="translate(420, 310)">
      <rect width="140" height="34" rx="6" fill="${statusColor}" fill-opacity="0.2" stroke="${statusColor}" stroke-width="2"/>
      <text x="70" y="22" fill="${statusColor}" font-size="13" font-weight="bold" text-anchor="middle">${status}</text>
    </g>
  </svg>
  `;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

export const MOCK_SCAN_RESULT = {
  scan_id: "scan-9a8b7c6d-0001",
  product_name_hint: "NutriCrunch Almond Cookies 400g",
  timestamp: new Date().toISOString(),
  detection: {
    method: "yolo",
    confidence: 0.94,
    pdp_bbox: { x_min: 80, y_min: 60, x_max: 520, y_max: 360 },
  },
  extracted_fields: [
    {
      field_name: "mrp",
      raw_ocr_text: "M.R.P. Rs. 149.00 (INCL. OF ALL TAXES)",
      normalized_value: "149.00",
      confidence: 0.96,
      bbox: { x_min: 100, y_min: 150, x_max: 280, y_max: 188 },
    },
    {
      field_name: "net_quantity",
      raw_ocr_text: "NET WEIGHT: 400 g",
      normalized_value: "400 g",
      confidence: 0.92,
      bbox: { x_min: 300, y_min: 150, x_max: 480, y_max: 188 },
    },
    {
      field_name: "mfg_date",
      raw_ocr_text: "PKD: 08/2026",
      normalized_value: "08/2026",
      confidence: 0.91,
      bbox: { x_min: 100, y_min: 205, x_max: 280, y_max: 243 },
    },
    {
      field_name: "manufacturer_name",
      raw_ocr_text: "Manufactured by: Apex Foods Pvt Ltd, Plot 14, Okhla Ind Area, New Delhi - 110020",
      normalized_value: "Apex Foods Pvt Ltd, Plot 14, Okhla Ind Area, New Delhi - 110020",
      confidence: 0.89,
      bbox: { x_min: 100, y_min: 260, x_max: 480, y_max: 302 },
    },
    {
      field_name: "consumer_care",
      raw_ocr_text: "For feedback: care@apexfoods.in / Toll Free 1800-11-2233",
      normalized_value: "care@apexfoods.in / 1800-11-2233",
      confidence: 0.88,
      bbox: { x_min: 100, y_min: 310, x_max: 480, y_max: 340 },
    },
  ],
  font_analysis: {
    calibration_method: "aruco",
    mm_per_pixel: 0.114,
    fields: [
      {
        field_name: "net_quantity",
        measured_height_mm: 3.2,
        required_height_mm: 2.5,
        status: "PASS",
        calibration_confidence: 0.92,
      },
      {
        field_name: "mrp",
        measured_height_mm: 2.8,
        required_height_mm: 2.0,
        status: "PASS",
        calibration_confidence: 0.91,
      },
      {
        field_name: "mfg_date",
        measured_height_mm: 2.2,
        required_height_mm: 2.0,
        status: "PASS",
        calibration_confidence: 0.89,
      },
    ],
  },
  placement_checks: [
    { field_name: "mrp", within_pdp: true, confidence: 0.96 },
    { field_name: "net_quantity", within_pdp: true, confidence: 0.94 },
    { field_name: "mfg_date", within_pdp: true, confidence: 0.93 },
    { field_name: "manufacturer_name", within_pdp: true, confidence: 0.91 },
    { field_name: "consumer_care", within_pdp: true, confidence: 0.90 },
  ],
  compliance_results: [
    {
      rule_id: "RULE_6_1_E_MRP",
      field_name: "mrp",
      status: "PASS",
      confidence: 0.96,
      message: "Maximum Retail Price (MRP) clearly stated with all taxes included.",
      rule_version: "LMPC-2011-v1.1",
    },
    {
      rule_id: "RULE_6_1_B_NET_QTY",
      field_name: "net_quantity",
      status: "PASS",
      confidence: 0.94,
      message: "Net Quantity declaration specified with standard SI unit (g).",
      rule_version: "LMPC-2011-v1.1",
    },
    {
      rule_id: "RULE_6_1_A_MANUFACTURER",
      field_name: "manufacturer_name",
      status: "PASS",
      confidence: 0.91,
      message: "Complete manufacturer name and registered address detected.",
      rule_version: "LMPC-2011-v1.1",
    },
    {
      rule_id: "RULE_6_1_D_MFG_DATE",
      field_name: "mfg_date",
      status: "PASS",
      confidence: 0.92,
      message: "Month and year of manufacture/packing correctly declared.",
      rule_version: "LMPC-2011-v1.1",
    },
    {
      rule_id: "RULE_6_2_CONSUMER_CARE",
      field_name: "consumer_care",
      status: "PASS",
      confidence: 0.90,
      message: "Consumer helpline telephone and email address verified.",
      rule_version: "LMPC-2011-v1.1",
    },
    {
      rule_id: "RULE_7_TABLE_1_FONT_HEIGHT",
      field_name: "net_quantity_font",
      status: "PASS",
      confidence: 0.92,
      message: "Net Quantity numeral font height (3.2mm) exceeds minimum requirement (2.5mm per Table-I).",
      rule_version: "LMPC-2011-v1.1",
    },
    {
      rule_id: "RULE_6_PLACEMENT_GROUPING",
      field_name: "pdp_grouping",
      status: "PASS",
      confidence: 0.94,
      message: "All mandatory declarations reside within the Principal Display Panel.",
      rule_version: "LMPC-2011-v1.1",
    },
  ],
  overall_status: "PASS",
  rule_version: "LMPC-2011-v1.1",
  evidence_image_url: createSvgEvidence("NutriCrunch Almond Cookies 400g", "PASS", "#10b981"),
  original_image_url: createSvgEvidence("NutriCrunch Almond Cookies 400g", "ORIGINAL", "#64748b"),
};

export const MOCK_SCANS_DATABASE = {
  [MOCK_SCAN_RESULT.scan_id]: MOCK_SCAN_RESULT,

  "scan-kohaku-0000": {
    scan_id: "scan-kohaku-0000",
    product_name_hint: "Organic Kohaku Water 500mL",
    timestamp: new Date().toISOString(),
    detection: {
      method: "yolo",
      confidence: 0.96,
      pdp_bbox: { x_min: 75, y_min: 80, x_max: 525, y_max: 380 },
    },
    extracted_fields: [
      {
        field_name: "mrp",
        raw_ocr_text: "MRP Rs. 120.00 (INCL. TAXES)",
        normalized_value: "120.00",
        confidence: 0.98,
        bbox: { x_min: 100, y_min: 160, x_max: 270, y_max: 195 },
      },
      {
        field_name: "net_quantity",
        raw_ocr_text: "NET CONTENTS: 500 mL",
        normalized_value: "500 mL",
        confidence: 0.97,
        bbox: { x_min: 300, y_min: 160, x_max: 480, y_max: 195 },
      },
      {
        field_name: "mfg_date",
        raw_ocr_text: "MFD: 09/2026",
        normalized_value: "09/2026",
        confidence: 0.95,
        bbox: { x_min: 100, y_min: 215, x_max: 260, y_max: 245 },
      },
      {
        field_name: "manufacturer_name",
        raw_ocr_text: "Bottled by: Kohaku Springs Alpine Reserve, Manali HP - 175131",
        normalized_value: "Kohaku Springs Alpine Reserve, Manali HP - 175131",
        confidence: 0.94,
        bbox: { x_min: 100, y_min: 265, x_max: 480, y_max: 305 },
      },
      {
        field_name: "consumer_care",
        raw_ocr_text: "Helpline: 1800-890-7766 / care@kohakuwater.in",
        normalized_value: "1800-890-7766 / care@kohakuwater.in",
        confidence: 0.93,
        bbox: { x_min: 100, y_min: 315, x_max: 480, y_max: 345 },
      },
    ],
    font_analysis: {
      calibration_method: "aruco",
      mm_per_pixel: 0.112,
      fields: [
        {
          field_name: "net_quantity",
          measured_height_mm: 3.4,
          required_height_mm: 2.5,
          status: "PASS",
          calibration_confidence: 0.96,
        },
        {
          field_name: "mrp",
          measured_height_mm: 2.9,
          required_height_mm: 2.0,
          status: "PASS",
          calibration_confidence: 0.95,
        },
      ],
    },
    placement_checks: [
      { field_name: "mrp", within_pdp: true, confidence: 0.97 },
      { field_name: "net_quantity", within_pdp: true, confidence: 0.98 },
      { field_name: "mfg_date", within_pdp: true, confidence: 0.96 },
      { field_name: "manufacturer_name", within_pdp: true, confidence: 0.94 },
      { field_name: "consumer_care", within_pdp: true, confidence: 0.93 },
    ],
    compliance_results: [
      {
        rule_id: "RULE_6_1_E_MRP",
        field_name: "mrp",
        status: "PASS",
        confidence: 0.98,
        message: "Maximum Retail Price (₹120.00 incl. taxes) prominently declared on PDP.",
        rule_version: "LMPC-2011-v1.1",
      },
      {
        rule_id: "RULE_6_1_B_NET_QTY",
        field_name: "net_quantity",
        status: "PASS",
        confidence: 0.97,
        message: "Net quantity declaration in standard SI liquid units (500 mL).",
        rule_version: "LMPC-2011-v1.1",
      },
      {
        rule_id: "RULE_6_1_A_MANUFACTURER",
        field_name: "manufacturer_name",
        status: "PASS",
        confidence: 0.94,
        message: "Complete address and bottling facility clearly legible.",
        rule_version: "LMPC-2011-v1.1",
      },
      {
        rule_id: "RULE_6_2_CONSUMER_CARE",
        field_name: "consumer_care",
        status: "PASS",
        confidence: 0.93,
        message: "Toll-free customer care number and email verified.",
        rule_version: "LMPC-2011-v1.1",
      },
      {
        rule_id: "RULE_7_TABLE_1_FONT_HEIGHT",
        field_name: "net_quantity_font",
        status: "PASS",
        confidence: 0.96,
        message: "Measured font height (3.4mm) comfortably exceeds Rule 7 Table-I minimum (2.5mm).",
        rule_version: "LMPC-2011-v1.1",
      },
      {
        rule_id: "RULE_6_PLACEMENT_GROUPING",
        field_name: "pdp_grouping",
        status: "PASS",
        confidence: 0.97,
        message: "All 5 mandatory declarations grouped cleanly on the Principal Display Panel.",
        rule_version: "LMPC-2011-v1.1",
      },
    ],
    overall_status: "PASS",
    rule_version: "LMPC-2011-v1.1",
    evidence_image_url: "/kohaku_bottle.jpg",
    original_image_url: "/kohaku_bottle.jpg",
  },


  "scan-violation-0002": {
    scan_id: "scan-violation-0002",
    product_name_hint: "Heritage Shahi Garam Masala 100g",
    timestamp: new Date(Date.now() - 3600 * 1000 * 4).toISOString(),
    detection: {
      method: "yolo",
      confidence: 0.88,
      pdp_bbox: { x_min: 70, y_min: 50, x_max: 530, y_max: 370 },
    },
    extracted_fields: [
      {
        field_name: "mrp",
        raw_ocr_text: "MRP 85/-",
        normalized_value: "85.00",
        confidence: 0.87,
        bbox: { x_min: 90, y_min: 140, x_max: 220, y_max: 180 },
      },
      {
        field_name: "net_quantity",
        raw_ocr_text: "100 GM",
        normalized_value: "100 g",
        confidence: 0.91,
        bbox: { x_min: 280, y_min: 140, x_max: 420, y_max: 180 },
      },
      {
        field_name: "mfg_date",
        raw_ocr_text: "05/2026",
        normalized_value: "05/2026",
        confidence: 0.89,
        bbox: { x_min: 90, y_min: 200, x_max: 220, y_max: 240 },
      },
    ],
    font_analysis: {
      calibration_method: "aruco",
      mm_per_pixel: 0.12,
      fields: [
        {
          field_name: "net_quantity",
          measured_height_mm: 1.8,
          required_height_mm: 2.0,
          status: "FAIL",
          calibration_confidence: 0.89,
        },
      ],
    },
    placement_checks: [
      { field_name: "mrp", within_pdp: true, confidence: 0.91 },
      { field_name: "net_quantity", within_pdp: true, confidence: 0.93 },
    ],
    compliance_results: [
      {
        rule_id: "RULE_6_1_E_MRP",
        field_name: "mrp",
        status: "PASS",
        confidence: 0.87,
        message: "MRP detected.",
        rule_version: "LMPC-2011-v1.1",
      },
      {
        rule_id: "RULE_6_2_CONSUMER_CARE",
        field_name: "consumer_care",
        status: "FAIL",
        confidence: 0.96,
        message: "Consumer helpline contact details completely absent from label.",
        rule_version: "LMPC-2011-v1.1",
      },
      {
        rule_id: "RULE_6_1_A_MANUFACTURER",
        field_name: "manufacturer_name",
        status: "FAIL",
        confidence: 0.92,
        message: "Manufacturer name and address not found on Principal Display Panel.",
        rule_version: "LMPC-2011-v1.1",
      },
      {
        rule_id: "RULE_7_TABLE_1_FONT_HEIGHT",
        field_name: "net_quantity",
        status: "FAIL",
        confidence: 0.89,
        message: "Net quantity numeral font height (1.8mm) is below required minimum (2.0mm).",
        rule_version: "LMPC-2011-v1.1",
      },
    ],
    overall_status: "FAIL",
    rule_version: "LMPC-2011-v1.1",
    evidence_image_url: createSvgEvidence("Heritage Shahi Garam Masala 100g", "FAIL", "#ef4444"),
    original_image_url: createSvgEvidence("Heritage Shahi Garam Masala 100g", "ORIGINAL", "#64748b"),
  },

  "scan-review-0003": {
    scan_id: "scan-review-0003",
    product_name_hint: "DuraClean Antiseptic Hand Rub 250ml",
    timestamp: new Date(Date.now() - 3600 * 1000 * 26).toISOString(),
    detection: {
      method: "opencv_fallback",
      confidence: 0.74,
      pdp_bbox: { x_min: 60, y_min: 40, x_max: 540, y_max: 380 },
    },
    extracted_fields: [
      {
        field_name: "mrp",
        raw_ocr_text: "MRP Rs. 120.00",
        normalized_value: "120.00",
        confidence: 0.84,
        bbox: { x_min: 90, y_min: 130, x_max: 240, y_max: 170 },
      },
      {
        field_name: "net_quantity",
        raw_ocr_text: "250 ml",
        normalized_value: "250 ml",
        confidence: 0.88,
        bbox: { x_min: 270, y_min: 130, x_max: 390, y_max: 170 },
      },
    ],
    font_analysis: {
      calibration_method: "known_object",
      mm_per_pixel: 0.13,
      fields: [
        {
          field_name: "mrp",
          measured_height_mm: 1.9,
          required_height_mm: 2.0,
          status: "REVIEW_REQUIRED",
          calibration_confidence: 0.68,
        },
      ],
    },
    placement_checks: [
      { field_name: "mrp", within_pdp: true, confidence: 0.82 },
      { field_name: "net_quantity", within_pdp: true, confidence: 0.80 },
    ],
    compliance_results: [
      {
        rule_id: "RULE_CATEGORY_MEDICAL_DEVICE",
        field_name: "category_exception",
        status: "REVIEW_REQUIRED",
        confidence: 0.71,
        message: "Product mentions 'Drug Mfg Lic'. Potential exemption under Legal Metrology Amendment Rules 2025 (Medical Devices Rules 2017). Officer verification required.",
        rule_version: "LMPC-2011-v1.1",
      },
      {
        rule_id: "RULE_7_FONT_HEIGHT_CALIBRATION",
        field_name: "font_height",
        status: "REVIEW_REQUIRED",
        confidence: 0.68,
        message: "Calibration confidence (68%) below threshold (75%). Officer caliper measurement recommended.",
        rule_version: "LMPC-2011-v1.1",
      },
    ],
    overall_status: "REVIEW_REQUIRED",
    rule_version: "LMPC-2011-v1.1",
    evidence_image_url: createSvgEvidence("DuraClean Antiseptic Hand Rub 250ml", "REVIEW_REQUIRED", "#f59e0b"),
    original_image_url: createSvgEvidence("DuraClean Antiseptic Hand Rub 250ml", "ORIGINAL", "#64748b"),
  },
};

export const MOCK_HISTORY_ITEMS = [
  {
    scan_id: "scan-kohaku-0000",
    product_name_hint: "Organic Kohaku Water 500mL",
    timestamp: new Date().toISOString(),
    overall_status: "PASS",
    evidence_thumbnail_url: "/kohaku_bottle.jpg",
  },
  {
    scan_id: "scan-9a8b7c6d-0001",
    product_name_hint: "NutriCrunch Almond Cookies 400g",
    timestamp: new Date().toISOString(),
    overall_status: "PASS",
    evidence_thumbnail_url: createSvgEvidence("NutriCrunch Cookies", "PASS", "#10b981"),
  },
  {
    scan_id: "scan-violation-0002",
    product_name_hint: "Heritage Shahi Garam Masala 100g",
    timestamp: new Date(Date.now() - 3600 * 1000 * 4).toISOString(),
    overall_status: "FAIL",
    evidence_thumbnail_url: createSvgEvidence("Garam Masala", "FAIL", "#ef4444"),
  },
  {
    scan_id: "scan-review-0003",
    product_name_hint: "DuraClean Antiseptic Hand Rub 250ml",
    timestamp: new Date(Date.now() - 3600 * 1000 * 26).toISOString(),
    overall_status: "REVIEW_REQUIRED",
    evidence_thumbnail_url: createSvgEvidence("Hand Sanitizer", "REVIEW", "#f59e0b"),
  },
  {
    scan_id: "scan-pass-0004",
    product_name_hint: "Golden Roast Filter Coffee 200g",
    timestamp: new Date(Date.now() - 3600 * 1000 * 48).toISOString(),
    overall_status: "PASS",
    evidence_thumbnail_url: createSvgEvidence("Filter Coffee", "PASS", "#10b981"),
  },
  {
    scan_id: "scan-fail-0005",
    product_name_hint: "Sparkle Shine Dishwash Bar 300g",
    timestamp: new Date(Date.now() - 3600 * 1000 * 72).toISOString(),
    overall_status: "FAIL",
    evidence_thumbnail_url: createSvgEvidence("Dishwash Bar", "FAIL", "#ef4444"),
  },
  {
    scan_id: "scan-review-0006",
    product_name_hint: "FreshFarm Organic Basmati Rice 5kg",
    timestamp: new Date(Date.now() - 3600 * 1000 * 96).toISOString(),
    overall_status: "REVIEW_REQUIRED",
    evidence_thumbnail_url: createSvgEvidence("Basmati Rice", "REVIEW", "#f59e0b"),
  },
];

export const MOCK_DASHBOARD_STATS = {
  total_scans: 48,
  compliant_count: 31,
  non_compliant_count: 11,
  review_required_count: 6,
  violations_by_field: {
    "Consumer Care": 6,
    "Font Height (Table-I)": 5,
    "MRP Declaration": 3,
    "Manufacturer Address": 2,
    "Net Quantity": 2,
    "Mfg/Pkd Date": 1,
  },
  compliance_trend: [
    { date: "Aug 29", compliant: 4, non_compliant: 1, review_required: 1 },
    { date: "Aug 30", compliant: 5, non_compliant: 2, review_required: 0 },
    { date: "Aug 31", compliant: 3, non_compliant: 1, review_required: 2 },
    { date: "Sep 01", compliant: 6, non_compliant: 2, review_required: 0 },
    { date: "Sep 02", compliant: 4, non_compliant: 3, review_required: 1 },
    { date: "Sep 03", compliant: 5, non_compliant: 1, review_required: 1 },
    { date: "Sep 04", compliant: 4, non_compliant: 1, review_required: 1 },
  ],
  rule_version: "LMPC-2011-v1.1",
};

export const MOCK_USERS = {
  inspector1: {
    username: "inspector1",
    role: "inspector",
    token: "demo-token-inspector1",
  },
  admin1: {
    username: "admin1",
    role: "admin",
    token: "demo-token-admin1",
  },
};
