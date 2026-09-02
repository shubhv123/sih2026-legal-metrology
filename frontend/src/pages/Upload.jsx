// Owner: Keshav
// Day 1-2: build this against the mock /scan response.
// Day 6: connect to Shubh's real pipeline - shape doesn't change.

import { useState } from "react";
import { scanLabel } from "../api/client";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [calibrationMethod, setCalibrationMethod] = useState("aruco");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const scanResult = await scanLabel(file, calibrationMethod);
      setResult(scanResult);
      // TODO(keshav): navigate to /results/:scan_id instead of inline display,
      // once React Router is wired up
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1>Scan a Product Label</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <select
          value={calibrationMethod}
          onChange={(e) => setCalibrationMethod(e.target.value)}
        >
          <option value="aruco">ArUco Marker</option>
          <option value="known_object">Known Object (coin, etc.)</option>
          <option value="none">No calibration (skip font check)</option>
        </select>
        <button type="submit" disabled={loading}>
          {loading ? "Scanning..." : "Scan"}
        </button>
      </form>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {result && (
        <pre>{JSON.stringify(result, null, 2)}</pre>
        /* TODO(keshav): replace with the real Results component -
           PASS/FAIL/REVIEW cards per compliance_results entry,
           evidence image with bboxes, overall_status banner */
      )}
    </div>
  );
}
