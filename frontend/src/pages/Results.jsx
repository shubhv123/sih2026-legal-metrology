// Owner: Keshav
// Day 3: build against mock scan result (pass sample JSON as props for now).
// Day 6: wire to real navigation from Upload page (react-router, /results/:scan_id)
//
// This page is what judges will look at most during the demo - make the
// PASS/FAIL/REVIEW_REQUIRED distinction visually obvious (colors: green/red/amber),
// and show the evidence image prominently per the "evidence-first" pitch angle.

export default function Results({ scanResult }) {
  if (!scanResult) return <p>No scan result to display.</p>;

  const statusColor = {
    PASS: "green",
    FAIL: "red",
    REVIEW_REQUIRED: "orange",
  };

  return (
    <div>
      <h1>Scan Result</h1>
      <div style={{ padding: 12, background: statusColor[scanResult.overall_status] }}>
        Overall Status: {scanResult.overall_status}
      </div>

      <img src={scanResult.evidence_image_url} alt="Evidence with annotations" style={{ maxWidth: "100%" }} />

      <h2>Compliance Findings</h2>
      <ul>
        {scanResult.compliance_results.map((r) => (
          <li key={r.rule_id} style={{ color: statusColor[r.status] }}>
            <strong>{r.field_name}</strong>: {r.status} ({Math.round(r.confidence * 100)}% confidence)
            <br />
            {r.message}
            <br />
            <small>Rule: {r.rule_id} — {r.rule_version}</small>
          </li>
        ))}
      </ul>

      {/* TODO(keshav): add "Download Report" buttons using getReportUrl(scanId, 'pdf'|'docx'|'json') */}
    </div>
  );
}
