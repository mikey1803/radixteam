"""Tests for LLM-based and rule-based extraction."""

from __future__ import annotations

import pytest

from backend.modules.resume_parser.extractor import _rule_based_extract


class TestRuleBasedExtract:
    def test_extracts_email(self, sample_resume_text):
        result = _rule_based_extract(sample_resume_text)
        assert result["personal_info"]["email"] == "jane@example.com"

    def test_extracts_name(self, sample_resume_text):
        result = _rule_based_extract(sample_resume_text)
        assert result["personal_info"]["first_name"] == "Jane"
        assert result["personal_info"]["last_name"] == "Doe"

    def test_extracts_phone(self, sample_resume_text):
        result = _rule_based_extract(sample_resume_text)
        assert result["personal_info"]["phone"] is not None

    def test_extracts_location(self, sample_resume_text):
        result = _rule_based_extract(sample_resume_text)
        assert result["personal_info"]["location"] is not None

    def test_extracts_skills(self, sample_resume_text):
        result = _rule_based_extract(sample_resume_text)
        assert len(result["skills"]) > 0
        skill_names = [s["name"] for s in result["skills"]]
        assert "Python" in skill_names

    def test_extracts_links(self, sample_resume_text):
        result = _rule_based_extract(sample_resume_text)
        assert len(result["links"]) > 0
        urls = [lnk["url"] for lnk in result["links"]]
        assert any("github.com" in u for u in urls)

    def test_extracts_education(self, sample_resume_text):
        result = _rule_based_extract(sample_resume_text)
        assert len(result["education"]) > 0

    def test_empty_text_returns_defaults(self):
        result = _rule_based_extract("")
        assert result["personal_info"]["email"] == "unknown@unknown.com"
        assert result["personal_info"]["first_name"] == "Unknown"

    def test_structure_matches_expected(self, sample_resume_text):
        result = _rule_based_extract(sample_resume_text)
        assert "personal_info" in result
        assert "summary" in result
        assert "education" in result
        assert "experience" in result
        assert "skills" in result
        assert "projects" in result
        assert "certifications" in result
        assert "links" in result
