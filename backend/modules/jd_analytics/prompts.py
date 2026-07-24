"""
AI extraction prompt — per Chapter 4.10.

Objective: extract Job Title, Skills, Responsibilities, Experience, Education,
Certifications, Technologies, Soft Skills, Industry as STRICT JSON — never
markdown, never explanation.

Tip from the hackathon brief: skill signal concentrates in "Key
Responsibilities" and "What We're Looking For" — the prompt nudges the model
there explicitly.
"""

JD_EXTRACTION_PROMPT_TEMPLATE = """You are extracting structured hiring data from a job description.

Map every requirement onto ONE of these 12 RADIX skill categories (use OTHER only
if nothing fits): DSA, COD, OOD, APTI, COMM, AI, CLOUD, SQL, SWE, SYSD, NETW, OS.

Pay special attention to any "Key Responsibilities" and "What We're Looking For"
sections — that's where most of the real skill signal lives. Do plain
keyword-matching AND semantic inference; JDs are written in natural prose on
purpose, so a skill may be implied without being named literally.

Return STRICT JSON ONLY, matching exactly this shape, with no markdown fences
and no explanation text before or after it:

{{
  "title": "",
  "experience": "",
  "education": "",
  "skills": [
    {{"skill_name": "", "category_code": "", "evidence": "", "confidence": "high|medium|low"}}
  ],
  "responsibilities": [],
  "technologies": [],
  "soft_skills": [],
  "industry": ""
}}

TEXT TO ANALYZE:
{jd_text}
"""


def build_jd_prompt(cleaned_text: str) -> str:
    return JD_EXTRACTION_PROMPT_TEMPLATE.format(jd_text=cleaned_text)
