// Owner: Keshav
// Thin wrapper around the backend contract in docs/API_CONTRACT.md
// Every function here maps 1:1 to an endpoint - don't put UI logic here.

import axios from "axios";

const API_BASE = "http://localhost:8000/api/v1";

const client = axios.create({ baseURL: API_BASE });

// Attach auth token to every request if we have one
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function scanLabel(imageFile, calibrationMethod = "aruco", knownObjectSizeMm = null) {
  const form = new FormData();
  form.append("image", imageFile);
  form.append("calibration_method", calibrationMethod);
  if (knownObjectSizeMm != null) {
    form.append("known_object_size_mm", knownObjectSizeMm);
  }
  const res = await client.post("/scan", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data; // ScanResult
}

export async function getHistory(params = {}) {
  // params: { page, page_size, status, product_name, date_from, date_to }
  const res = await client.get("/history", { params });
  return res.data; // HistoryResponse
}

export async function getScanDetail(scanId) {
  const res = await client.get(`/history/${scanId}`);
  return res.data; // full ScanResult
}

export async function searchScans(query, params = {}) {
  const res = await client.get("/search", { params: { q: query, ...params } });
  return res.data; // HistoryResponse
}

export function getReportUrl(scanId, format) {
  // format: 'pdf' | 'docx' | 'json'
  // Used directly as an <a href> or window.open target, not fetched via axios
  return `${API_BASE}/reports/${scanId}/${format}`;
}

export async function getDashboardStats() {
  const res = await client.get("/dashboard/stats");
  return res.data; // DashboardStats
}

export async function login(username, password) {
  const res = await client.post("/auth/login", { username, password });
  localStorage.setItem("access_token", res.data.access_token);
  localStorage.setItem("role", res.data.role);
  return res.data; // LoginResponse
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("role");
}

export function getCurrentRole() {
  return localStorage.getItem("role"); // 'inspector' | 'admin' | null
}
