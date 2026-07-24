import { useState } from "react";
import { talentCheckApi, TalentCheckResult, CandidateProfile } from "../api/client";

/**
 * STUB for Role 4. Uses a sample profile so the button works standalone;
 * wire this up to a real saved profile (from Profile Builder) once
 * profile selection UI exists.
 */
const SAMPLE_PROFILE: CandidateProfile = {
  name: "Sample Candidate",
  email: "sample@example.com",
  skills: [
    { skill_name: "Python", category_code: "COD", evidence: "sample", confidence: "high" },
    { skill_name: "SQL", category_code: "SQL", evidence: "sample", confidence: "high" },
  ],
  hackathons: [],
  internships: [],
  certifications: [],
  preferred_roles: [],
};

export default function TalentCheck() {
  const [company, setCompany] = useState("Google");
  const [result, setResult] = useState<TalentCheckResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleRun = async () => {
    setLoading(true);
    try {
      const r = await talentCheckApi.run(SAMPLE_PROFILE, company);
      setResult(r);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Talent Check <small style={{ color: "#999" }}>(stub — Role 4)</small></h2>
      <select value={company} onChange={(e) => setCompany(e.target.value)}>
        <option>Google</option>
        <option>Microsoft</option>
        <option>Oracle Financial Services Software</option>
      </select>
      <button onClick={handleRun} disabled={loading} style={{ marginLeft: 8 }}>
        {loading ? "Checking..." : "Run Talent Check"}
      </button>

      {result && (
        <div style={{ marginTop: 16 }}>
          <h3>Readiness Score: {result.readiness_score}%</h3>
          <table border={1} cellPadding={6} style={{ borderCollapse: "collapse", width: "100%" }}>
            <thead><tr><th>Category</th><th>Required</th><th>Candidate</th><th>Gap?</th></tr></thead>
            <tbody>
              {result.skillset_gap.map((g, i) => (
                <tr key={i} style={{ background: g.gap ? "#fee2e2" : "#dcfce7" }}>
                  <td>{g.category_code}</td>
                  <td>{g.required_level}</td>
                  <td>{g.candidate_level}</td>
                  <td>{g.gap ? "Yes" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
