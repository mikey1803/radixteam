import { useState } from "react";
import JDUpload from "./pages/JDUpload";
import ResumeUpload from "./pages/ResumeUpload";
import ProfileBuilder from "./pages/ProfileBuilder";
import TalentCheck from "./pages/TalentCheck";
import SkillMatch from "./pages/SkillMatch";

type TabKey = "jd" | "resume" | "profile" | "talent" | "match";

const TABS: { key: TabKey; label: string }[] = [
  { key: "jd", label: "1. JD Analytics" },
  { key: "resume", label: "2. Resume Parser" },
  { key: "profile", label: "3. Profile Builder" },
  { key: "talent", label: "4. Talent Check" },
  { key: "match", label: "5. Skill Matching" },
];

export default function App() {
  const [active, setActive] = useState<TabKey>("jd");

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", maxWidth: 960, margin: "0 auto", padding: 24 }}>
      <h1>RADIX Talent Match</h1>
      <nav style={{ display: "flex", gap: 8, marginBottom: 24, flexWrap: "wrap" }}>
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActive(tab.key)}
            style={{
              padding: "8px 14px",
              borderRadius: 6,
              border: "1px solid #ccc",
              background: active === tab.key ? "#1f2937" : "#f3f4f6",
              color: active === tab.key ? "white" : "#111",
              cursor: "pointer",
            }}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {active === "jd" && <JDUpload />}
      {active === "resume" && <ResumeUpload />}
      {active === "profile" && <ProfileBuilder />}
      {active === "talent" && <TalentCheck />}
      {active === "match" && <SkillMatch />}
    </div>
  );
}
