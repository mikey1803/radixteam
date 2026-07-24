import { useState } from "react";
import { profileBuilderApi, CandidateProfile } from "../api/client";

/**
 * STUB for Role 3. Real form + real save/load against the shared
 * CandidateProfile contract — extend with hackathons/certifications/CV
 * upload fields.
 */
export default function ProfileBuilder() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [saved, setSaved] = useState<CandidateProfile | null>(null);

  const handleSave = async () => {
    const profile: CandidateProfile = {
      name,
      email,
      skills: [
        { skill_name: "Python", category_code: "COD", evidence: "manual entry", confidence: "high" },
      ],
      hackathons: [],
      internships: [],
      certifications: [],
      preferred_roles: [],
    };
    const record = await profileBuilderApi.create(profile);
    setSaved(record);
  };

  return (
    <div>
      <h2>Profile Builder <small style={{ color: "#999" }}>(stub — Role 3)</small></h2>
      <div style={{ display: "flex", flexDirection: "column", gap: 8, maxWidth: 320 }}>
        <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
        <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <button onClick={handleSave} disabled={!name || !email}>Save Profile</button>
      </div>

      {saved && (
        <pre style={{ background: "#f3f4f6", padding: 12, marginTop: 16 }}>
          {JSON.stringify(saved, null, 2)}
        </pre>
      )}
    </div>
  );
}
