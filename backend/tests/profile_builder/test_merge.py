"""Tests for deduplication and merging utilities."""

from __future__ import annotations

import pytest

from backend.modules.profile_builder.merge import (
    deduplicate_certifications,
    deduplicate_projects,
    deduplicate_skills,
    normalize_project_technologies,
    normalize_skills,
)
from backend.modules.profile_builder.schemas import (
    CertificationItem,
    ProjectItem,
    SkillItem,
)


class TestDeduplicateSkills:
    def test_no_duplicates(self):
        skills = [SkillItem(name="Python"), SkillItem(name="Java")]
        result = deduplicate_skills(skills)
        assert len(result) == 2

    def test_case_insensitive_dedup(self):
        skills = [
            SkillItem(name="Python"),
            SkillItem(name="python"),
            SkillItem(name="PYTHON"),
        ]
        result = deduplicate_skills(skills)
        assert len(result) == 1
        assert result[0].name == "Python"

    def test_whitespace_handling(self):
        skills = [
            SkillItem(name="Python"),
            SkillItem(name="  python  "),
        ]
        result = deduplicate_skills(skills)
        assert len(result) == 1

    def test_empty_list(self):
        assert deduplicate_skills([]) == []

    def test_preserves_first_occurrence(self):
        skills = [
            SkillItem(name="Python", category="Lang"),
            SkillItem(name="python", category="Tool"),
        ]
        result = deduplicate_skills(skills)
        assert result[0].category == "Lang"


class TestDeduplicateProjects:
    def test_no_duplicates(self):
        projects = [ProjectItem(name="A"), ProjectItem(name="B")]
        result = deduplicate_projects(projects)
        assert len(result) == 2

    def test_case_insensitive_dedup(self):
        projects = [
            ProjectItem(name="MyProject", technologies=["Python"]),
            ProjectItem(name="myproject", technologies=["Rust"]),
        ]
        result = deduplicate_projects(projects)
        assert len(result) == 1
        assert set(result[0].technologies) == {"Python", "Rust"}

    def test_merges_highlights(self):
        projects = [
            ProjectItem(name="P1", highlights=["H1"]),
            ProjectItem(name="p1", highlights=["H2"]),
        ]
        result = deduplicate_projects(projects)
        assert len(result) == 1
        assert set(result[0].highlights) == {"H1", "H2"}

    def test_empty_list(self):
        assert deduplicate_projects([]) == []


class TestDeduplicateCertifications:
    def test_no_duplicates(self):
        certs = [
            CertificationItem(name="AWS"),
            CertificationItem(name="GCP"),
        ]
        result = deduplicate_certifications(certs)
        assert len(result) == 2

    def test_case_insensitive_dedup(self):
        certs = [
            CertificationItem(name="AWS Solutions Architect"),
            CertificationItem(name="aws solutions architect"),
        ]
        result = deduplicate_certifications(certs)
        assert len(result) == 1

    def test_empty_list(self):
        assert deduplicate_certifications([]) == []


class TestNormalizeSkills:
    def test_title_case(self):
        skills = [SkillItem(name="python"), SkillItem(name="FASTAPI")]
        result = normalize_skills(skills)
        assert result[0].name == "Python"
        assert result[1].name == "FASTAPI"

    def test_preserves_short_words(self):
        skills = [SkillItem(name="go")]
        result = normalize_skills(skills)
        assert result[0].name == "GO"


class TestNormalizeProjectTechnologies:
    def test_lowercases_and_sorts(self):
        projects = [
            ProjectItem(name="P", technologies=["React", "python", "Go"])
        ]
        result = normalize_project_technologies(projects)
        assert result[0].technologies == ["go", "python", "react"]

    def test_removes_duplicates(self):
        projects = [
            ProjectItem(name="P", technologies=["Python", "python", "PYTHON"])
        ]
        result = normalize_project_technologies(projects)
        assert len(result[0].technologies) == 1
