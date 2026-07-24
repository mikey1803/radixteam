"""
Service Layer — per Chapter 2.8 / 4.14.
Business logic only. No SQL. No HTTP. No UI.

Workflow (Chapter 4.5 / 4.14):
    Validate -> Extract Text -> Clean -> AI Prompt -> Normalize -> Save -> Return
"""
from __future__ import annotations

import logging

from app.shared.ai.provider import AIProvider
from app.shared.exceptions import AIErrorApp
from app.shared.schemas.skill import ExtractedSkillList, Skill

from . import validators
from .parser import clean_text, extract_text
from .prompts import build_jd_prompt
from .repository import JobRepository
from .utils import normalize_ai_skills

logger = logging.getLogger("radix.jd_analytics")


class JDAnalyticsService:
    def __init__(self, repository: JobRepository | None = None, ai_provider: AIProvider | None = None):
        self.repository = repository or JobRepository()
        self.ai_provider = ai_provider or AIProvider()

    def process_upload(self, filename: str, raw_bytes: bytes) -> dict:
        logger.info(f"Upload received | file={filename}")

        extension = validators.validate_extension(filename)
        validators.validate_size(len(raw_bytes))
        if extension == ".pdf":
            validators.validate_not_corrupted_pdf(raw_bytes)

        raw_text = extract_text(raw_bytes, extension)
        logger.info(f"Extraction complete | file={filename} | chars={len(raw_text)}")

        cleaned = clean_text(raw_text)

        prompt = build_jd_prompt(cleaned)
        try:
            ai_result = self.ai_provider.complete_json(prompt)
        except AIErrorApp as e:
            logger.error(f"AI call failed | file={filename} | error={e.message}")
            raise

        ai_result["skills"] = normalize_ai_skills(ai_result.get("skills", []))
        logger.info(f"Normalization complete | file={filename} | skills={len(ai_result['skills'])}")

        extracted = ExtractedSkillList(
            source_type="jd",
            source_file=filename,
            company=None,
            role=ai_result.get("title"),
            title=ai_result.get("title"),
            experience=ai_result.get("experience"),
            education=ai_result.get("education"),
            skills=[Skill(**s) for s in ai_result["skills"]],
            responsibilities=ai_result.get("responsibilities", []),
            technologies=ai_result.get("technologies", []),
            soft_skills=ai_result.get("soft_skills", []),
            industry=ai_result.get("industry"),
        )

        record = self.repository.insert({
            "filename": filename,
            "extracted": extracted.model_dump(),
        })
        logger.info(f"Save complete | file={filename} | job_id={record['id']}")

        return record

    def get_job(self, job_id: str) -> dict | None:
        return self.repository.get(job_id)

    def list_jobs(self) -> list[dict]:
        return self.repository.list()

    def delete_job(self, job_id: str) -> bool:
        return self.repository.delete(job_id)
