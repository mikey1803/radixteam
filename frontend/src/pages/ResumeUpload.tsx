import { useState } from "react";
import { resumeParserApi } from "../api/client";

/**
 * STUB for Role 2 (Resume Parser). Functional against the stub backend
 * (mock extraction) so the flow is demoable today. Swap in richer UI
 * (education/projects/experience fields) as the real service.py fills in.
 */
export default function ResumeUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const record = await resumeParserApi.upload(file);
      setResult(record);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Resume Parser <small style={{ color: "#999" }}>(stub — Role 2)</small></h2>
      <p>Upload a resume (PDF or DOCX). Currently backed by a mock extractor.</p>

      <input type="file" accept=".pdf,.docx" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      <button onClick={handleUpload} disabled={!file || loading} style={{ marginLeft: 8 }}>
        {loading ? "Parsing..." : "Upload & Parse"}
      </button>

      {result && (
        <pre style={{ background: "#f3f4f6", padding: 12, marginTop: 16 }}>
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
