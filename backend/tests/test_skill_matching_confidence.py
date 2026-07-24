"""
Skill Matching — Milestone 5 Unit Tests (confidence.py).

Covers the Skill / Requirement / Overall confidence aggregation on top of
Milestone 4's matching output, plus a full-fixture integration pass
through adapt -> normalize -> match -> confidence.
"""

import json
from datetime import date
from pathlib import Path

from modules.skill_matching.adapters import adapt_candidate, adapt_job
from modules.skill_matching.confidence import (
    overall_confidence,
    requirement_confidence,
    skill_confidence,
)
from modules.skill_matching.matching import MatchType, SkillMatch, match_job
from modules.skill_matching.models import (
    Candidate,
    CandidateSkill,
    EvidenceDepth,
    EvidenceSourceType,
    Job,
    JobSkillRequirement,
    RequirementLevel,
    SkillCategory,
    SkillEvidence,
)
from modules.skill_matching.normalization import normalize_candidate, normalize_job

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skill_matching"
AS_OF = date(2024, 12, 1)


def _load(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _skill(*evidence: SkillEvidence) -> CandidateSkill:
    return CandidateSkill(raw_text="x", canonical_skill_id="x", evidence=list(evidence))


def _evidence(**overrides) -> SkillEvidence:
    defaults = dict(
        source_type=EvidenceSourceType.PROJECT,
        source_reference="ref",
        depth=EvidenceDepth.DESCRIBED,
    )
    defaults.update(overrides)
    return SkillEvidence(**defaults)


# ─── skill_confidence ─────────────────────────────────────────────────────

class TestSkillConfidence:
    def test_no_evidence_is_zero(self):
        assert skill_confidence([_skill()], AS_OF) == 0.0

    def test_single_item_matches_evidence_item_weight(self):
        from modules.skill_matching.evidence import evidence_item_weight

        ev = _evidence(verified=None)
        assert skill_confidence([_skill(ev)], AS_OF) == evidence_item_weight(ev, AS_OF)

    def test_multiple_corroborating_sources_rank_above_a_single_weak_one(self):
        weak_only = skill_confidence([_skill(_evidence(source_type=EvidenceSourceType.PROFILE_SUMMARY))], AS_OF)
        corroborated = skill_confidence(
            [_skill(
                _evidence(source_type=EvidenceSourceType.PROFILE_SUMMARY),
                _evidence(source_type=EvidenceSourceType.PROJECT),
            )],
            AS_OF,
        )
        assert corroborated > weak_only

    def test_diminishing_returns_never_exceeds_one(self):
        many_strong_items = [
            _evidence(
                source_type=EvidenceSourceType.EXPERIENCE,
                depth=EvidenceDepth.CENTRAL,
                verified=True,
            )
            for _ in range(10)
        ]
        assert skill_confidence([_skill(*many_strong_items)], AS_OF) <= 1.0

    def test_conflicting_verification_reduces_confidence_vs_no_conflict(self):
        no_conflict = skill_confidence(
            [_skill(
                _evidence(source_type=EvidenceSourceType.EXPERIENCE, verified=True),
                _evidence(source_type=EvidenceSourceType.PROJECT, verified=True),
            )],
            AS_OF,
        )
        conflicting = skill_confidence(
            [_skill(
                _evidence(source_type=EvidenceSourceType.EXPERIENCE, verified=True),
                _evidence(source_type=EvidenceSourceType.PROJECT, verified=False),
            )],
            AS_OF,
        )
        assert conflicting < no_conflict


# ─── requirement_confidence ────────────────────────────────────────────────

class TestRequirementConfidence:
    def _match(self, match_type: MatchType, skills: list[CandidateSkill]) -> SkillMatch:
        return SkillMatch(
            requirement=JobSkillRequirement(raw_text="req", canonical_skill_id="req"),
            match_type=match_type,
            matched_candidate_skills=skills,
        )

    def test_none_match_is_always_zero(self):
        assert requirement_confidence(self._match(MatchType.NONE, []), AS_OF) == 0.0

    def test_ceiling_orders_exact_above_transferable_above_adjacent(self):
        skills = [_skill(_evidence(source_type=EvidenceSourceType.EXPERIENCE, depth=EvidenceDepth.CENTRAL))]
        exact = requirement_confidence(self._match(MatchType.EXACT, skills), AS_OF)
        transferable = requirement_confidence(self._match(MatchType.TRANSFERABLE, skills), AS_OF)
        adjacent = requirement_confidence(self._match(MatchType.ADJACENT, skills), AS_OF)

        assert exact > transferable > adjacent > 0


# ─── overall_confidence ────────────────────────────────────────────────────

class TestOverallConfidence:
    def _required_match(self, match_type: MatchType, skills: list[CandidateSkill]) -> SkillMatch:
        req = JobSkillRequirement(
            raw_text="req", canonical_skill_id="req",
            category=SkillCategory.CORE_TECHNICAL, level=RequirementLevel.REQUIRED,
        )
        return SkillMatch(requirement=req, match_type=match_type, matched_candidate_skills=skills)

    def test_empty_matches_is_zero(self):
        candidate = Candidate(candidate_id="c1")
        assert overall_confidence([], candidate, AS_OF) == 0.0

    def test_sparse_profile_produces_low_confidence_without_crashing(self):
        candidate = Candidate(candidate_id="c1", completeness_score=0.1)
        matches = [self._required_match(MatchType.NONE, [])]
        result = overall_confidence(matches, candidate, AS_OF)
        assert result == 0.0

    def test_weakest_critical_requirement_drags_score_down_sharply(self):
        strong_skill = [_skill(_evidence(
            source_type=EvidenceSourceType.EXPERIENCE, depth=EvidenceDepth.CENTRAL, verified=True,
        ))]
        matches = [
            self._required_match(MatchType.EXACT, strong_skill),
            self._required_match(MatchType.NONE, []),
        ]
        candidate = Candidate(candidate_id="c1")
        result = overall_confidence(matches, candidate, AS_OF)

        plain_average = 0.5  # (~1.0 + 0.0) / 2, for comparison
        assert result < plain_average

    def test_capped_by_completeness_score(self):
        strong_skill = [_skill(_evidence(
            source_type=EvidenceSourceType.EXPERIENCE, depth=EvidenceDepth.CENTRAL, verified=True,
        ))]
        matches = [self._required_match(MatchType.EXACT, strong_skill)]
        candidate = Candidate(candidate_id="c1", completeness_score=0.3)

        result = overall_confidence(matches, candidate, AS_OF)
        assert result <= 0.3

    def test_no_completeness_score_does_not_artificially_cap(self):
        strong_skill = [_skill(_evidence(
            source_type=EvidenceSourceType.EXPERIENCE, depth=EvidenceDepth.CENTRAL, verified=True,
        ))]
        matches = [self._required_match(MatchType.EXACT, strong_skill)]
        candidate = Candidate(candidate_id="c1", completeness_score=None)

        result = overall_confidence(matches, candidate, AS_OF)
        assert result > 0.5


# ─── Full pipeline integration (Milestones 1, 3, 4, 5 together) ──────────

class TestFullPipelineConfidence:
    def test_exact_match_outranks_transferable_match_end_to_end(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = {m.requirement.raw_text: m for m in match_job(job, candidate)}

        python_confidence = requirement_confidence(matches["Python"], AS_OF)  # EXACT
        tensorflow_confidence = requirement_confidence(matches["TensorFlow"], AS_OF)  # TRANSFERABLE

        assert 0 < tensorflow_confidence < python_confidence <= 1.0

    def test_overall_confidence_is_plausible_for_a_strong_candidate(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)

        result = overall_confidence(matches, candidate, AS_OF)
        assert 0.3 < result <= 1.0

    def test_overall_confidence_is_low_for_a_sparse_unrelated_candidate(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_sparse_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)

        result = overall_confidence(matches, candidate, AS_OF)
        assert result == 0.0  # no requirement resolved at all -- JavaScript is unrelated to every requirement
