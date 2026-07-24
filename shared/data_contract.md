# Shared Data Contract

Canonical version lives in code at `backend/app/shared/schemas/skill.py`
(Pydantic models) and mirrors `frontend/src/api/client.ts` (TypeScript
interfaces) exactly. This file is the human-readable reference — if you
change one, change all three.

## Skill
```json
{ "skill_name": "...", "category_code": "DSA|COD|OOD|APTI|COMM|AI|CLOUD|SQL|SWE|SYSD|NETW|OS|OTHER", "evidence": "...", "confidence": "high|medium|low" }
```

## ExtractedSkillList (JD Analytics / Resume Parser output)
```json
{ "source_type": "jd|resume", "source_file": "...", "company": "...", "role": "...", "skills": [Skill, ...] }
```

## CandidateProfile (Profile Builder output)
```json
{ "name": "...", "email": "...", "education": "...", "skills": [Skill, ...], "hackathons": [...], "internships": [...], "certifications": [...], "preferred_roles": [...], "cv_file": "..." }
```

## TalentCheckResult
```json
{ "company": "...", "skillset_gap": [{ "category_code": "...", "required_level": 1-10, "candidate_level": 1-10, "gap": true }], "readiness_score": 0-100 }
```

## SkillMatchResult
```json
{ "jd_source_file": "...", "match_score": 0-100, "matched_skills": [...], "missing_skills": [...] }
```

## 12 Skill Categories
DSA, COD, OOD, APTI, COMM, AI, CLOUD, SQL, SWE, SYSD, NETW, OS (+ OTHER as fallback)
