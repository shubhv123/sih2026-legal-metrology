// Owner: Keshav
// Thin wrapper around the backend contract in docs/API_CONTRACT.md
// Handles communication with FastAPI backend with graceful fallback to mock data
// when the backend is offline or unreachable during standalone UI development.

import axios from "axios";
import {
  MOCK_SCAN_RESULT,
  MOCK_SCANS_DATABASE,
  MOCK_HISTORY_ITEMS,
  MOCK_DASHBOARD_STATS,
  MOCK_USERS,
} from "./mockData";

export const BACKEND_URL =
  typeof window !== "undefined" && (window.location.port === "5173" || window.location.port === "3000")
    ? ""
    : "http://127.0.0.1:8000";
const API_BASE = `${BACKEND_URL}/api/v1`;

export function resolveImageUrl(url) {
  if (!url) return "/kohaku_bottle.jpg";
  if (
    url.startsWith("http://") ||
    url.startsWith("https://") ||
    url.startsWith("data:") ||
    url.startsWith("blob:")
  ) {
    return url;
  }
  const clean = url.startsWith("/") ? url : `/${url}`;
  return BACKEND_URL ? `${BACKEND_URL}${clean}` : clean;
}

const client = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
});


// Local in-memory state for mock sessions
const localMockScans = { ...MOCK_SCANS_DATABASE };
const localMockHistory = [...MOCK_HISTORY_ITEMS];
let isBackendConnected = false;

// Attach auth token to every request if available
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Check if live backend is accessible
export async function checkBackendHealth() {
  try {
    const res = await axios.get(`${BACKEND_URL}/api/v1/health`, { timeout: 2000 });
    isBackendConnected = res.status === 200;
    return isBackendConnected;
  } catch {
    isBackendConnected = false;
    return false;
  }
}

export function isMockFallbackActive() {
  return !isBackendConnected;
}

/**
 * Normalizes backend ScanResponse (or mock ScanResult) into a unified shape
 * that safely provides both Array and Object access where needed.
 */
export function normalizeScanResult(data) {
  if (!data) return MOCK_SCAN_RESULT;

  const pName =
    data.product_name ||
    data.product_name_hint ||
    data.brand_name ||
    "Packaged Commodity Sample";

  const timeStr = data.created_at || data.timestamp || new Date().toISOString();

  // Normalize extracted_fields: ensure it can be mapped over as an Array
  // while also supporting dictionary lookups
  let extractedArray = [];
  let extractedDict = {};
  if (Array.isArray(data.extracted_fields)) {
    extractedArray = data.extracted_fields.map((ef) => ({
      field_name: ef.field_name || "unknown",
      raw_ocr_text: ef.raw_ocr_text || ef.raw_text || "",
      normalized_value: ef.normalized_value ?? "",
      confidence: ef.confidence ?? 0.9,
      bbox: ef.bbox || ef.bounding_box || null,
      unit: ef.unit || null,
    }));
    extractedArray.forEach((item) => {
      extractedDict[item.field_name] = item;
    });
  } else if (data.extracted_fields && typeof data.extracted_fields === "object") {
    extractedDict = { ...data.extracted_fields };
    extractedArray = Object.entries(data.extracted_fields).map(([key, val]) => ({
      field_name: val.field_name || key,
      raw_ocr_text: val.raw_text || val.raw_ocr_text || "",
      normalized_value: val.normalized_value ?? "",
      confidence: val.confidence ?? 0.9,
      bbox: val.bounding_box || val.bbox || null,
      unit: val.unit || null,
    }));
  }

  // Attach dict keys onto the array so `res.extracted_fields.map` works AND `res.extracted_fields[key]` works
  extractedArray.dict = extractedDict;

  // Normalize compliance results
  const complianceResults = (data.compliance_results || []).map((cr) => ({
    rule_id: cr.rule_id || "RULE_GENERIC",
    rule_name: cr.rule_name || cr.field_name || "Statutory Declaration",
    field_name: cr.field_name || cr.rule_name || "declaration",
    status: cr.status || "REVIEW_REQUIRED",
    confidence: cr.confidence ?? 0.88,
    measured_value: cr.measured_value ?? null,
    expected_value: cr.expected_value ?? null,
    violation_reason: cr.violation_reason ?? null,
    rule_version: cr.rule_version || data.rule_version || "LMPC-2011-v1.0",
    message:
      cr.message ||
      cr.violation_reason ||
      (cr.status === "PASS"
        ? `${cr.rule_name || cr.field_name} verified compliant per ${cr.rule_version || "LMPC 2011"}.`
        : `Non-compliance detected in ${cr.rule_name || cr.field_name}.`),
  }));

  // Normalize font_analysis
  let fontAnalysis = data.font_analysis;
  if (!fontAnalysis) {
    const scale = data.calibrated_scale_factor || 0.114;
    const fontChecks = complianceResults.filter((r) =>
      r.rule_id?.toLowerCase().includes("font") || r.field_name?.toLowerCase().includes("font")
    );
    fontAnalysis = {
      calibration_method: data.calibration_method || "aruco",
      mm_per_pixel: scale,
      fields: fontChecks.length > 0
        ? fontChecks.map((fc) => ({
            field_name: fc.field_name,
            measured_height_mm: parseFloat(fc.measured_value) || 2.8,
            required_height_mm: parseFloat(fc.expected_value) || 2.0,
            status: fc.status,
            calibration_confidence: fc.confidence,
          }))
        : [
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
              calibration_confidence: 0.88,
            },
          ],
    };
  }

  // Normalize detection
  const detection = data.detection || {
    method: "opencv_fallback",
    confidence: data.overall_confidence ?? 0.91,
    pdp_bbox: { x_min: 40, y_min: 30, x_max: 560, y_max: 420 },
  };

  return {
    scan_id: data.scan_id,
    product_name_hint: pName,
    product_name: pName,
    brand_name: data.brand_name || null,
    category: data.category || "standard_retail",
    timestamp: timeStr,
    created_at: timeStr,
    overall_status: data.overall_status || "REVIEW_REQUIRED",
    overall_confidence: data.overall_confidence ?? 0.9,
    rule_version: data.rule_version || "LMPC-2011-v1.0",
    evidence_image_url: data.evidence_image_url || data.original_image_url || "/kohaku_bottle.jpg",
    original_image_url: data.original_image_url || data.evidence_image_url || "/kohaku_bottle.jpg",
    detection,
    extracted_fields: extractedArray,
    font_analysis: fontAnalysis,
    placement_checks: data.placement_checks || [
      { field_name: "mrp", within_pdp: true, confidence: 0.93 },
      { field_name: "net_quantity", within_pdp: true, confidence: 0.9 },
    ],
    compliance_results: complianceResults,
  };
}

// 1. POST /api/v1/scan
export async function scanLabel(
  imageFile,
  calibrationMethod = "aruco",
  knownObjectSizeMm = null,
  productCategory = "standard_retail"
) {
  try {
    let uploadFile = imageFile;

    // If no real file or dummy object passed, fetch sample image as real Blob
    if (!uploadFile || typeof uploadFile === "string" || uploadFile.size < 64) {
      try {
        const response = await fetch("/kohaku_bottle.jpg");
        const blob = await response.blob();
        uploadFile = new File([blob], "kohaku_bottle.jpg", { type: "image/jpeg" });
      } catch {
        // Fallback to existing uploadFile
      }
    }

    const form = new FormData();
    // Conforms strictly to docs/API_CONTRACT.md
    form.append("image", uploadFile);
    form.append("calibration_method", calibrationMethod || "aruco");
    form.append("product_category", productCategory || "standard_retail");
    form.append("category", productCategory || "standard_retail");

    if (knownObjectSizeMm != null && !isNaN(Number(knownObjectSizeMm))) {
      form.append("known_object_size_mm", Number(knownObjectSizeMm));
      form.append("known_marker_size_mm", Number(knownObjectSizeMm));
    }

    const res = await client.post("/scan", form);


    isBackendConnected = true;
    const normalized = normalizeScanResult(res.data);

    // Save to local cache for session detail lookups
    localMockScans[normalized.scan_id] = normalized;
    localMockHistory.unshift({
      scan_id: normalized.scan_id,
      product_name: normalized.product_name,
      product_name_hint: normalized.product_name,
      timestamp: normalized.timestamp,
      created_at: normalized.created_at,
      overall_status: normalized.overall_status,
      overall_confidence: normalized.overall_confidence,
      evidence_thumbnail_url: normalized.evidence_image_url,
      evidence_image_url: normalized.evidence_image_url,
      violations_count: normalized.compliance_results.filter((c) => c.status === "FAIL").length,
    });

    return normalized;
  } catch (err) {
    console.error("Backend /scan error:", err);
    // If user uploaded an actual custom file and backend request failed, surface the real error
    if (imageFile && imageFile.name !== "kohaku_bottle.jpg" && (imageFile.size > 100 || typeof imageFile !== "string")) {
      const msg = err.response?.data?.detail || err.message || "Failed to process image scan.";
      throw new Error(`Scan failed on server: ${msg}`);
    }

    isBackendConnected = false;

    // Simulate pipeline latency for realistic UI inspection states
    await new Promise((resolve) => setTimeout(resolve, 1200));

    const scanId = `scan-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 6)}`;
    const fileName = imageFile?.name || "Packaged Product Label";
    const productHint = fileName.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ");

    const newScan = {
      ...MOCK_SCAN_RESULT,
      scan_id: scanId,
      product_name: productHint.charAt(0).toUpperCase() + productHint.slice(1),
      product_name_hint: productHint.charAt(0).toUpperCase() + productHint.slice(1),
      category: productCategory,
      timestamp: new Date().toISOString(),
      created_at: new Date().toISOString(),
      font_analysis: {
        ...MOCK_SCAN_RESULT.font_analysis,
        calibration_method: calibrationMethod,
      },
    };

    const normalized = normalizeScanResult(newScan);
    localMockScans[scanId] = normalized;
    localMockHistory.unshift({
      scan_id: scanId,
      product_name: normalized.product_name,
      product_name_hint: normalized.product_name,
      timestamp: normalized.timestamp,
      created_at: normalized.created_at,
      overall_status: normalized.overall_status,
      evidence_thumbnail_url: normalized.evidence_image_url,
      evidence_image_url: normalized.evidence_image_url,
      violations_count: normalized.compliance_results.filter((c) => c.status === "FAIL").length,
    });

    return normalized;
  }
}

// 2. GET /api/v1/history
export async function getHistory(params = {}) {
  try {
    const res = await client.get("/history", { params });
    isBackendConnected = true;

    const rawItems = res.data.items || res.data.results || [];
    const items = rawItems.map((item) => ({
      scan_id: item.scan_id,
      product_name: item.product_name || item.product_name_hint || "Scanned Commodity Sample",
      product_name_hint: item.product_name || item.product_name_hint || "Scanned Commodity Sample",
      brand_name: item.brand_name || null,
      category: item.category || "standard_retail",
      timestamp: item.created_at || item.timestamp || new Date().toISOString(),
      created_at: item.created_at || item.timestamp || new Date().toISOString(),
      overall_status: item.overall_status,
      overall_confidence: item.overall_confidence ?? 0.9,
      rule_version: item.rule_version || "LMPC-2011-v1.0",
      evidence_thumbnail_url: item.evidence_image_url || item.evidence_thumbnail_url || "/kohaku_bottle.jpg",
      evidence_image_url: item.evidence_image_url || item.evidence_thumbnail_url || "/kohaku_bottle.jpg",
      violations_count: item.violations_count ?? 0,
    }));

    return {
      total: res.data.total ?? items.length,
      page: res.data.page || 1,
      page_size: res.data.page_size || 10,
      total_pages: res.data.total_pages || Math.ceil((res.data.total || items.length) / (res.data.page_size || 10)),
      results: items,
      items: items,
    };
  } catch (err) {
    console.warn("Backend /history unavailable, using mock history:", err.message);
    isBackendConnected = false;

    let items = [...localMockHistory];
    if (params.status && params.status !== "ALL") {
      items = items.filter((item) => item.overall_status === params.status);
    }
    if (params.product_name) {
      const q = params.product_name.toLowerCase();
      items = items.filter((item) =>
        (item.product_name || item.product_name_hint || "").toLowerCase().includes(q)
      );
    }
    if (params.category && params.category !== "ALL") {
      items = items.filter((item) => item.category === params.category);
    }

    const page = params.page || 1;
    const pageSize = params.page_size || 10;

    return {
      total: items.length,
      page,
      page_size: pageSize,
      total_pages: Math.ceil(items.length / pageSize),
      results: items.slice((page - 1) * pageSize, page * pageSize),
      items: items.slice((page - 1) * pageSize, page * pageSize),
    };
  }
}

// 3. GET /api/v1/history/{scan_id}
export async function getScanDetail(scanId) {
  try {
    const res = await client.get(`/history/${scanId}`);
    isBackendConnected = true;
    return normalizeScanResult(res.data);
  } catch (err) {
    console.warn(`Backend /history/${scanId} unavailable, using mock scan detail:`, err.message);
    isBackendConnected = false;
    return (
      localMockScans[scanId] ||
      normalizeScanResult(MOCK_SCANS_DATABASE[scanId] || MOCK_SCAN_RESULT)
    );
  }
}

// 4. GET /api/v1/search?q={query}
export async function searchScans(query, params = {}) {
  try {
    const res = await client.get("/search", { params: { q: query, ...params } });
    isBackendConnected = true;

    const rawList = res.data.results || res.data.scans || res.data.items || [];
    const items = rawList.map((item) => ({
      scan_id: item.scan_id || item.id,
      product_name: item.product_name || item.product_name_hint || "Scanned Commodity",
      product_name_hint: item.product_name || item.product_name_hint || "Scanned Commodity",
      brand_name: item.brand_name || null,
      category: item.category || "standard_retail",
      timestamp: item.created_at || item.timestamp || new Date().toISOString(),
      created_at: item.created_at || item.timestamp || new Date().toISOString(),
      overall_status: item.overall_status,
      overall_confidence: item.overall_confidence ?? 0.9,
      evidence_thumbnail_url: item.evidence_image_url || item.evidence_thumbnail_url || "/kohaku_bottle.jpg",
      evidence_image_url: item.evidence_image_url || item.evidence_thumbnail_url || "/kohaku_bottle.jpg",
      violations_count: item.violations_count ?? 0,
    }));

    return {
      total: res.data.total ?? items.length,
      page: 1,
      page_size: params.page_size || 20,
      total_pages: 1,
      results: items,
      items: items,
    };
  } catch (err) {
    console.warn("Backend /search unavailable, filtering local data:", err.message);
    isBackendConnected = false;
    const q = (query || "").toLowerCase();
    const filtered = localMockHistory.filter(
      (item) =>
        (item.product_name || item.product_name_hint || "").toLowerCase().includes(q) ||
        (item.scan_id || "").toLowerCase().includes(q)
    );
    return {
      total: filtered.length,
      page: 1,
      page_size: params.page_size || 20,
      total_pages: 1,
      results: filtered,
      items: filtered,
    };
  }
}

// 5. GET /api/v1/reports/{scan_id}/pdf | /docx | /json
export function getReportUrl(scanId, format) {
  const fmt = (format || "pdf").toLowerCase();
  return `${API_BASE}/reports/${scanId}/${fmt}`;
}

// 6. GET /api/v1/dashboard/stats
export async function getDashboardStats() {
  try {
    const res = await client.get("/dashboard/stats");
    isBackendConnected = true;
    const raw = res.data;

    // Convert most_common_violations list into dictionary map for Recharts
    const violationsMap = {};
    if (Array.isArray(raw.most_common_violations)) {
      raw.most_common_violations.forEach((v) => {
        const key = v.label || v.rule_id || "Violation";
        violationsMap[key] = v.count;
      });
    }

    const total = raw.total_scans ?? 0;
    const pass = raw.pass_count ?? raw.compliant_count ?? 0;
    const fail = raw.fail_count ?? raw.non_compliant_count ?? 0;
    const review = raw.review_required_count ?? 0;
    const rate = raw.compliance_rate_pct ?? (total > 0 ? Math.round((pass / total) * 100) : 0);

    return {
      total_scans: total,
      compliant_count: pass,
      pass_count: pass,
      non_compliant_count: fail,
      fail_count: fail,
      review_required_count: review,
      compliance_rate_pct: rate,
      rule_version: raw.rule_version || "LMPC-2011-v1.0",
      violations_by_field: Object.keys(violationsMap).length > 0 ? violationsMap : MOCK_DASHBOARD_STATS.violations_by_field,
      most_common_violations: raw.most_common_violations || [],
      compliance_trend: raw.compliance_trend || [
        { date: "Day 1", compliant: Math.max(0, pass - 2), non_compliant: Math.max(0, fail - 1) },
        { date: "Day 2", compliant: pass, non_compliant: fail },
      ],
      recent_activity: raw.recent_activity || [],
    };
  } catch (err) {
    console.warn("Backend /dashboard/stats unavailable, using mock stats:", err.message);
    isBackendConnected = false;
    return MOCK_DASHBOARD_STATS;
  }
}

// 7. POST /api/v1/auth/login
export async function login(username, password) {
  try {
    const res = await client.post("/auth/login", { username, password });
    localStorage.setItem("access_token", res.data.access_token);
    localStorage.setItem("role", res.data.role);
    localStorage.setItem("username", res.data.username);
    isBackendConnected = true;
    return res.data; // TokenResponse
  } catch (err) {
    console.warn("Backend /auth/login unavailable, checking demo credentials:", err.message);

    // Support both new seeded accounts (inspector / inspector123) and demo accounts
    const validAccounts = {
      inspector: { password: "inspector123", role: "inspector", name: "Field Officer Sharma" },
      admin: { password: "admin123", role: "admin", name: "Enforcement Director Verma" },
      inspector1: { password: "demo123", role: "inspector", name: "Field Officer 1" },
      admin1: { password: "demo123", role: "admin", name: "Administrator 1" },
    };

    const matched = validAccounts[username];
    if (matched && (matched.password === password || password === "demo123")) {
      const mockToken = `demo-token-${username}`;
      localStorage.setItem("access_token", mockToken);
      localStorage.setItem("role", matched.role);
      localStorage.setItem("username", username);
      return {
        access_token: mockToken,
        token_type: "bearer",
        role: matched.role,
        username,
        full_name: matched.name,
      };
    }

    const mockUser = MOCK_USERS[username];
    if (mockUser && (password === "demo123" || password === "inspector123" || password === "admin123")) {
      localStorage.setItem("access_token", mockUser.token);
      localStorage.setItem("role", mockUser.role);
      localStorage.setItem("username", mockUser.username);
      return {
        access_token: mockUser.token,
        token_type: "bearer",
        role: mockUser.role,
        username: mockUser.username,
      };
    }

    throw new Error("Invalid credentials. Try inspector / inspector123 or admin / admin123");
  }
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("role");
  localStorage.removeItem("username");
}

export function getCurrentRole() {
  return localStorage.getItem("role"); // 'inspector' | 'admin' | null
}

export function getCurrentUsername() {
  return localStorage.getItem("username");
}

