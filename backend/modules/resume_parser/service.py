"""
Resume Parser Service — STUB for Role 2.

Whoever owns this role: reuse modules/jd_analytics/parser.py's
extract_text()/clean_text() functions (same PDF/DOCX extraction pattern —
per the hackathon brief "you may be able to share real code, not just a
data format"), then swap in a resume-specific prompt. This stub returns a
mock ExtractedSkillList (source_type="resume") that already matches the
shared contract, so Talent Check / Skill Matching / Profile Builder can be
wired against it today without waiting on the real implementation.
"""
from __future__ import annotations

from app.shared.schemas.skill import ExtractedSkillList, Skill
from .repository import ResumeRepository


class ResumeParserService:
    def __init__(self, repository: ResumeRepository | None = None):
        self.repository = repository or ResumeRepository()

    def process_upload(self, filename: str, raw_bytes: bytes) -> dict:
        # TODO(Role 2): replace with real extraction + AI call, reusing
        # modules/jd_analytics/parser.py's extract_text/clean_text and an
        # AIProvider().complete_json(prompt) call, same pattern as JD Analytics.
        mock_extracted = ExtractedSkillList(
            source_type="resume",
            source_file=filename,
            skills=[
                Skill(skill_name="Python", category_code="COD",
                      evidence="mock stub — replace with real parsing", confidence="low"),
                Skill(skill_name="SQL", category_code="SQL",
                      evidence="mock stub — replace with real parsing", confidence="low"),
            ],
            education="Mock: B.Tech Computer Science",
            experience="Mock: 2 years",
        )
        record = self.repository.insert({
            "filename": filename,
            "extracted": mock_extracted.model_dump(),
        })
        return record

    def get_resume(self, resume_id: str) -> dict | None:
        return self.repository.get(resume_id)

    def list_resumes(self) -> list[dict]:
        return self.repository.list()
