"""
AI prompts for the Talent Check module.
"""

RESUME_PARSE_PROMPT = """You are an expert resume parser. Extract structured data from the following resume text.

Return ONLY a valid JSON object with these exact keys:
{{
  "name": "Full Name",
  "email": "email@example.com or null",
  "phone": "phone number or null",
  "skills": ["skill1", "skill2", ...],
  "experience_years": 0.0,
  "education": [{{"degree": "...", "institution": "...", "year": "..."}}]
}}

Resume text:
---
{resume_text}
---

Return ONLY the JSON, no markdown, no explanation."""


TALENT_CHECK_PROMPT = """You are an expert talent evaluator. Evaluate the candidate against the job description.

CANDIDATE PROFILE:
- Name: {candidate_name}
- Skills: {candidate_skills}
- Experience: {experience_years} years
- Education: {education}
- Resume: {resume_text}

JOB DESCRIPTION:
- Title: {jd_title}
- Company: {jd_company}
- Description: {jd_description}
- Required Skills: {required_skills}
- Preferred Skills: {preferred_skills}
- Minimum Experience: {min_experience} years

Evaluate and return ONLY a valid JSON object:
{{
  "overall_score": 0-100,
  "skill_match_score": 0-100,
  "experience_score": 0-100,
  "matched_skills": ["skills the candidate has that match the JD"],
  "skill_gaps": ["required skills the candidate is missing"],
  "reasoning": "2-3 sentence explanation of the evaluation"
}}

Return ONLY the JSON, no markdown, no explanation."""


INTERVIEW_QUESTIONS_PROMPT = """You are an expert interviewer. Generate targeted interview questions based on the skill gaps and job requirements.

JOB TITLE: {jd_title}
JOB DESCRIPTION: {jd_description}
CANDIDATE SKILLS: {candidate_skills}
SKILL GAPS: {skill_gaps}
MATCHED SKILLS: {matched_skills}

Generate 5-7 interview questions that:
1. Probe the candidate's depth in matched skills
2. Assess awareness of gap areas
3. Evaluate problem-solving ability relevant to the role

Return ONLY a valid JSON array:
[
  {{"question": "Your question here?", "focus_area": "Skill or topic being assessed"}},
  ...
]

Return ONLY the JSON array, no markdown, no explanation."""
