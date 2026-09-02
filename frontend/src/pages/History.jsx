// Owner: Keshav
// Day 4: build against mock /history. Wire filters to query params.

import { useEffect, useState } from "react";
import { getHistory } from "../api/client";

export default function History() {
  const [results, setResults] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    getHistory({ status: statusFilter || undefined })
      .then((data) => setResults(data.results))
      .catch(console.error);
  }, [statusFilter]);

  return (
    <div>
      <h1>Scan History</h1>
      <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
        <option value="">All</option>
        <option value="PASS">Pass</option>
        <option value="FAIL">Fail</option>
        <option value="REVIEW_REQUIRED">Review Required</option>
      </select>
      <ul>
        {results.map((r) => (
          <li key={r.scan_id}>
            {r.product_name_hint} — {r.overall_status} — {r.timestamp}
          </li>
        ))}
      </ul>
    </div>
  );
}
