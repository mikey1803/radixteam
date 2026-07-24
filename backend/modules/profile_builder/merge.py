"""Deduplication and merging utilities for profile sections."""

from __future__ import annotations

from shared.logging import get_logger

from backend.modules.profile_builder.schemas import (
    CertificationItem,
    ProjectItem,
    SkillItem,
)

logger = get_logger(__name__)


def deduplicate_skills(skills: list[SkillItem]) -> list[SkillItem]:
    """Remove duplicate skills by case-insensitive name comparison."""
    seen: dict[str, SkillItem] = {}
    for skill in skills:
        key = skill.name.strip().lower()
        if key not in seen:
            seen[key] = skill
        else:
            logger.debug("Duplicate skill removed", name=skill.name)
    return list(seen.values())


def deduplicate_projects(projects: list[ProjectItem]) -> list[ProjectItem]:
    """Remove duplicate projects by case-insensitive name comparison."""
    seen: dict[str, ProjectItem] = {}
    for project in projects:
        key = project.name.strip().lower()
        if key not in seen:
            seen[key] = project
        else:
            existing = seen[key]
            merged = _merge_project_duplicates(existing, project)
            seen[key] = merged
    return list(seen.values())


def deduplicate_certifications(
    certs: list[CertificationItem],
) -> list[CertificationItem]:
    """Remove duplicate certifications by case-insensitive name."""
    seen: dict[str, CertificationItem] = {}
    for cert in certs:
        key = cert.name.strip().lower()
        if key not in seen:
            seen[key] = cert
        else:
            logger.debug("Duplicate certification removed", name=cert.name)
    return list(seen.values())


def normalize_skills(skills: list[SkillItem]) -> list[SkillItem]:
    """Normalize skill names to title case."""
    normalized: list[SkillItem] = []
    for skill in skills:
        normalized.append(
            skill.model_copy(update={"name": _title_case(skill.name)})
        )
    return normalized


def normalize_project_technologies(
    projects: list[ProjectItem],
) -> list[ProjectItem]:
    """Normalize technology names inside each project."""
    result: list[ProjectItem] = []
    for project in projects:
        techs = sorted({t.strip().lower() for t in project.technologies})
        result.append(project.model_copy(update={"technologies": techs}))
    return result


def _merge_project_duplicates(a: ProjectItem, b: ProjectItem) -> ProjectItem:
    """Merge two project entries that share the same name."""
    technologies = list({*a.technologies, *b.technologies})
    highlights = list({*a.highlights, *b.highlights})
    description = b.description or a.description
    url = b.url or a.url
    return ProjectItem(
        name=a.name,
        description=description,
        url=url,
        technologies=technologies,
        highlights=highlights,
    )


def _title_case(value: str) -> str:
    """Smart title-casing that preserves acronyms (<=2 chars) and ALL-CAPS."""
    words = value.strip().split()
    result: list[str] = []
    for word in words:
        if len(word) <= 2:
            result.append(word.upper())
        elif word.isupper():
            result.append(word)
        else:
            result.append(word.capitalize())
    return " ".join(result) if result else value
