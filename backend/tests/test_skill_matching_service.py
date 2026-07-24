"""
Skill Matching — Milestone 12 Unit Tests (service.py).

Covers apply_trust_signal (the verification-reconciliation gap closed in
this milestone) and the full orchestration entry points run_match /
run_what_if, exercised through the public request schemas exactly as
api.py would call them -- no HTTP layer involved here, that's covered
separately in test_skill_matching_api.py.
"""

import json
from datetime import date
from pathlib import Path

import pytest

from app.shared.exceptions import ValidationError
from modules.skill_matching.models import (
    Candidate,
    CandidateSkill,
    EvidenceDepth,
    EvidenceSourceType,
    SkillEvidence,
    TrustSignal,
)
from modules.skill_matching.schemas import SkillMatchRequest, WhatIfRequest
from modules.skill_matching.service import apply_trust_signal, run_match, run_what_if

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skill_matching"
AS_OF = date(2024, 12, 1)


def _load(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _candidate_with_skill(raw_text: str, canonical_skill_id: str | None) -> Candidate:
    evidence = [SkillEvidence(source_type=EvidenceSourceType.PROJECT, source_reference="ref", depth=EvidenceDepth.DESCRIBED)]
    skill = CandidateSkill(raw_text=raw_text, canonical_skill_id=canonical_skill_id, evidence=evidence)
    return Candidate(candidate_id="c1", skills=[skill])


# ─── apply_trust_signal ─────────────────────────────────────────────────

class TestApplyTrustSignal:
    def test_no_trust_signal_leaves_evidence_unchanged(self):
        candidate = _candidate_with_skill("Python", "python")
        result = apply_trust_signal(candidate, None)
        assert result.skills[0].evidence[0].verified is None

    def test_empty_verified_list_leaves_evidence_unchanged(self):
        candidate = _candidate_with_skill("Python", "python")
        trust_signal = TrustSignal(candidate_id="c1", verified_skill_ids=[])
        result = apply_trust_signal(candidate, trust_signal)
        assert result.skills[0].evidence[0].verified is None

    def test_verified_skill_by_canonical_id_gets_marked_verified(self):
        candidate = _candidate_with_skill("Python", "python")
        trust_signal = TrustSignal(candidate_id="c1", verified_skill_ids=["python"])
        result = apply_trust_signal(candidate, trust_signal)
        assert result.skills[0].evidence[0].verified is True

    def test_verified_skill_by_raw_text_when_unmapped(self):
        candidate = _candidate_with_skill("Some Obscure Tool", None)
        trust_signal = TrustSignal(candidate_id="c1", verified_skill_ids=["Some Obscure Tool"])
        result = apply_trust_signal(candidate, trust_signal)
        assert result.skills[0].evidence[0].verified is True

    def test_unlisted_skill_stays_none_not_false(self):
        # absence from verified_skill_ids must never be escalated to False
        candidate = _candidate_with_skill("Python", "python")
        trust_signal = TrustSignal(candidate_id="c1", verified_skill_ids=["fastapi"])
        result = apply_trust_signal(candidate, trust_signal)
        assert result.skills[0].evidence[0].verified is None

    def test_all_evidence_items_on_a_verified_skill_are_marked(self):
        evidence = [
            SkillEvidence(source_type=EvidenceSourceType.PROJECT, source_reference="a", depth=EvidenceDepth.DESCRIBED),
            SkillEvidence(source_type=EvidenceSourceType.EXPERIENCE, source_reference="b", depth=EvidenceDepth.CENTRAL),
        ]
        candidate = Candidate(
            candidate_id="c1",
            skills=[CandidateSkill(raw_text="Python", canonical_skill_id="python", evidence=evidence)],
        )
        trust_signal = TrustSignal(candidate_id="c1", verified_skill_ids=["python"])
        result = apply_trust_signal(candidate, trust_signal)
        assert all(e.verified is True for e in result.skills[0].evidence)

    def test_original_candidate_is_not_mutated(self):
        candidate = _candidate_with_skill("Python", "python")
        trust_signal = TrustSignal(candidate_id="c1", verified_skill_ids=["python"])
        apply_trust_signal(candidate, trust_signal)
        assert candidate.skills[0].evidence[0].verified is None


# ─── run_match ────────────────────────────────────────────────────────────

class TestRunMatch:
    def test_returns_a_complete_report(self):
        request = SkillMatchRequest(job=_load("job_fixture.json"), candidate=_load("candidate_fixture.json"))
        report = run_match(request, as_of=AS_OF)

        assert report.candidate_id == "cand-001"
        assert report.job_id == "job-101"
        assert len(report.matches) == len(report.match_confidences)
        assert report.explanation_source == "template"  # no AI provider configured in this test
        assert report.insights is not None

    def test_empty_job_raises_validation_error(self):
        request = SkillMatchRequest(job=_load("job_empty_fixture.json"), candidate=_load("candidate_fixture.json"))
        with pytest.raises(ValidationError):
            run_match(request, as_of=AS_OF)

    def test_insights_include_all_four_innovation_features(self):
        request = SkillMatchRequest(job=_load("job_fixture.json"), candidate=_load("candidate_fixture.json"))
        report = run_match(request, as_of=AS_OF)

        assert "weakest_matched_skill" in report.insights
        assert "candidate_bonus_skills" in report.insights
        assert "interview_questions" in report.insights
        assert "ats_keyword_match_rate" in report.insights
        assert "Machine Learning" in report.insights["candidate_bonus_skills"]

    def test_talent_check_verification_reaches_matched_skill_evidence(self):
        request = SkillMatchRequest(
            job=_load("job_fixture.json"),
            candidate=_load("candidate_fixture.json"),
            talent_check=_load("talent_check_fixture.json"),  # verifies python, fastapi
        )
        report = run_match(request, as_of=AS_OF)

        python_match = next(m for m in report.matches if m.requirement.raw_text == "Python")
        assert any(e.verified is True for skill in python_match.matched_candidate_skills for e in skill.evidence)

    def test_reproducible_with_a_fixed_as_of(self):
        request = SkillMatchRequest(job=_load("job_fixture.json"), candidate=_load("candidate_fixture.json"))
        first = run_match(request, as_of=AS_OF)
        second = run_match(request, as_of=AS_OF)
        assert first.score.overall_score == second.score.overall_score
        assert first.overall_confidence == second.overall_confidence
        assert first.recommendation.tier == second.recommendation.tier

    def test_sparse_candidate_still_produces_a_valid_report(self):
        request = SkillMatchRequest(job=_load("job_fixture.json"), candidate=_load("candidate_sparse_fixture.json"))
        report = run_match(request, as_of=AS_OF)
        assert report.score.overall_score == 0.0
        assert report.recommendation.tier.value == "low_match"


# ─── run_what_if ──────────────────────────────────────────────────────────

class TestRunWhatIf:
    def test_returns_a_result(self):
        request = WhatIfRequest(
            job=_load("job_fixture.json"), candidate=_load("candidate_sparse_fixture.json"),
            hypothetical_skill="Python",
        )
        result = run_what_if(request, as_of=AS_OF)
        assert result.hypothetical_skill_recognized is True
        assert result.score_delta > 0

    def test_empty_job_raises_validation_error(self):
        request = WhatIfRequest(
            job=_load("job_empty_fixture.json"), candidate=_load("candidate_fixture.json"),
            hypothetical_skill="Python",
        )
        with pytest.raises(ValidationError):
            run_what_if(request, as_of=AS_OF)
