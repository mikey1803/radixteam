"""
Skill Matching — Service Layer.

Orchestration only: the fixed pipeline sequence adapters -> validation ->
normalization -> trust-signal reconciliation -> matching -> scoring ->
confidence -> gap analysis -> recommendation -> reasoning -> innovation
layer -> aggregation. This is the only file api.py calls, and the only
file that decides how a live request invokes the pipeline — Milestone 9's
Tier 2 semantic-assist discovery was deliberately left unwired from
matching.py for exactly this reason; that orchestration decision belongs
here, not bolted onto the deterministic core.

No business logic lives here — every rule, weight, and threshold that
matters already lives in the stage it belongs to. This file only
sequences calls and translates between the public request contract
(schemas.py) and the internal pipeline.

A real gap closed here, not before: TrustSignal.verified_skill_ids
(adapted since Milestone 1) was never actually reconciled against
candidate evidence anywhere in the pipeline — every SkillEvidence.verified
stayed at its default (None) regardless of what Talent Check reported.
apply_trust_signal() below closes that. It only ever moves verified from
None to True (never to False): verified_skill_ids is a positive-only
signal (things Talent Check confirmed), so absence from that list is
correctly left as "no signal," never escalated to "confirmed false" —
consistent with confidence.py's own "absence of verification is not
evidence of dishonesty" principle. trust_signal.overall_trust_score (a
coarser, non-per-skill alternative) is intentionally NOT applied anywhere
— how a single overall score should modulate confidence is a real
modeling decision this milestone doesn't invent; a documented gap, not
an oversight.
"""

from datetime import date, datetime, timezone
from typing import Optional

from app.core.ai_provider import AIProvider

from .adapters import adapt_match_context
from .aggregator import MatchReport, assemble_match_report
from .confidence import overall_confidence, requirement_confidence
from .gap_analysis import analyze_gaps
from .innovation.ats_alignment import compute_ats_alignment
from .innovation.candidate_insights import compute_candidate_insights
from .innovation.confidence_meter import compute_confidence_meter
from .innovation.interview_intelligence import generate_interview_questions
from .innovation.whatif_simulator import WhatIfResult, simulate_added_skill
from .matching import match_job
from .models import Candidate, CandidateSkill, TrustSignal
from .normalization import normalize_candidate, normalize_job
from .reasoning import generate_explanation
from .recommendation import recommend
from .schemas import SkillMatchRequest, WhatIfRequest
from .scoring import score_match
from .validators import validate_match_context


def _resolve_as_of(as_of: Optional[date]) -> date:
    return as_of or datetime.now(timezone.utc).date()


def apply_trust_signal(candidate: Candidate, trust_signal: Optional[TrustSignal]) -> Candidate:
    """Reconcile Talent Check's per-skill verification against the candidate's evidence."""
    if trust_signal is None or not trust_signal.verified_skill_ids:
        return candidate

    verified_set = {v.lower() for v in trust_signal.verified_skill_ids}

    def _maybe_verify(skill: CandidateSkill) -> CandidateSkill:
        is_verified = (
            skill.canonical_skill_id is not None and skill.canonical_skill_id.lower() in verified_set
        ) or skill.raw_text.lower() in verified_set

        if not is_verified:
            return skill

        updated_evidence = [evidence.model_copy(update={"verified": True}) for evidence in skill.evidence]
        return skill.model_copy(update={"evidence": updated_evidence})

    return candidate.model_copy(update={"skills": [_maybe_verify(s) for s in candidate.skills]})


def run_match(
    request: SkillMatchRequest,
    ai_provider: Optional[AIProvider] = None,
    as_of: Optional[date] = None,
) -> MatchReport:
    """
    Run the full deterministic + AI-reasoning + innovation-layer pipeline
    for one match request and return the assembled internal report.

    `as_of` defaults to the current UTC date but is always an explicit,
    overridable parameter, never a hidden call inside a pipeline stage —
    the only place "now" is resolved is here, once, at the request
    boundary, which is what keeps every downstream function's
    reproducibility guarantee real.
    """
    resolved_as_of = _resolve_as_of(as_of)

    context = adapt_match_context(request.job, request.candidate, request.talent_check)
    validate_match_context(context)

    candidate = apply_trust_signal(context.candidate, context.trust_signal)
    candidate = normalize_candidate(candidate)
    job = normalize_job(context.job)

    matches = match_job(job, candidate)
    match_confidences = [requirement_confidence(match, resolved_as_of) for match in matches]
    score = score_match(matches, resolved_as_of)
    confidence = overall_confidence(matches, candidate, resolved_as_of)
    gaps = analyze_gaps(matches, resolved_as_of)
    recommendation = recommend(score, confidence, gaps)
    explanation = generate_explanation(ai_provider, matches, score, gaps, recommendation, resolved_as_of)

    confidence_meter = compute_confidence_meter(matches, recommendation, resolved_as_of)
    candidate_insights = compute_candidate_insights(candidate, matches)
    interview_questions = generate_interview_questions(matches, gaps, resolved_as_of)
    ats_alignment = compute_ats_alignment(candidate, job)

    insights = {
        "weakest_matched_skill": (
            confidence_meter.weakest_requirement.skill if confidence_meter.weakest_requirement else None
        ),
        "candidate_bonus_skills": [b.skill for b in candidate_insights.bonus_skills],
        "interview_questions": [q.model_dump() for q in interview_questions],
        "ats_keyword_match_rate": ats_alignment.keyword_match_rate,
    }

    return assemble_match_report(
        candidate_id=candidate.candidate_id,
        job_id=job.job_id,
        matches=matches,
        match_confidences=match_confidences,
        score=score,
        confidence=confidence,
        gaps=gaps,
        recommendation=recommendation,
        explanation=explanation,
        insights=insights,
    )


def run_what_if(request: WhatIfRequest, as_of: Optional[date] = None) -> WhatIfResult:
    """Run the deterministic pipeline twice (baseline vs. hypothetical) and diff the result."""
    resolved_as_of = _resolve_as_of(as_of)

    context = adapt_match_context(request.job, request.candidate)
    validate_match_context(context)

    candidate = normalize_candidate(context.candidate)
    job = normalize_job(context.job)

    return simulate_added_skill(candidate, job, request.hypothetical_skill, resolved_as_of)
