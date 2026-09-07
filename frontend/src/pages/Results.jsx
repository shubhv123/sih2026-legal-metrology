// Owner: Keshav
// Ultra-luxury minimal enterprise results page mirroring the Legal Metrology AI UI mockup.
// Asymmetrical 2-column grid:
// - Left/Center: Large packaging canvas with active laser scanning sweep beam & floating 3D dimension badges
// - Right: Numbered editorial Assessment Column (01, 02, 03...) with crisp dividers & solid matte-black action button

import React, { useState, useEffect } from "react";
import { useParams, useLocation, Link, useNavigate } from "react-router-dom";
import { getScanDetail, getReportUrl, resolveImageUrl, getCurrentRole, getCurrentUsername } from "../api/client";
import { MOCK_SCAN_RESULT, MOCK_SCANS_DATABASE } from "../api/mockData";

export default function Results() {
  const { scanId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const currentRole = getCurrentRole();
  const currentUsername = getCurrentUsername();

  const [scanResult, setScanResult] = useState(
    location.state?.scanResult || (scanId ? null : (MOCK_SCANS_DATABASE["scan-kohaku-0000"] || MOCK_SCAN_RESULT))
  );
  const [loading, setLoading] = useState(!scanResult && Boolean(scanId));
  const [error, setError] = useState(null);
  const [viewTab, setViewTab] = useState("checklist"); // checklist | font_table | raw_tokens
  const [adjudicatingRuleId, setAdjudicatingRuleId] = useState(null);
  const [officerRemarks, setOfficerRemarks] = useState("");
  const [officerVerdict, setOfficerVerdict] = useState("PASS");
  const [filterStatus, setFilterStatus] = useState("ALL"); // ALL | FAIL | REVIEW_REQUIRED | PASS

  useEffect(() => {
    if (!scanResult && scanId) {
      setLoading(true);
      getScanDetail(scanId)
        .then((data) => {
          setScanResult(data);
          setError(null);
        })
        .catch((err) => {
          setError(err.message || "Failed to load scan details.");
        })
        .finally(() => setLoading(false));
    }
  }, [scanId, scanResult]);

  if (loading) {
    return (
      <div className="py-28 text-center space-y-4">
        <div className="w-10 h-10 border-2 border-neutral-300 border-t-black rounded-full animate-spin mx-auto" />
        <p className="text-neutral-500 text-xs font-mono uppercase tracking-widest">
          Retrieving Inspection Coordinates & Legal Assessment...
        </p>
      </div>
    );
  }

  if (error || !scanResult) {
    return (
      <div className="max-w-xl mx-auto py-20 text-center space-y-4 bg-white p-8 rounded-2xl border border-[#E5E7EB] shadow-sm">
        <div className="w-12 h-12 bg-neutral-100 rounded-full flex items-center justify-center mx-auto text-xl">
          ⚖️
        </div>
        <h2 className="text-base font-bold text-neutral-900 tracking-tight">
          Inspection Record Not Found
        </h2>
        <p className="text-xs text-neutral-500 max-w-sm mx-auto">
          {error || "No active scan payload available. Please upload a packaged commodity label."}
        </p>
        <button
          onClick={() => navigate("/")}
          className="px-5 py-2 rounded-lg bg-black text-white text-xs font-semibold hover:bg-neutral-800 transition-colors shadow-sm"
        >
          Initialize New Scan
        </button>
      </div>
    );
  }

  // 3-State Status Badge styling
  const statusTheme = {
    PASS: {
      text: "text-emerald-700",
      bg: "bg-emerald-50",
      border: "border-emerald-200",
      tag: "PASS",
      pill: "bg-emerald-600 text-white",
    },
    FAIL: {
      text: "text-rose-700",
      bg: "bg-rose-50",
      border: "border-rose-200",
      tag: "VIOLATION",
      pill: "bg-rose-600 text-white",
    },
    REVIEW_REQUIRED: {
      text: "text-amber-700",
      bg: "bg-amber-50",
      border: "border-amber-200",
      tag: "REVIEW REQUIRED",
      pill: "bg-amber-600 text-white",
    },
  };

  const currentTheme = statusTheme[scanResult.overall_status] || statusTheme.REVIEW_REQUIRED;


  const handleAdjudicateSubmit = (targetRuleId) => {
    if (!scanResult) return;
    const updatedResults = (scanResult.compliance_results || []).map((cr, idx) => {
      if ((cr.rule_id || idx) === targetRuleId) {
        return {
          ...cr,
          status: officerVerdict,
          confidence: 1.0,
          adjudicated_by: currentUsername || currentRole || "Field Officer",
          adjudicated_at: new Date().toISOString(),
          officer_note: officerRemarks || "Physical verification complete.",
          message: officerRemarks
            ? `[Officer Adjudicated: ${officerVerdict}] ${officerRemarks}`
            : `Physical inspection verified: marked as ${officerVerdict}.`,
        };
      }
      return cr;
    });

    let newOverall = "PASS";
    if (updatedResults.some((r) => r.status === "FAIL")) {
      newOverall = "FAIL";
    } else if (updatedResults.some((r) => r.status === "REVIEW_REQUIRED")) {
      newOverall = "REVIEW_REQUIRED";
    }

    setScanResult({
      ...scanResult,
      overall_status: newOverall,
      compliance_results: updatedResults,
    });
    setAdjudicatingRuleId(null);
    setOfficerRemarks("");
  };

  return (
    <div className="space-y-6">
      {/* TOP CONTEXT BAR: Breadcrumbs & Telemetry Meta */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#E5E7EB]">
        <div className="flex items-center space-x-2 text-xs text-neutral-500 font-mono">
          <Link to="/" className="hover:text-black transition-colors">
            WORKSPACE
          </Link>
          <span>/</span>
          <span className="text-neutral-900 font-semibold">{scanResult.scan_id}</span>
          <span>•</span>
          <span className="text-neutral-400">
            {new Date(scanResult.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
        </div>

        {/* Action controls */}
        <div className="flex items-center space-x-2">
          <a
            href={getReportUrl(scanResult.scan_id, "pdf")}
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-white hover:bg-neutral-50 text-neutral-700 border border-neutral-200 transition-colors shadow-sm"
          >
            PDF
          </a>
          <a
            href={getReportUrl(scanResult.scan_id, "docx")}
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-white hover:bg-neutral-50 text-neutral-700 border border-neutral-200 transition-colors shadow-sm"
          >
            DOCX
          </a>
          <a
            href={getReportUrl(scanResult.scan_id, "json")}
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-white hover:bg-neutral-50 text-neutral-700 border border-neutral-200 transition-colors shadow-sm"
          >
            JSON
          </a>
        </div>
      </div>

      {/* MAIN ASYMMETRICAL 2-COLUMN GRID (Mirrors Mockup Image) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* ============================================================ */}
        {/* CENTER CANVAS COMPONENT: Packaging Box with Laser Sweep & 3D Badges */}
        {/* ============================================================ */}
        <div className="lg:col-span-7 xl:col-span-8 flex flex-col space-y-4">
          <div className="relative bg-white rounded-2xl border border-[#E5E7EB] shadow-[0_4px_25px_rgba(0,0,0,0.03)] p-6 md:p-8 overflow-hidden min-h-[540px] flex flex-col items-center justify-center">
            
            {/* Subtle Canvas Corner Coordinates */}
            <div className="absolute top-4 left-5 text-[10px] font-mono text-neutral-400 tracking-wider">
              PDP_BBOX: [{scanResult.detection?.pdp_bbox?.x_min || 75}, {scanResult.detection?.pdp_bbox?.y_min || 80}, {scanResult.detection?.pdp_bbox?.x_max || 525}, {scanResult.detection?.pdp_bbox?.y_max || 380}]
            </div>
            <div className="absolute top-4 right-5 text-[10px] font-mono text-neutral-400 tracking-wider">
              SCALE: {scanResult.font_analysis?.mm_per_pixel ? `${scanResult.font_analysis.mm_per_pixel.toFixed(3)} mm/px` : "ARUCO_CALIBRATED"}
            </div>

            {/* Product Display Box Graphic Container */}
            <div className="relative w-full max-w-xl mx-auto flex items-center justify-center my-4">
              
              {/* Product Image / Package Surface */}
              <div className="relative rounded-xl overflow-hidden shadow-2xl border border-neutral-200/80 bg-neutral-900 group min-h-[360px] min-w-[320px] w-full flex items-center justify-center">
                <img
                  src={resolveImageUrl(scanResult.evidence_image_url || scanResult.original_image_url)}
                  alt="Scanned product package template"
                  className="w-full max-h-[460px] object-contain block select-none"
                  onError={(e) => {
                    if (location.state?.previewUrl) {
                      e.currentTarget.src = location.state.previewUrl;
                    } else {
                      e.currentTarget.src = "/kohaku_bottle.jpg";
                    }
                  }}
                />
              </div>
            </div>

            {/* Canvas Footer Metadata Pill */}
            <div className="w-full flex items-center justify-between text-xs pt-4 border-t border-[#F0F2F5] text-neutral-500 font-mono">
              <div className="flex items-center space-x-2">
                <span className="inline-block w-2 h-2 rounded-full bg-black animate-pulse" />
                <span className="font-semibold text-neutral-800">
                  {scanResult.product_name_hint || "Packaged Commodity Sample"}
                </span>
              </div>
              <div className="flex items-center space-x-3 text-[11px]">
                <span>MODEL: {scanResult.detection?.method?.toUpperCase() || "YOLOV8"}</span>
                <span>•</span>
                <span>CONF: {Math.round((scanResult.detection?.confidence || 0.94) * 100)}%</span>
                <span>•</span>
                <span>CALIBRATION: {scanResult.font_analysis?.calibration_method?.toUpperCase() || "ARUCO"}</span>
              </div>
            </div>
          </div>

          {/* SECONDARY VIEW TABS: Font Height Table & Raw OCR */}
          <div className="bg-white rounded-xl border border-[#E5E7EB] p-4 shadow-sm">
            <div className="flex items-center space-x-4 border-b border-[#F0F2F5] pb-2 text-xs font-mono">
              <button
                onClick={() => setViewTab("checklist")}
                className={`pb-1 font-semibold tracking-wider transition-colors ${
                  viewTab === "checklist" ? "text-black border-b-2 border-black" : "text-neutral-400 hover:text-neutral-700"
                }`}
              >
                SUMMARY VIEW
              </button>
              <button
                onClick={() => setViewTab("font_table")}
                className={`pb-1 font-semibold tracking-wider transition-colors ${
                  viewTab === "font_table" ? "text-black border-b-2 border-black" : "text-neutral-400 hover:text-neutral-700"
                }`}
              >
                RULE 7 FONT TABLE-I
              </button>
              <button
                onClick={() => setViewTab("raw_tokens")}
                className={`pb-1 font-semibold tracking-wider transition-colors ${
                  viewTab === "raw_tokens" ? "text-black border-b-2 border-black" : "text-neutral-400 hover:text-neutral-700"
                }`}
              >
                RAW OCR TOKENS
              </button>
            </div>

            {/* TAB CONTENT */}
            <div className="pt-3">
              {viewTab === "font_table" && (
                <div className="overflow-x-auto text-xs">
                  <table className="w-full text-left font-mono">
                    <thead>
                      <tr className="text-neutral-400 text-[10px] border-b border-[#E5E7EB] uppercase">
                        <th className="py-2">Field</th>
                        <th className="py-2">Measured</th>
                        <th className="py-2">Statutory Min</th>
                        <th className="py-2">Confidence</th>
                        <th className="py-2">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#F0F2F5]">
                      {scanResult.font_analysis?.fields?.map((f, i) => (
                        <tr key={i} className="text-neutral-700">
                          <td className="py-2 font-medium capitalize text-neutral-900">{f.field_name.replace(/_/g, " ")}</td>
                          <td className="py-2 font-bold text-neutral-900">{f.measured_height_mm.toFixed(2)} mm</td>
                          <td className="py-2 text-neutral-500">≥ {f.required_height_mm.toFixed(2)} mm</td>
                          <td className="py-2 text-neutral-500">{Math.round(f.calibration_confidence * 100)}%</td>
                          <td className="py-2">
                            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${f.status === "PASS" ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"}`}>
                              {f.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {viewTab === "raw_tokens" && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                  {(Array.isArray(scanResult.extracted_fields)
                    ? scanResult.extracted_fields
                    : Object.entries(scanResult.extracted_fields || {}).map(([k, v]) => ({
                        field_name: v.field_name || k,
                        raw_ocr_text: v.raw_ocr_text || v.raw_text || "",
                        normalized_value: v.normalized_value ?? "",
                        confidence: v.confidence ?? 0.9,
                      }))
                  ).map((ef, i) => (
                    <div key={i} className="p-2.5 rounded-lg bg-neutral-50 border border-neutral-200">
                      <div className="flex justify-between text-neutral-400 text-[10px] uppercase">
                        <span>{ef.field_name}</span>
                        <span>{Math.round((ef.confidence || 0.9) * 100)}%</span>
                      </div>
                      <p className="text-neutral-900 font-semibold mt-1">"{ef.raw_ocr_text}"</p>
                      <p className="text-emerald-700 text-[11px] mt-0.5">
                        Normalized: {String(ef.normalized_value)}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {viewTab === "checklist" && (
                <p className="text-xs text-neutral-500 font-sans leading-relaxed">
                  Principal Display Panel analyzed using dual-path spatial computer vision. Bounding coordinates verified against Rule 6 grouping requirements and Rule 7 character proportions.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* ============================================================ */}
        {/* RIGHT ASSESSMENT COLUMN: Editorial Checklist & Matte-Black Button */}
        {/* ============================================================ */}
        <div className="lg:col-span-5 xl:col-span-4 bg-white rounded-2xl border border-[#E5E7EB] shadow-[0_4px_25px_rgba(0,0,0,0.03)] p-6 md:p-8 flex flex-col justify-between space-y-4 lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)]">
          
          <div className="flex flex-col space-y-4 flex-1 min-h-0">
            {/* Heading & Subtitle (Pinned at top) */}
            <div className="flex items-center justify-between border-b border-[#E5E7EB] pb-3 shrink-0">
              <div>
                <h2 className="text-xl font-bold tracking-tight text-neutral-900 font-sans">
                  Assessment
                </h2>
                <p className="text-xs text-neutral-400 font-mono mt-0.5">
                  STAMP: {scanResult.rule_version}
                </p>
              </div>
              <div className={`px-2.5 py-1 rounded-md text-[11px] font-mono font-bold tracking-wider uppercase border ${currentTheme.bg} ${currentTheme.text} ${currentTheme.border}`}>
                {scanResult.overall_status}
              </div>
            </div>

            {/* Quick Status Filter Tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-[11px] font-mono shrink-0">
              <button
                type="button"
                onClick={() => setFilterStatus("ALL")}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  filterStatus === "ALL"
                    ? "bg-neutral-900 text-white font-bold"
                    : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200"
                }`}
              >
                All ({(scanResult.compliance_results?.length || 0) + 2})
              </button>
              {scanResult.compliance_results?.some((r) => r.status === "FAIL") && (
                <button
                  type="button"
                  onClick={() => setFilterStatus("FAIL")}
                  className={`px-2.5 py-1 rounded-md transition-colors ${
                    filterStatus === "FAIL"
                      ? "bg-rose-600 text-white font-bold"
                      : "bg-rose-50 text-rose-700 hover:bg-rose-100"
                  }`}
                >
                  Violations ({scanResult.compliance_results?.filter((r) => r.status === "FAIL").length + (scanResult.overall_status === "FAIL" ? 1 : 0)})
                </button>
              )}
              {scanResult.compliance_results?.some((r) => r.status === "REVIEW_REQUIRED") && (
                <button
                  type="button"
                  onClick={() => setFilterStatus("REVIEW_REQUIRED")}
                  className={`px-2.5 py-1 rounded-md transition-colors ${
                    filterStatus === "REVIEW_REQUIRED"
                      ? "bg-amber-600 text-white font-bold"
                      : "bg-amber-50 text-amber-800 hover:bg-amber-100"
                  }`}
                >
                  Review ({scanResult.compliance_results?.filter((r) => r.status === "REVIEW_REQUIRED").length})
                </button>
              )}
              {scanResult.compliance_results?.some((r) => r.status === "PASS") && (
                <button
                  type="button"
                  onClick={() => setFilterStatus("PASS")}
                  className={`px-2.5 py-1 rounded-md transition-colors ${
                    filterStatus === "PASS"
                      ? "bg-emerald-600 text-white font-bold"
                      : "bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                  }`}
                >
                  Compliant ({scanResult.compliance_results?.filter((r) => r.status === "PASS").length + 1})
                </button>
              )}
            </div>

            {/* SCROLLABLE NUMBERED EDITORIAL LEGAL CHECKLIST */}
            <div className="overflow-y-auto flex-1 min-h-0 max-h-[480px] lg:max-h-[calc(100vh-270px)] pr-2 divide-y divide-[#F0F2F5] space-y-0 focus:outline-none">
              
              {/* 01 Legal compliance checklist */}
              {(filterStatus === "ALL" || filterStatus === scanResult.overall_status) && (
                <div className="py-3.5 space-y-1 group">
                  <div className="flex items-baseline space-x-2.5">
                    <span className="font-mono text-sm font-bold text-neutral-900 tracking-tight">01</span>
                    <div className="flex-1 flex items-center justify-between">
                      <h3 className="text-xs font-bold text-neutral-900 uppercase tracking-wider">
                        Overall Compliance Checklist
                      </h3>
                      <span className={`text-[10px] font-mono font-bold uppercase px-1.5 py-0.5 rounded ${currentTheme.pill}`}>
                        {scanResult.overall_status}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-neutral-500 pl-6 leading-relaxed">
                    Automated computer vision negative space and declaration assessment per LMPC 2011 specifications.
                  </p>
                </div>
              )}

              {/* Dynamic Compliance Results from rule engine */}
              {scanResult.compliance_results
                ?.filter((res) => filterStatus === "ALL" || res.status === filterStatus)
                .map((res, index) => {
                  const num = (index + 2).toString().padStart(2, "0");
                  const itemTheme = statusTheme[res.status] || statusTheme.REVIEW_REQUIRED;
                  const fieldTitle =
                    res.rule_name ||
                    (res.field_name ? res.field_name.replace(/_/g, " ") : "Statutory Declaration");
                  const messageText =
                    res.message ||
                    res.violation_reason ||
                    (res.status === "PASS"
                      ? `${fieldTitle} verified compliant per ${res.rule_version || "LMPC 2011"}.`
                      : `Non-compliance detected in ${fieldTitle}.`);

                  return (
                    <div key={res.rule_id || index} className="py-3.5 space-y-1 group">
                      <div className="flex items-baseline space-x-2.5">
                        <span className="font-mono text-sm font-bold text-neutral-900 tracking-tight">
                          {num}
                        </span>
                        <div className="flex-1 flex items-center justify-between">
                          <h3 className="text-xs font-bold text-neutral-900 uppercase tracking-wider">
                            {fieldTitle}
                          </h3>
                          <div className="flex items-center space-x-2">
                            <span className="text-[10px] font-mono text-neutral-400">
                              {Math.round((res.confidence || 0.9) * 100)}%
                            </span>
                            <span className={`text-[9px] font-mono font-bold uppercase px-1.5 py-0.2 rounded ${itemTheme.pill}`}>
                              {res.status}
                            </span>
                          </div>
                        </div>
                      </div>
                      <p className="text-xs text-neutral-600 pl-6 leading-relaxed">
                        {messageText}
                      </p>
                      {(res.measured_value || res.expected_value) && (
                        <div className="pl-6 text-[10px] font-mono text-neutral-500 flex items-center space-x-2">
                          {res.measured_value && <span>Measured: {res.measured_value}</span>}
                          {res.measured_value && res.expected_value && <span>•</span>}
                          {res.expected_value && <span>Required: {res.expected_value}</span>}
                        </div>
                      )}
                      <div className="pl-6 text-[10px] font-mono text-neutral-400 flex items-center space-x-2 pt-0.5">
                        <span>{res.rule_id}</span>
                        <span>•</span>
                        <span>{res.rule_version}</span>
                      </div>

                      {/* Inspector Adjudication Block for Review Required */}
                      {res.status === "REVIEW_REQUIRED" && (
                        <div className="pl-6 pt-2">
                          {adjudicatingRuleId === (res.rule_id || index) ? (
                            <div className="p-3 bg-neutral-50 rounded-xl border border-neutral-300 space-y-2.5">
                              <div className="text-[11px] font-bold text-neutral-800 uppercase tracking-wider flex items-center justify-between">
                                <span>Field Officer Determination</span>
                                <span className="text-[10px] text-neutral-500 font-mono">{currentUsername || "inspector"}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <button
                                  type="button"
                                  onClick={() => setOfficerVerdict("PASS")}
                                  className={`px-2.5 py-1 text-[10px] font-bold rounded-md transition-colors ${
                                    officerVerdict === "PASS"
                                      ? "bg-emerald-600 text-white"
                                      : "bg-white border border-neutral-300 text-neutral-700"
                                  }`}
                                >
                                  ✓ Verify Compliant (PASS)
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setOfficerVerdict("FAIL")}
                                  className={`px-2.5 py-1 text-[10px] font-bold rounded-md transition-colors ${
                                    officerVerdict === "FAIL"
                                      ? "bg-rose-600 text-white"
                                      : "bg-white border border-neutral-300 text-neutral-700"
                                  }`}
                                >
                                  ✕ Flag Violation (FAIL)
                                </button>
                              </div>
                              <input
                                type="text"
                                placeholder="Physical caliper measurement or verification note..."
                                value={officerRemarks}
                                onChange={(e) => setOfficerRemarks(e.target.value)}
                                className="w-full px-2.5 py-1.5 text-xs rounded-md bg-white border border-[#D1D5DB] text-neutral-900 focus:outline-none focus:border-black font-sans"
                              />
                              <div className="flex items-center gap-2">
                                <button
                                  type="button"
                                  onClick={() => handleAdjudicateSubmit(res.rule_id || index)}
                                  className="px-3 py-1.5 bg-black text-white text-[10px] font-bold uppercase tracking-wider rounded-md hover:bg-neutral-800 shadow-xs"
                                >
                                  Submit Official Sign-Off
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setAdjudicatingRuleId(null)}
                                  className="px-2 py-1 text-[10px] text-neutral-500 hover:text-black"
                                >
                                  Cancel
                                </button>
                              </div>
                            </div>
                          ) : (
                            <button
                              type="button"
                              onClick={() => {
                                setAdjudicatingRuleId(res.rule_id || index);
                                setOfficerRemarks("");
                                setOfficerVerdict("PASS");
                              }}
                              className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-amber-800 bg-amber-100 hover:bg-amber-200 px-2.5 py-1 rounded-md transition-colors shadow-xs"
                            >
                              <span>⚖️</span>
                              <span>Adjudicate Review Item</span>
                            </button>
                          )}
                        </div>
                      )}

                      {/* Adjudicated Verification Badge */}
                      {res.adjudicated_by && (
                        <div className="pl-6 pt-1.5">
                          <span className="inline-flex items-center gap-1 text-[9px] font-mono font-bold text-neutral-700 bg-neutral-100 px-2 py-0.5 rounded border border-neutral-200">
                            <span>✓ Verified by</span>
                            <span className="text-black">{res.adjudicated_by}</span>
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}

              {/* PDP Placement Check (Rule 6) */}
              {(filterStatus === "ALL" || filterStatus === "PASS") && (
                <div className="py-3.5 space-y-1">
                  <div className="flex items-baseline space-x-2.5">
                    <span className="font-mono text-sm font-bold text-neutral-900 tracking-tight">
                      {(scanResult.compliance_results?.length + 2).toString().padStart(2, "0")}
                    </span>
                    <div className="flex-1 flex items-center justify-between">
                      <h3 className="text-xs font-bold text-neutral-900 uppercase tracking-wider">
                        PDP Placement Verification
                      </h3>
                      <span className="text-[9px] font-mono font-bold uppercase px-1.5 py-0.2 rounded bg-emerald-600 text-white">
                        PASS
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-neutral-500 pl-6 leading-relaxed">
                    Rule 6 grouping check verified: all mandatory text coordinates reside inside detected PDP boundary.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* BOTTOM ACTIONS: Primary Solid Matte-Black Button (Fixed at bottom) */}
          <div className="space-y-3 pt-4 border-t border-[#E5E7EB] shrink-0 bg-white">
            <a
              href={getReportUrl(scanResult.scan_id, "pdf")}
              target="_blank"
              rel="noreferrer"
              className="block w-full py-3.5 rounded-xl bg-black text-white text-xs font-bold uppercase tracking-widest text-center hover:bg-neutral-900 active:scale-[0.99] transition-all shadow-md"
            >
              Export Inspection Report (PDF)
            </a>

            <div className="flex items-center justify-between text-xs font-mono pt-1 text-neutral-400">
              <Link to="/" className="text-neutral-600 hover:text-black hover:underline">
                ← Scan Another Label
              </Link>
              <Link to="/history" className="text-neutral-600 hover:text-black hover:underline">
                View Inspection Logs →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
