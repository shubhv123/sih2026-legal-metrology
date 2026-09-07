// Owner: Keshav
// History & Search page matching docs/API_CONTRACT.md
// Styled in the luxury minimalist porcelain & stark-white design system.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHistory, searchScans, resolveImageUrl } from "../api/client";

export default function History() {
  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      if (searchQuery.trim()) {
        const data = await searchScans(searchQuery.trim(), {
          page,
          page_size: 10,
          status: statusFilter === "ALL" ? undefined : statusFilter,
          category: categoryFilter === "ALL" ? undefined : categoryFilter,
        });
        setResults(data.results || data.items || []);
        setTotal(data.total || 0);
      } else {
        const params = {
          page,
          page_size: 10,
          status: statusFilter === "ALL" ? undefined : statusFilter,
          category: categoryFilter === "ALL" ? undefined : categoryFilter,
        };
        const data = await getHistory(params);
        setResults(data.results || data.items || []);
        setTotal(data.total || 0);
      }
    } catch (err) {
      console.error("Failed to load history:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [page, statusFilter, categoryFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchHistory();
  };

  const statusBadgeStyle = {
    PASS: "bg-emerald-50 text-emerald-700 border-emerald-200",
    FAIL: "bg-rose-50 text-rose-700 border-rose-200",
    REVIEW_REQUIRED: "bg-amber-50 text-amber-700 border-amber-200",
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E5E7EB] pb-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-neutral-900 font-sans">
            Inspection Logs & Repository
          </h1>
          <p className="text-xs text-neutral-500 mt-1">
            Browse and retrieve previous packaged commodity compliance audits, violation records, and evidence.
          </p>
        </div>
        <Link
          to="/"
          className="self-start sm:self-auto px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider bg-black hover:bg-neutral-900 text-white shadow transition-colors"
        >
          + New Label Scan
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-[#E5E7EB] shadow-xs flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} className="w-full md:w-96 flex items-center gap-2">
          <div className="relative w-full">
            <span className="absolute left-3 top-2.5 text-xs text-neutral-400">🔍</span>
            <input
              type="text"
              placeholder="Search product, brand, or scan ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-2 text-xs rounded-lg bg-neutral-50 border border-[#D1D5DB] text-neutral-900 placeholder-neutral-400 focus:outline-none focus:border-black font-sans"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-lg bg-neutral-900 hover:bg-black text-white transition-colors"
          >
            Search
          </button>
        </form>

        {/* Filters: Category & 3-State Verdict */}
        <div className="flex items-center gap-2 self-start md:self-auto flex-wrap">
          {/* Category Dropdown */}
          <select
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setPage(1);
            }}
            className="px-2.5 py-1.5 rounded-lg text-xs font-mono bg-neutral-50 border border-[#D1D5DB] text-neutral-800 focus:outline-none focus:border-black"
          >
            <option value="ALL">All Categories</option>
            <option value="standard_retail">Standard Retail</option>
            <option value="food_expiry">Food Item</option>
            <option value="medical_device">Medical Device</option>
            <option value="bulk_exempt">Bulk Exempt</option>
          </select>

          {/* 3-State Filter Pills */}
          <div className="flex items-center gap-1">
            {["ALL", "PASS", "FAIL", "REVIEW_REQUIRED"].map((st) => (
              <button
                key={st}
                onClick={() => {
                  setStatusFilter(st);
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                  statusFilter === st
                    ? "bg-black text-white shadow-xs"
                    : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200/80"
                }`}
              >
                {st === "ALL" ? "All" : st.replace("_", " ")}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* History Items List */}
      <div className="bg-white rounded-2xl border border-[#E5E7EB] shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-20 text-center space-y-3">
            <div className="w-8 h-8 border-2 border-neutral-300 border-t-black rounded-full animate-spin mx-auto" />
            <p className="text-neutral-500 text-xs font-mono uppercase tracking-widest">
              Querying Stored Inspection Records...
            </p>
          </div>
        ) : results.length === 0 ? (
          <div className="py-16 text-center space-y-2 text-neutral-400">
            <div className="text-3xl">📭</div>
            <p className="text-xs font-medium">No inspection records found matching criteria.</p>
          </div>
        ) : (
          <div className="divide-y divide-[#F0F2F5]">
            {results.map((item) => (
              <div
                key={item.scan_id}
                className="p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-neutral-50/60 transition-colors"
              >
                {/* Left: Thumbnail & Meta */}
                <div className="flex items-center space-x-4">
                  {/* Thumbnail / Evidence icon */}
                  <div className="w-14 h-14 rounded-xl overflow-hidden bg-neutral-900 border border-[#E5E7EB] shrink-0 flex items-center justify-center">
                    {item.evidence_thumbnail_url ? (
                      <img
                        src={resolveImageUrl(item.evidence_thumbnail_url)}
                        alt="Evidence thumbnail"
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.currentTarget.src = "/kohaku_bottle.jpg";
                        }}
                      />
                    ) : (
                      <span className="text-xl">📦</span>
                    )}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                          statusBadgeStyle[item.overall_status] || "bg-neutral-100 text-neutral-700"
                        }`}
                      >
                        {item.overall_status}
                      </span>
                      <span className="text-[10px] font-mono text-neutral-400">
                        {new Date(item.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-neutral-900 mt-1">
                      {item.product_name_hint || "Unnamed Packaged Commodity"}
                    </h3>
                    <p className="text-[11px] font-mono text-neutral-500">ID: {item.scan_id}</p>
                  </div>
                </div>

                {/* Right: Actions */}
                <div className="flex items-center space-x-2 self-end sm:self-auto">
                  <Link
                    to={`/results/${item.scan_id}`}
                    className="px-3.5 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-black text-white hover:bg-neutral-900 transition-colors shadow-xs"
                  >
                    View Report →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination footer */}
        {total > 10 && (
          <div className="p-4 border-t border-[#E5E7EB] bg-neutral-50 flex items-center justify-between text-xs text-neutral-500 font-mono">
            <span>
              Showing {results.length} of {total} records
            </span>
            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-2.5 py-1 rounded border border-[#D1D5DB] bg-white text-neutral-700 hover:bg-neutral-50 disabled:opacity-40"
              >
                Prev
              </button>
              <span>Page {page}</span>
              <button
                disabled={page * 10 >= total}
                onClick={() => setPage((p) => p + 1)}
                className="px-2.5 py-1 rounded border border-[#D1D5DB] bg-white text-neutral-700 hover:bg-neutral-50 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
