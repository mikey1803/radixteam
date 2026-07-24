"""
Skill Matching — FastAPI Router (API Layer).

HTTP concerns only — all business logic lives in service.py. Every
response returns through the shared APIResponse envelope
(app.shared.schemas), the contract every module uses.

Endpoints:
    POST /skill-match          — score one candidate against one job
    POST /skill-match/what-if  — simulate adding one hypothetical skill

Validation failures (e.g. an empty JD) raise the shared ValidationError
from service.py and are deliberately NOT caught here — they propagate to
main.py's global exception handler, the same pattern every module in
this codebase uses, so error responses stay consistent platform-wide.
"""

from typing import Optional

from fastapi import APIRouter, Depends

from app.api.dependencies import get_ai_provider
from app.core.ai_provider import AIProvider
from app.shared.schemas import APIResponse

from . import service
from .aggregator import MatchReport
from .gap_analysis import Gap
from .innovation.whatif_simulator import WhatIfResult
from .schemas import (
    GapOut,
    MatchedSkillOut,
    MatchInsightsOut,
    RecommendationOut,
    SkillEvidenceOut,
    SkillMatchRequest,
    SkillMatchResponse,
    WhatIfRequest,
    WhatIfResponseOut,
)

router = APIRouter(prefix="/skill-match", tags=["Skill Matching"])


def _gap_reason(gap: Gap) -> str:
    if not gap.matched_via:
        return f"{gap.severity.value.replace('_', ' ')}: no supporting evidence found."
    related = gap.matched_via[0].raw_text
    return f"{gap.severity.value.replace('_', ' ')}: related evidence via {related}."


def _build_response(report: MatchReport) -> SkillMatchResponse:
    """Map the internal MatchReport onto the public SkillMatchResponse contract."""
    matched_skills = [
        MatchedSkillOut(
            skill=match.requirement.raw_text,
            match_type=match.match_type.value,
            confidence=confidence,
            evidence=[
                SkillEvidenceOut(
                    source_type=evidence.source_type.value,
                    source_reference=evidence.source_reference,
                    depth=evidence.depth.value,
                    verified=evidence.verified,
                )
                for skill in match.matched_candidate_skills
                for evidence in skill.evidence
            ],
        )
        for match, confidence in zip(report.matches, report.match_confidences)
        if match.match_type.value != "none"
    ]

    gaps = [
        GapOut(skill=gap.requirement.raw_text, severity=gap.severity.value, reason=_gap_reason(gap))
        for gap in report.gaps
    ]

    recommendation = RecommendationOut(
        tier=report.recommendation.tier.value,
        confidence_label=report.recommendation.confidence_label.value,
    )

    insights = MatchInsightsOut(**report.insights) if report.insights else None

    return SkillMatchResponse(
        candidate_id=report.candidate_id,
        job_id=report.job_id,
        overall_score=report.score.overall_score,
        overall_confidence=report.overall_confidence,
        matched_skills=matched_skills,
        gaps=gaps,
        recommendation=recommendation,
        explanation=report.explanation,
        explanation_source=report.explanation_source,
        insights=insights,
    )


def _build_whatif_response(result: WhatIfResult) -> WhatIfResponseOut:
    return WhatIfResponseOut(
        hypothetical_skill=result.hypothetical_skill,
        hypothetical_skill_recognized=result.hypothetical_skill_recognized,
        baseline_score=result.baseline.overall_score,
        projected_score=result.projected.overall_score,
        score_delta=result.score_delta,
        baseline_confidence=result.baseline.overall_confidence,
        projected_confidence=result.projected.overall_confidence,
        confidence_delta=result.confidence_delta,
        critical_gaps_resolved=result.critical_gaps_resolved,
    )


@router.post("", response_model=APIResponse)
def match_candidate_to_job(
    request: SkillMatchRequest,
    ai_provider: Optional[AIProvider] = Depends(get_ai_provider),
) -> APIResponse:
    """Score one candidate against one job and return the full deterministic + AI result."""
    report = service.run_match(request, ai_provider=ai_provider)
    response = _build_response(report)
    return APIResponse(success=True, message="Match computed.", data=response.model_dump())


@router.post("/what-if", response_model=APIResponse)
def what_if(request: WhatIfRequest) -> APIResponse:
    """Simulate the effect of the candidate having one additional hypothetical skill."""
    result = service.run_what_if(request)
    response = _build_whatif_response(result)
    return APIResponse(success=True, message="What-if simulation computed.", data=response.model_dump())
