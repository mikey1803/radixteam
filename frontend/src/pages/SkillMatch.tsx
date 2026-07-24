import { useState } from "react";
import { skillMatchingApi, SkillMatchResult, Skill, ExtractedSkillList } from "../api/client";

/**
 * STUB for Role 5. Uses sample candidate skills + a sample JD skill list
 * (matching the shape Role 1 / JD Analytics produces) so the flow works
 * standalone. Wire the real JD selector + real candidate profile once
 * those pieces are integrated.
 */
const SAMPLE_CANDIDATE_SKILLS: Skill[] = [
  { skill_name: "Python", category_code: "COD", evidence: "sample", confidence: "high" },
  { skill_name: "PostgreSQL", category_code: "SQL", evidence: "sample", confidence: "high" },
];

const SAMPLE_JD_SKILLS: ExtractedSkillList = {
  source_type: "jd",
  source_file: "sample_jd.pdf",
  skills: [
    { skill_name: "Python", category_code: "COD", evidence: "sample", confidence: "high" },
    { skill_name: "Postgres", category_code: "SQL", evidence: "sample", confidence: "high" },
    { skill_name: "Kubernetes", category_code: "CLOUD", evidence: "sample", confidence: "medium" },
  ],
  responsibilities: [],
  technologies: [],
  soft_skills: [],
};

export default function SkillMatch() {
  const [result, setResult] = useState<SkillMatchResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleRun = async () => {
    setLoading(true);
    try {
      const r = await skillMatchingApi.run(SAMPLE_CANDIDATE_SKILLS, SAMPLE_JD_SKILLS);
      setResult(r);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Skill Matching <small style={{ color: "#999" }}>(stub — Role 5)</small></h2>
      <button onClick={handleRun} disabled={loading}>
        {loading ? "Matching..." : "Run Skill Match (sample data)"}
      </button>

      {result && (
        <div style={{ marginTop: 16 }}>
          <h3>Match Score: {result.match_score}%</h3>
          <p><strong>Matched:</strong> {result.matched_skills.join(", ") || "—"}</p>
          <p><strong>Missing:</strong> {result.missing_skills.join(", ") || "—"}</p>
        </div>
      )}
    </div>
  );
}
