// Owner: Keshav
// Day 5: build against mock /dashboard/stats. Use recharts for the trend chart.

import { useEffect, useState } from "react";
import { getDashboardStats } from "../api/client";

export default function Dashboard() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    getDashboardStats().then(setStats).catch(console.error);
  }, []);

  if (!stats) return <p>Loading...</p>;

  return (
    <div>
      <h1>Compliance Dashboard</h1>
      <div>
        <span>Total Scans: {stats.total_scans}</span>
        <span>Compliant: {stats.compliant_count}</span>
        <span>Non-Compliant: {stats.non_compliant_count}</span>
        <span>Review Required: {stats.review_required_count}</span>
      </div>
      {/* TODO(keshav): recharts BarChart for violations_by_field,
          LineChart for compliance_trend */}
      <p>Rule version: {stats.rule_version}</p>
    </div>
  );
}
