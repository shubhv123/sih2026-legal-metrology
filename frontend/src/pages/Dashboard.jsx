// Owner: Keshav
// Dashboard page — Analytics & Monitoring matching docs/API_CONTRACT.md
// Styled in the luxury minimalist porcelain & stark-white design system with Recharts.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  AreaChart,
  Area,
  CartesianGrid,
} from "recharts";
import { getDashboardStats, getCurrentRole, getCurrentUsername } from "../api/client";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const currentRole = getCurrentRole();
  const currentUsername = getCurrentUsername();

  useEffect(() => {
    getDashboardStats()
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="py-24 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-neutral-300 border-t-black rounded-full animate-spin mx-auto" />
        <p className="text-neutral-500 text-xs font-mono uppercase tracking-widest">
          Aggregating Compliance Analytics...
        </p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="py-20 text-center text-neutral-500 bg-white rounded-2xl border border-[#E5E7EB] p-8">
        Unable to load dashboard statistics.
      </div>
    );
  }

  // Calculate compliance rate percentage
  const complianceRate =
    stats.compliance_rate_pct != null
      ? Math.round(stats.compliance_rate_pct)
      : stats.total_scans > 0
      ? Math.round(((stats.compliant_count || stats.pass_count || 0) / stats.total_scans) * 100)
      : 0;

  // Format violations data into recharts array
  const violationsData =
    Array.isArray(stats.most_common_violations) && stats.most_common_violations.length > 0
      ? stats.most_common_violations.map((v) => ({
          field: (v.label || v.rule_id || "Violation").replace(/^RULE_\d+_/, "").replace(/_/g, " "),
          violations: v.count,
        }))
      : Object.entries(stats.violations_by_field || {}).map(([field, count]) => ({
          field: field.replace(/^RULE_\d+_/, "").replace(/_/g, " "),
          violations: count,
        }));

  const statusBadgeStyle = {
    PASS: "bg-emerald-50 text-emerald-700 border-emerald-200",
    FAIL: "bg-rose-50 text-rose-700 border-rose-200",
    REVIEW_REQUIRED: "bg-amber-50 text-amber-700 border-amber-200",
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E5E7EB] pb-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-neutral-900 font-sans">
            Enforcement Compliance Analytics
          </h1>
          <p className="text-xs text-neutral-500 mt-1">
            Real-time monitoring of packaged commodity inspections, violation distributions, and officer queues.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <div className="px-3 py-1.5 rounded-lg bg-white border border-[#E5E7EB] text-[11px] font-mono text-neutral-600 shadow-xs">
            Active Ruleset: <span className="text-black font-bold">{stats.rule_version}</span>
          </div>
          <Link
            to="/"
            className="px-3.5 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-black hover:bg-neutral-900 text-white transition-colors shadow-sm"
          >
            + Scan Label
          </Link>
        </div>
      </div>

      {/* KPI METRIC CARDS */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Scans */}
        <div className="bg-white p-5 rounded-2xl border border-[#E5E7EB] shadow-xs space-y-1">
          <div className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest">
            Total Audits
          </div>
          <div className="text-2xl font-extrabold text-neutral-900 font-mono">{stats.total_scans}</div>
          <p className="text-[11px] text-neutral-500">Labels processed</p>
        </div>

        {/* Compliant PASS */}
        <div className="bg-white p-5 rounded-2xl border border-emerald-200/80 shadow-xs space-y-1">
          <div className="text-[10px] font-bold text-emerald-700 uppercase tracking-widest flex items-center justify-between">
            <span>Pass (Compliant)</span>
            <span>✓</span>
          </div>
          <div className="text-2xl font-extrabold text-emerald-600 font-mono">
            {stats.compliant_count ?? stats.pass_count ?? 0}
          </div>
          <p className="text-[11px] text-neutral-500">Rule 6 & 7 compliant</p>
        </div>

        {/* Non-Compliant FAIL */}
        <div className="bg-white p-5 rounded-2xl border border-rose-200/80 shadow-xs space-y-1">
          <div className="text-[10px] font-bold text-rose-700 uppercase tracking-widest flex items-center justify-between">
            <span>Fail (Violations)</span>
            <span>✕</span>
          </div>
          <div className="text-2xl font-extrabold text-rose-600 font-mono">
            {stats.non_compliant_count ?? stats.fail_count ?? 0}
          </div>
          <p className="text-[11px] text-neutral-500">Statutory notice flagged</p>
        </div>

        {/* Review Required */}
        <div className="bg-white p-5 rounded-2xl border border-amber-200/80 shadow-xs space-y-1">
          <div className="text-[10px] font-bold text-amber-700 uppercase tracking-widest flex items-center justify-between">
            <span>Review Queue</span>
            <span>⚠️</span>
          </div>
          <div className="text-2xl font-extrabold text-amber-600 font-mono">
            {stats.review_required_count ?? 0}
          </div>
          <p className="text-[11px] text-neutral-500">Officer verification needed</p>
        </div>

        {/* Compliance Rate */}
        <div className="col-span-2 lg:col-span-1 bg-white p-5 rounded-2xl border border-[#E5E7EB] shadow-xs space-y-1">
          <div className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest">
            Compliance Index
          </div>
          <div className="text-2xl font-extrabold text-neutral-900 font-mono">{complianceRate}%</div>
          <div className="w-full bg-neutral-100 h-1.5 rounded-full overflow-hidden mt-2">
            <div
              className="bg-black h-full rounded-full transition-all duration-500"
              style={{ width: `${complianceRate}%` }}
            />
          </div>
        </div>
      </div>

      {/* CHARTS SECTION (2 COLUMNS) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Compliance Trend Over Time */}
        <div className="lg:col-span-7 bg-white p-6 rounded-2xl border border-[#E5E7EB] shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-[#F0F2F5] pb-3">
            <div>
              <h2 className="text-sm font-bold text-neutral-900 uppercase tracking-wider">
                Inspection Verdict Trend
              </h2>
              <p className="text-xs text-neutral-500">Historical compliance vs violations over time</p>
            </div>
            <span className="text-[10px] font-mono text-neutral-400">TELEMETRY</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={stats.compliance_trend}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="colorCompliant" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#059669" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#059669" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorNonCompliant" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#DC2626" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#DC2626" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#F0F2F5" />
                <XAxis dataKey="date" stroke="#9CA3AF" fontSize={11} />
                <YAxis stroke="#9CA3AF" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#FFFFFF",
                    borderColor: "#E5E7EB",
                    borderRadius: "8px",
                    fontSize: "12px",
                    color: "#18181B",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.05)",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
                <Area
                  type="monotone"
                  dataKey="compliant"
                  name="Pass (Compliant)"
                  stroke="#059669"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorCompliant)"
                />
                <Area
                  type="monotone"
                  dataKey="non_compliant"
                  name="Fail (Violations)"
                  stroke="#DC2626"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorNonCompliant)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Violations By Field Breakdown */}
        <div className="lg:col-span-5 bg-white p-6 rounded-2xl border border-[#E5E7EB] shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-[#F0F2F5] pb-3">
            <div>
              <h2 className="text-sm font-bold text-neutral-900 uppercase tracking-wider">
                Violations by Rule Field
              </h2>
              <p className="text-xs text-neutral-500">Most frequent non-compliances flagged</p>
            </div>
            <span className="text-[10px] font-mono text-neutral-400">RULE 6 / 7</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={violationsData}
                layout="vertical"
                margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#F0F2F5" horizontal={false} />
                <XAxis type="number" stroke="#9CA3AF" fontSize={11} />
                <YAxis
                  dataKey="field"
                  type="category"
                  stroke="#9CA3AF"
                  fontSize={11}
                  width={110}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#FFFFFF",
                    borderColor: "#E5E7EB",
                    borderRadius: "8px",
                    fontSize: "12px",
                    color: "#18181B",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.05)",
                  }}
                />
                <Bar
                  dataKey="violations"
                  name="Count"
                  fill="#18181B"
                  radius={[0, 4, 4, 0]}
                  barSize={18}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* RECENT INSPECTION ACTIVITY TABLE */}
      {Array.isArray(stats.recent_activity) && stats.recent_activity.length > 0 && (
        <div className="bg-white rounded-2xl border border-[#E5E7EB] shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[#F0F2F5] pb-3">
            <div>
              <h2 className="text-sm font-bold text-neutral-900 uppercase tracking-wider">
                Recent Inspection Activity
              </h2>
              <p className="text-xs text-neutral-500">Live stream of incoming audit records</p>
            </div>
            <Link
              to="/history"
              className="text-xs font-semibold text-neutral-700 hover:text-black hover:underline"
            >
              View Full History →
            </Link>
          </div>

          <div className="divide-y divide-[#F0F2F5]">
            {stats.recent_activity.map((activity, idx) => (
              <div
                key={activity.scan_id || idx}
                className="py-3 flex items-center justify-between text-xs"
              >
                <div className="flex items-center space-x-3">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${
                      statusBadgeStyle[activity.overall_status] || "bg-neutral-100 text-neutral-700"
                    }`}
                  >
                    {activity.overall_status}
                  </span>
                  <span className="font-bold text-neutral-900">
                    {activity.product_name || "Scanned Commodity"}
                  </span>
                  <span className="text-[11px] font-mono text-neutral-400">
                    ID: {activity.scan_id}
                  </span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-neutral-400 font-mono text-[11px]">
                    {new Date(activity.created_at).toLocaleString()}
                  </span>
                  <Link
                    to={`/results/${activity.scan_id}`}
                    className="px-2.5 py-1 rounded bg-neutral-100 hover:bg-neutral-200 text-neutral-800 font-semibold"
                  >
                    View
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ADMIN CONTROL & STATUTORY AUDIT METADATA CARD (Visible for Admin role) */}
      {(currentRole === "admin" || !currentRole) && (
        <div className="bg-white p-6 rounded-2xl border border-neutral-300/80 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#F0F2F5] pb-3">
            <div>
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-blue-600" />
                <h3 className="text-xs font-bold text-neutral-900 uppercase tracking-wider">
                  Admin Regulatory Governance & Rule Engine Audit
                </h3>
              </div>
              <p className="text-[11px] text-neutral-500 mt-0.5">
                Statutory configuration and exception taxonomy active on this node.
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-neutral-100 text-neutral-800 border border-neutral-200">
                ROLE: {currentRole?.toUpperCase() || "DEMO ADMIN"}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
            <div className="p-3 bg-neutral-50 rounded-xl border border-neutral-200 space-y-1">
              <span className="text-[10px] text-neutral-400 uppercase font-bold tracking-wider">Rule Version Stamp</span>
              <p className="text-neutral-900 font-bold">{stats.rule_version || "LMPC-2011-v1.1"}</p>
              <p className="text-[10px] text-neutral-500 font-sans">Single source of truth in lmpc_rules_v1.json</p>
            </div>

            <div className="p-3 bg-neutral-50 rounded-xl border border-neutral-200 space-y-1">
              <span className="text-[10px] text-neutral-400 uppercase font-bold tracking-wider">Statutory Exceptions (3/3)</span>
              <p className="text-emerald-700 font-bold">medical_device • bulk_exempt • food_expiry</p>
              <p className="text-[10px] text-neutral-500 font-sans">Enforced per statutory taxonomy limits</p>
            </div>

            <div className="p-3 bg-neutral-50 rounded-xl border border-neutral-200 space-y-1">
              <span className="text-[10px] text-neutral-400 uppercase font-bold tracking-wider">Storage & Database</span>
              <p className="text-neutral-900 font-bold">SQLite compliance.db (WAL Mode)</p>
              <p className="text-[10px] text-neutral-500 font-sans">Zero external infra dependencies required</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
