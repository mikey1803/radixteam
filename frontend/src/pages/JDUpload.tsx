import { useState } from "react";
import { jdAnalyticsApi, JobRecord } from "../api/client";

export default function JDUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<JobRecord | null>(null);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const record = await jdAnalyticsApi.upload(file);
      setResult(record);
    } catch (e: any) {
      setError(e.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>JD Analytics</h2>
      <p>Upload a job description (PDF or DOCX). This calls <code>POST /jobs/upload</code>.</p>

      <input
        type="file"
        accept=".pdf,.docx"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
      />
      <button onClick={handleUpload} disabled={!file || loading} style={{ marginLeft: 8 }}>
        {loading ? "Analyzing..." : "Upload & Analyze"}
      </button>

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {result && (
        <div style={{ marginTop: 24 }}>
          <h3>{result.extracted.title || result.filename}</h3>
          <p><strong>Job ID:</strong> {result.id}</p>
          <p><strong>Industry:</strong> {result.extracted.industry}</p>

          <h4>Extracted Skills</h4>
          <table border={1} cellPadding={6} style={{ borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr><th>Skill</th><th>Category</th><th>Confidence</th><th>Evidence</th></tr>
            </thead>
            <tbody>
              {result.extracted.skills.map((s, i) => (
                <tr key={i}>
                  <td>{s.skill_name}</td>
                  <td>{s.category_code}</td>
                  <td>{s.confidence}</td>
                  <td style={{ fontSize: 12, color: "#555" }}>{s.evidence}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h4>Technologies</h4>
          <p>{result.extracted.technologies.join(", ") || "—"}</p>

          <details style={{ marginTop: 16 }}>
            <summary>Raw JSON (for Skill Matching / integration)</summary>
            <pre style={{ background: "#f3f4f6", padding: 12, overflowX: "auto" }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}
