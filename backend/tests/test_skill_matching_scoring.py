"""
Skill Matching — Milestone 6 Unit Tests.

Covers scoring.py: per-requirement score contribution, required/preferred
sub-scores, and the overall score, plus the structural sanity invariants
the algorithm design requires (full coverage beats partial, verified
never scores below unverified, adjacent contribution stays capped small).
"""

import json
from datetime import date
from pathlib import Path

from modules.skill_matching.adapters import adapt_candidate, adapt_job
from modules.skill_matching.matching import MatchType, SkillMatch, match_job
from modules.skill_matching.models import (
    CandidateSkill,
    EvidenceDepth,
    EvidenceSourceType,
    JobSkillRequirement,
    RequirementLevel,
    SkillCategory,
    SkillEvidence,
)
from modules.skill_matching.normalization import normalize_candidate, normalize_job
from modules.skill_matching.scoring import requirement_score_contribution, score_match

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skill_matching"
AS_OF = date(2024, 12, 1)


def _load(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _evidence(**overrides) -> SkillEvidence:
    defaults = dict(
        source_type=EvidenceSourceType.EXPERIENCE,
        source_reference="ref",
        depth=EvidenceDepth.CENTRAL,
        end_date=date(2024, 6, 1),
    )
    defaults.update(overrides)
    return SkillEvidence(**defaults)


def _match(
    match_type: MatchType,
    level: RequirementLevel = RequirementLevel.REQUIRED,
    category: SkillCategory = SkillCategory.CORE_TECHNICAL,
    evidence: list[SkillEvidence] | None = None,
) -> SkillMatch:
    requirement = JobSkillRequirement(
        raw_text="req", canonical_skill_id="req", level=level, category=category
    )
    skills = [CandidateSkill(raw_text="s", canonical_skill_id="s", evidence=evidence or [])] if evidence else []
    return SkillMatch(requirement=requirement, match_type=match_type, matched_candidate_skills=skills)


# ─── Per-requirement contribution ─────────────────────────────────────────

class TestRequirementScoreContribution:
    def test_exact_match_with_strong_evidence_scores_near_one(self):
        match = _match(MatchType.EXACT, evidence=[_evidence(verified=True)])
        assert requirement_score_contribution(match, AS_OF) > 0.9

    def test_none_match_scores_zero(self):
        match = _match(MatchType.NONE)
        assert requirement_score_contribution(match, AS_OF) == 0.0

    def test_adjacent_match_contribution_stays_capped_small_even_with_best_evidence(self):
        best_possible_evidence = [_evidence(verified=True)]
        adjacent = _match(MatchType.ADJACENT, evidence=best_possible_evidence)
        exact = _match(MatchType.EXACT, evidence=best_possible_evidence)

        adjacent_score = requirement_score_contribution(adjacent, AS_OF)
        exact_score = requirement_score_contribution(exact, AS_OF)

        assert adjacent_score <= 0.21  # MATCH_TYPE_CEILING(0.5) * SCORE_CONTRIBUTION_MULTIPLIER(0.4)
        assert adjacent_score < exact_score / 3  # meaningfully smaller, not just "a bit lower"

    def test_transferable_contribution_not_further_dampened_beyond_its_confidence_ceiling(self):
        from modules.skill_matching.confidence import requirement_confidence

        transferable = _match(MatchType.TRANSFERABLE, evidence=[_evidence(verified=True)])
        assert requirement_score_contribution(transferable, AS_OF) == requirement_confidence(
            transferable, AS_OF
        )


# ─── Sanity invariants required by the algorithm design §4 ───────────────

class TestScoringSanityInvariants:
    def test_full_required_coverage_scores_higher_than_partial(self):
        full = [
            _match(MatchType.EXACT, evidence=[_evidence()]),
            _match(MatchType.EXACT, evidence=[_evidence()]),
        ]
        partial = [
            _match(MatchType.EXACT, evidence=[_evidence()]),
            _match(MatchType.NONE),
        ]
        assert score_match(full, AS_OF).overall_score > score_match(partial, AS_OF).overall_score

    def test_verified_evidence_never_scores_below_unverified_for_identical_skill(self):
        verified = [_match(MatchType.EXACT, evidence=[_evidence(verified=True)])]
        unverified = [_match(MatchType.EXACT, evidence=[_evidence(verified=None)])]

        verified_score = score_match(verified, AS_OF).overall_score
        unverified_score = score_match(unverified, AS_OF).overall_score

        assert verified_score >= unverified_score

    def test_explicitly_failed_verification_never_scores_above_unverified(self):
        failed = [_match(MatchType.EXACT, evidence=[_evidence(verified=False)])]
        unverified = [_match(MatchType.EXACT, evidence=[_evidence(verified=None)])]

        assert score_match(failed, AS_OF).overall_score <= score_match(unverified, AS_OF).overall_score

    def test_required_dominates_preferred_when_required_has_a_gap(self):
        matches = [
            _match(MatchType.NONE, level=RequirementLevel.REQUIRED),
            _match(MatchType.EXACT, level=RequirementLevel.PREFERRED, evidence=[_evidence(verified=True)]),
        ]
        result = score_match(matches, AS_OF)
        # perfect preferred coverage cannot paper over a required gap
        assert result.overall_score < 0.3

    def test_job_with_only_required_skills_overall_equals_required_sub_score(self):
        matches = [_match(MatchType.EXACT, evidence=[_evidence()])]
        result = score_match(matches, AS_OF)
        assert result.preferred_sub_score is None
        assert result.overall_score == result.required_sub_score

    def test_job_with_only_preferred_skills_overall_equals_preferred_sub_score(self):
        matches = [_match(MatchType.EXACT, level=RequirementLevel.PREFERRED, evidence=[_evidence()])]
        result = score_match(matches, AS_OF)
        assert result.required_sub_score is None
        assert result.overall_score == result.preferred_sub_score

    def test_empty_matches_scores_zero_without_raising(self):
        result = score_match([], AS_OF)
        assert result.overall_score == 0.0


# ─── Full pipeline integration (Milestones 1, 3, 4, 5, 6 together) ───────

class TestFullPipelineScoring:
    def test_strong_candidate_scores_highly_on_matching_job(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)

        result = score_match(matches, AS_OF)
        assert result.overall_score > 0.6
        assert result.required_sub_score is not None
        assert result.preferred_sub_score is not None

    def test_unrelated_sparse_candidate_scores_zero(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_sparse_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)

        result = score_match(matches, AS_OF)
        assert result.overall_score == 0.0
