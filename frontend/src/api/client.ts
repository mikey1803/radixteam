/**
 * Shared API client. Every page imports from here — no duplicated fetch logic.
 * Matches the shared data contract shapes (see backend/app/shared/schemas/skill.py).
 */
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface Skill {
  skill_name: string;
  category_code: string;
  evidence: string;
  confidence: "high" | "medium" | "low";
}

export interface ExtractedSkillList {
  source_type: "jd" | "resume";
  source_file: string;
  company?: string;
  role?: string;
  title?: string;
  experience?: string;
  education?: string;
  skills: Skill[];
  responsibilities: string[];
  technologies: string[];
  soft_skills: string[];
  industry?: string;
}

export interface JobRecord {
  id: string;
  filename: string;
  extracted: ExtractedSkillList;
}

export interface CandidateProfile {
  id?: string;
  name: string;
  email: string;
  education?: string;
  skills: Skill[];
  hackathons: string[];
  internships: string[];
  certifications: string[];
  preferred_roles: string[];
  cv_file?: string;
}

export interface TalentCheckResult {
  company: string;
  skillset_gap: { category_code: string; required_level: number; candidate_level: number; gap: boolean }[];
  readiness_score: number;
}

export interface SkillMatchResult {
  jd_source_file: string;
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
}

async function handleResponse<T>(res: Response): Promise<T> {
  const body = await res.json();
  if (!res.ok || body.success === false) {
    throw new Error(body.message || `Request failed with status ${res.status}`);
  }
  return body.data as T;
}

export const jdAnalyticsApi = {
  upload: async (file: File): Promise<JobRecord> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/jobs/upload`, { method: "POST", body: form });
    return handleResponse<JobRecord>(res);
  },
  list: async (): Promise<JobRecord[]> => {
    const res = await fetch(`${API_BASE}/jobs`);
    return handleResponse<JobRecord[]>(res);
  },
  get: async (id: string): Promise<JobRecord> => {
    const res = await fetch(`${API_BASE}/jobs/${id}`);
    return handleResponse<JobRecord>(res);
  },
};

export const resumeParserApi = {
  upload: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/resumes/upload`, { method: "POST", body: form });
    return handleResponse<any>(res);
  },
};

export const profileBuilderApi = {
  create: async (profile: CandidateProfile) => {
    const res = await fetch(`${API_BASE}/profiles`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    return handleResponse<CandidateProfile>(res);
  },
};

export const talentCheckApi = {
  run: async (profile: CandidateProfile, company: string): Promise<TalentCheckResult> => {
    const res = await fetch(`${API_BASE}/talent-check/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile, company }),
    });
    return handleResponse<TalentCheckResult>(res);
  },
};

export const skillMatchingApi = {
  run: async (candidate_skills: Skill[], jd_skill_list: ExtractedSkillList): Promise<SkillMatchResult> => {
    const res = await fetch(`${API_BASE}/skill-match/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ candidate_skills, jd_skill_list }),
    });
    return handleResponse<SkillMatchResult>(res);
  },
};
