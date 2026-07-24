"""
Profile Builder — Duplicate Resolution & Section Merging.

Handles deduplication of skills, projects, certifications, and education.
This module does NOT parse resumes — it only works with structured data.

Key rules:
    - Skills: case-insensitive dedup, keep title-cased version
    - Projects: fuzzy name matching (normalized comparison)
    - Certifications: name-based dedup
    - Education: remove exact duplicates
"""

import re

from modules.profile_builder.schemas import (
    ProfileCreateRequest,
    EducationItem,
    ExperienceItem,
    ProjectItem,
    CertificationItem,
)
from modules.profile_builder.utils import normalize_location, normalize_degree


def deduplicate_skills(skills: list[str]) -> list[str]:
    """
    Deduplicate skills using case-insensitive comparison.

    Example:
        [Python, python, PYTHON] → [Python]
        [React, react, React.js] → [React, React.js]

    Keeps the first occurrence's casing, then title-cases the result.
    """
    if not skills:
        return []

    seen: dict[str, str] = {}
    for skill in skills:
        if not skill or not skill.strip():
            continue
        key = skill.strip().lower()
        if key not in seen:
            # Store the title-cased version
            seen[key] = skill.strip().title()

    return list(seen.values())


def _normalize_name(name: str) -> str:
    """
    Normalize a name for fuzzy comparison.

    Removes spaces, hyphens, underscores; lowercases everything.
    Example: "Deploy Sense" → "deploysense", "DeploySense" → "deploysense"
    """
    if not name:
        return ""
    return re.sub(r"[\s\-_]+", "", name.strip().lower())


def deduplicate_projects(projects: list[ProjectItem]) -> list[ProjectItem]:
    """
    Deduplicate projects using fuzzy name matching.

    Example:
        [DeploySense, Deploy Sense] → keeps only the first one.

    Merges technologies from duplicates into the kept project.
    """
    if not projects:
        return []

    seen: dict[str, ProjectItem] = {}
    for project in projects:
        key = _normalize_name(project.name)
        if key not in seen:
            seen[key] = project
        else:
            # Merge technologies from duplicate into the existing one
            existing = seen[key]
            merged_techs = list(existing.technologies)
            for tech in project.technologies:
                if tech.strip().lower() not in [t.lower() for t in merged_techs]:
                    merged_techs.append(tech)
            seen[key] = ProjectItem(
                name=existing.name,
                description=existing.description or project.description,
                technologies=merged_techs,
                url=existing.url or project.url,
            )

    return list(seen.values())


def deduplicate_certifications(
    certifications: list[CertificationItem],
) -> list[CertificationItem]:
    """
    Deduplicate certifications by normalized name.

    Keeps the first occurrence. Fills in missing fields from duplicates.
    """
    if not certifications:
        return []

    seen: dict[str, CertificationItem] = {}
    for cert in certifications:
        key = _normalize_name(cert.name)
        if key not in seen:
            seen[key] = cert
        else:
            existing = seen[key]
            seen[key] = CertificationItem(
                name=existing.name,
                issuer=existing.issuer or cert.issuer,
                date=existing.date or cert.date,
                url=existing.url or cert.url,
            )

    return list(seen.values())


def merge_education(education: list[EducationItem]) -> list[EducationItem]:
    """
    Remove exact duplicate education entries.

    Deduplicates by (institution + degree + field_of_study) normalized key.
    Normalizes degree names in the process.
    """
    if not education:
        return []

    seen: dict[str, EducationItem] = {}
    for edu in education:
        # Normalize the degree
        normalized_degree = normalize_degree(edu.degree)
        key = _normalize_name(
            f"{edu.institution}_{normalized_degree}_{edu.field_of_study or ''}"
        )
        if key not in seen:
            seen[key] = EducationItem(
                institution=edu.institution,
                degree=normalized_degree,
                field_of_study=edu.field_of_study,
                start_date=edu.start_date,
                end_date=edu.end_date,
                gpa=edu.gpa,
            )

    return list(seen.values())


def merge_experience(experience: list[ExperienceItem]) -> list[ExperienceItem]:
    """
    Remove duplicate experience entries and normalize locations.

    Deduplicates by (company + title) normalized key.
    """
    if not experience:
        return []

    seen: dict[str, ExperienceItem] = {}
    for exp in experience:
        key = _normalize_name(f"{exp.company}_{exp.title}")
        if key not in seen:
            seen[key] = ExperienceItem(
                company=exp.company,
                title=exp.title,
                location=normalize_location(exp.location) if exp.location else None,
                start_date=exp.start_date,
                end_date=exp.end_date,
                description=exp.description,
                technologies=exp.technologies,
            )

    return list(seen.values())


def merge_profile_sections(data: ProfileCreateRequest) -> dict:
    """
    Orchestrate all deduplication and normalization on profile data.

    This is the main entry point for the merge module.
    Performs:
        1. Deduplicate skills
        2. Deduplicate projects
        3. Deduplicate certifications
        4. Merge education (with degree normalization)
        5. Merge experience (with location normalization)
        6. Normalize top-level location

    Returns a dict ready for profile creation.
    """
    return {
        "name": data.name.strip(),
        "email": data.email.strip().lower(),
        "phone": data.phone.strip() if data.phone else None,
        "location": normalize_location(data.location) if data.location else None,
        "summary": data.summary,
        "skills": deduplicate_skills(data.skills),
        "education": [
            edu.model_dump() for edu in merge_education(data.education)
        ],
        "experience": [
            exp.model_dump() for exp in merge_experience(data.experience)
        ],
        "projects": [
            proj.model_dump() for proj in deduplicate_projects(data.projects)
        ],
        "certifications": [
            cert.model_dump()
            for cert in deduplicate_certifications(data.certifications)
        ],
        "links": data.links.model_dump() if data.links else {},
        "resume_version": data.metadata.resume_version if data.metadata else None,
        "parser_version": data.metadata.parser_version if data.metadata else None,
        "ai_model": data.metadata.ai_model if data.metadata else None,
    }
