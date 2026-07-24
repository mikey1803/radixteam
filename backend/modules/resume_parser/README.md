# Resume Parser Module (STUB — Role 2)

This is a working stub, not the real implementation. It returns mock data
matching the shared `ExtractedSkillList` contract (source_type="resume") so
the rest of the team can integrate against it today.

**Role 2 owner: replace `service.py`'s `process_upload` with real logic.**
Recommended approach (per hackathon brief):
1. Reuse `modules/jd_analytics/parser.py` (`extract_text`, `clean_text`) —
   same PDF/DOCX extraction, no need to rewrite it.
2. Write a resume-specific prompt (resumes are messier/less standardized
   than JDs — build in tolerance for format variation).
3. Call `AIProvider().complete_json(prompt)` from `app.shared.ai.provider`.
4. Normalize with the same pattern as `modules/jd_analytics/utils.py`.
