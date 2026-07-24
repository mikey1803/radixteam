"""
Skill Matching — Upstream Adapters.

Translates raw upstream payloads (JD Analytics, Resume Parser / Profile
Builder, Talent Check) into this module's internal models (models.py).
This is the module's anti-corruption boundary: every assumption about an
upstream module's field names lives here and nowhere else, so a schema
change upstream only ever requires touching this one file.

Candidate contract is grounded in Profile Builder's real ProfileResponse
schema: `skills` is a flat list[str] with no per-skill linkage, but
`experience` and `projects` entries each carry a `technologies: list[str]`
field. This adapter reconstructs skill-to-evidence links by cross-
referencing each skill against those technology lists (and certification
names) rather than assuming a direct link the upstream schema doesn't
provide. A skill with no cross-referenced evidence anywhere still gets an
entry — weighted as the weakest evidence tier — instead of being dropped.

JD Analytics and Talent Check have no committed schema anywhere in this
repo as of this milestone. The shapes assumed below are explicitly
documented placeholders, not confirmed contracts — update only this file
once the real shapes land.
"""

from datetime import date, datetime
from typing import Any, Optional

from .models import (
    Candidate,
    CandidateSkill,
    EvidenceDepth,
    EvidenceSourceType,
    Job,
    JobSkillRequirement,
    MatchContext,
    RequirementLevel,
    SkillEvidence,
    TrustSignal,
)


def _norm(text: str) -> str:
    """Lowercase + strip, for loose skill-name comparison during evidence linking."""
    return text.strip().lower()


def _parse_date(value: Any) -> Optional[date]:
    """Best-effort ISO date parse; malformed or missing values degrade to None, never raise."""
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None


def _collect_technology_evidence(
    skill_raw: str,
    entries: list[dict[str, Any]],
    source_type: EvidenceSourceType,
    reference_fields: tuple[str, ...],
) -> list[SkillEvidence]:
    """Scan experience/project-shaped dicts for a technologies list mentioning skill_raw."""
    evidence: list[SkillEvidence] = []
    target = _norm(skill_raw)

    for entry in entries:
        technologies = entry.get("technologies") or []
        if not any(_norm(str(t)) == target for t in technologies):
            continue

        reference_parts = [str(entry[f]) for f in reference_fields if entry.get(f)]
        reference = " at ".join(reference_parts) if reference_parts else "unspecified entry"

        evidence.append(
            SkillEvidence(
                source_type=source_type,
                source_reference=reference,
                depth=EvidenceDepth.DESCRIBED,
                start_date=_parse_date(entry.get("start_date")),
                end_date=_parse_date(entry.get("end_date")),
            )
        )
    return evidence


def _collect_certification_evidence(
    skill_raw: str, certifications: list[dict[str, Any]]
) -> list[SkillEvidence]:
    """A skill matching (part of) a certification name is treated as strong, central evidence."""
    target = _norm(skill_raw)
    evidence: list[SkillEvidence] = []

    for cert in certifications:
        name = str(cert.get("name", ""))
        if target and target in _norm(name):
            evidence.append(
                SkillEvidence(
                    source_type=EvidenceSourceType.CERTIFICATION,
                    source_reference=name or "certification",
                    depth=EvidenceDepth.CENTRAL,
                    start_date=_parse_date(cert.get("date")),
                    end_date=_parse_date(cert.get("date")),
                )
            )
    return evidence


# ─── Candidate adapter ───────────────────────────────────────────────────

def adapt_candidate(payload: dict[str, Any]) -> Candidate:
    """
    Build an internal Candidate from a Profile Builder-shaped payload.

    Falls back gracefully on missing optional fields; a skill with no
    cross-referenced evidence anywhere still produces an entry, evidenced
    only as a bare profile mention, rather than being dropped.
    """
    candidate_id = str(payload.get("id") or payload.get("candidate_id") or "unknown")
    raw_skills: list[str] = payload.get("skills") or []
    experience: list[dict[str, Any]] = payload.get("experience") or []
    projects: list[dict[str, Any]] = payload.get("projects") or []
    certifications: list[dict[str, Any]] = payload.get("certifications") or []

    skills: list[CandidateSkill] = []
    for raw in raw_skills:
        evidence = (
            _collect_technology_evidence(raw, experience, EvidenceSourceType.EXPERIENCE, ("title", "company"))
            + _collect_technology_evidence(raw, projects, EvidenceSourceType.PROJECT, ("name",))
            + _collect_certification_evidence(raw, certifications)
        )

        if not evidence:
            evidence.append(
                SkillEvidence(
                    source_type=EvidenceSourceType.PROFILE_SUMMARY,
                    source_reference="listed in candidate skills",
                    depth=EvidenceDepth.MENTIONED,
                )
            )

        skills.append(CandidateSkill(raw_text=raw, evidence=evidence))

    return Candidate(
        candidate_id=candidate_id,
        name=payload.get("name"),
        skills=skills,
        completeness_score=payload.get("completeness_score"),
        profile_status=payload.get("profile_status"),
    )


# ─── Job adapter ─────────────────────────────────────────────────────────

def adapt_job(payload: dict[str, Any]) -> Job:
    """
    Build an internal Job from a JD Analytics-shaped payload.

    ASSUMPTION (unverified upstream — no committed JD Analytics schema
    exists yet): top-level `required_skills` and `preferred_skills` lists,
    each either plain strings or {"name": ...} dicts. Update this function
    — and only this function — once the real schema is confirmed.
    """
    job_id = str(payload.get("id") or payload.get("job_id") or "unknown")

    def _extract(items: list[Any]) -> list[str]:
        out: list[str] = []
        for item in items:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict) and item.get("name"):
                out.append(str(item["name"]))
        return out

    required = _extract(payload.get("required_skills") or [])
    preferred = _extract(payload.get("preferred_skills") or [])

    skills = [
        JobSkillRequirement(raw_text=s, level=RequirementLevel.REQUIRED) for s in required
    ] + [
        JobSkillRequirement(raw_text=s, level=RequirementLevel.PREFERRED) for s in preferred
    ]

    return Job(
        job_id=job_id,
        title=payload.get("title"),
        seniority=payload.get("seniority"),
        skills=skills,
    )


# ─── Talent Check adapter ────────────────────────────────────────────────

def adapt_trust_signal(payload: Optional[dict[str, Any]], candidate_id: str) -> Optional[TrustSignal]:
    """
    Build an internal TrustSignal from a Talent Check payload, if provided.

    Talent Check is optional input throughout the pipeline; returning None
    here (rather than a zeroed-out TrustSignal) is what lets the confidence
    engine (Milestone 5) distinguish "not verified" from "verification
    wasn't attempted at all".
    """
    if not payload:
        return None

    return TrustSignal(
        candidate_id=candidate_id,
        overall_trust_score=payload.get("overall_trust_score"),
        verified_skill_ids=payload.get("verified_skill_ids") or [],
    )


# ─── Entry point ──────────────────────────────────────────────────────────

def adapt_match_context(
    job_payload: dict[str, Any],
    candidate_payload: dict[str, Any],
    talent_check_payload: Optional[dict[str, Any]] = None,
) -> MatchContext:
    """Adapt all three upstream payloads into one MatchContext for the pipeline."""
    candidate = adapt_candidate(candidate_payload)
    job = adapt_job(job_payload)
    trust_signal = adapt_trust_signal(talent_check_payload, candidate.candidate_id)
    return MatchContext(candidate=candidate, job=job, trust_signal=trust_signal)
