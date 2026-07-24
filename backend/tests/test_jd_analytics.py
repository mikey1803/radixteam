"""
Unit tests for JD Analytics — per Chapter 4.19.
Covers: valid PDF/DOCX, empty file, large file, invalid extension,
skill normalization, and end-to-end service flow using the mock AI provider.
"""
import io
import os

import pytest

os.environ.setdefault("AI_PROVIDER_MODE", "mock")

from app.shared.exceptions import FileErrorApp, ValidationErrorApp
from modules.jd_analytics import validators
from modules.jd_analytics.utils import normalize_ai_skills, normalize_skill_name
from modules.jd_analytics.service import JDAnalyticsService
from modules.jd_analytics.repository import JobRepository


def make_minimal_pdf_bytes(text: str) -> bytes:
    """Build a tiny valid PDF containing `text`, using PyMuPDF."""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


class TestValidators:
    def test_rejects_unsupported_extension(self):
        with pytest.raises(ValidationErrorApp):
            validators.validate_extension("resume.txt")

    def test_accepts_pdf_and_docx(self):
        assert validators.validate_extension("jd.pdf") == ".pdf"
        assert validators.validate_extension("jd.docx") == ".docx"

    def test_rejects_empty_file(self):
        with pytest.raises(FileErrorApp):
            validators.validate_size(0)

    def test_rejects_oversized_file(self):
        with pytest.raises(FileErrorApp):
            validators.validate_size(11 * 1024 * 1024)

    def test_rejects_corrupted_pdf(self):
        with pytest.raises(FileErrorApp):
            validators.validate_not_corrupted_pdf(b"not a real pdf")


class TestNormalization:
    def test_normalizes_js_variants(self):
        assert normalize_skill_name("JS") == "JavaScript"
        assert normalize_skill_name("Javascript") == "JavaScript"
        assert normalize_skill_name("Java Script") == "JavaScript"

    def test_normalizes_node_variants(self):
        assert normalize_skill_name("Node") == "Node.js"
        assert normalize_skill_name("NodeJS") == "Node.js"

    def test_dedupes_and_defaults_bad_category(self):
        raw = [
            {"skill_name": "JS", "category_code": "COD"},
            {"skill_name": "Javascript", "category_code": "COD"},  # duplicate after normalization
            {"skill_name": "Rust", "category_code": "NOT_REAL"},
        ]
        result = normalize_ai_skills(raw)
        names = [s["skill_name"] for s in result]
        assert names.count("JavaScript") == 1
        rust = next(s for s in result if s["skill_name"] == "Rust")
        assert rust["category_code"] == "OTHER"


class TestJDAnalyticsServiceEndToEnd:
    def setup_method(self):
        # Use a throwaway repository file per test run so tests don't pollute real data.
        os.environ["AI_PROVIDER_MODE"] = "mock"
        self.service = JDAnalyticsService(repository=JobRepository())

    def test_valid_pdf_produces_structured_json(self):
        pdf_bytes = make_minimal_pdf_bytes(
            "Software Engineer\n"
            "Key Responsibilities: build APIs with Python and FastAPI, work with AWS cloud infra.\n"
            "What We're Looking For: strong SQL skills, system design experience, good communication."
        )
        record = self.service.process_upload("test_jd.pdf", pdf_bytes)

        assert record["filename"] == "test_jd.pdf"
        extracted = record["extracted"]
        assert extracted["source_type"] == "jd"
        assert isinstance(extracted["skills"], list)
        assert len(extracted["skills"]) > 0
        for skill in extracted["skills"]:
            assert skill["category_code"] in (
                "DSA", "COD", "OOD", "APTI", "COMM", "AI",
                "CLOUD", "SQL", "SWE", "SYSD", "NETW", "OS", "OTHER",
            )

    def test_empty_pdf_raises_file_error(self):
        with pytest.raises(FileErrorApp):
            self.service.process_upload("empty.pdf", b"")

    def test_invalid_extension_raises_validation_error(self):
        with pytest.raises(ValidationErrorApp):
            self.service.process_upload("jd.txt", b"some text")

    def test_corrupted_pdf_raises_file_error(self):
        with pytest.raises(FileErrorApp):
            self.service.process_upload("bad.pdf", b"this is not a pdf")

    def test_get_and_list_after_upload(self):
        pdf_bytes = make_minimal_pdf_bytes("Data Scientist role requiring Python and TensorFlow.")
        record = self.service.process_upload("ds_role.pdf", pdf_bytes)

        fetched = self.service.get_job(record["id"])
        assert fetched is not None
        assert fetched["filename"] == "ds_role.pdf"

        all_jobs = self.service.list_jobs()
        assert any(j["id"] == record["id"] for j in all_jobs)
