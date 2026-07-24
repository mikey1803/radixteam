"""
Skill Matching — Milestone 8 Unit Tests.

Covers recommendation.py: the deterministic tier decision, the
confidence-gating invariant the whole design insists on, and a full
fixture-driven pipeline run producing complete deterministic output --
score, gaps, and tier together, with zero AI dependency. This is the
milestone-8 checkpoint: everything below must work without ever touching
the network.
"""

import json
from datetime import date
from pathlib import Path

from modules.skill_matching.adapters import adapt_candidate, adapt_job
from modules.skill_matching.confidence import overall_confidence
from modules.skill_matching.gap_analysis import Gap, GapSeverity, analyze_gaps
from modules.skill_matching.matching import MatchType, match_job
from modules.skill_matching.models import JobSkillRequirement, RequirementLevel, SkillCategory
from modules.skill_matching.normalization import normalize_candidate, normalize_job
from modules.skill_matching.recommendation import ConfidenceLabel, RecommendationTier, recommend
from modules.skill_matching.scoring import ScoreResult, score_match

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skill_matching"
AS_OF = date(2024, 12, 1)


def _load(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _score(overall: float) -> ScoreResult:
    return ScoreResult(overall_score=overall)


def _gap(severity: GapSeverity) -> Gap:
    requirement = JobSkillRequirement(
        raw_text="x", canonical_skill_id="x",
        level=RequirementLevel.REQUIRED, category=SkillCategory.CORE_TECHNICAL,
    )
    return Gap(requirement=requirement, match_type=MatchType.NONE, severity=severity, mitigating_confidence=0.0)


# ─── Rule table coverage ───────────────────────────────────────────────────

class TestRecommendTier:
    def test_two_or_more_critical_gaps_is_always_low_match(self):
        gaps = [_gap(GapSeverity.CRITICAL), _gap(GapSeverity.CRITICAL)]
        result = recommend(_score(0.95), 0.95, gaps)  # even with a great score/confidence
        assert result.tier == RecommendationTier.LOW_MATCH

    def test_one_critical_gap_with_meaningful_overlap_is_needs_upskilling(self):
        gaps = [_gap(GapSeverity.CRITICAL)]
        result = recommend(_score(0.6), 0.7, gaps)
        assert result.tier == RecommendationTier.NEEDS_UPSKILLING

    def test_one_critical_gap_with_too_little_overlap_is_low_match(self):
        gaps = [_gap(GapSeverity.CRITICAL)]
        result = recommend(_score(0.1), 0.7, gaps)
        assert result.tier == RecommendationTier.LOW_MATCH

    def test_no_critical_gaps_but_score_below_floor_is_low_match(self):
        result = recommend(_score(0.1), 0.9, [])
        assert result.tier == RecommendationTier.LOW_MATCH

    def test_high_score_high_confidence_no_critical_gaps_is_strong_match(self):
        result = recommend(_score(0.85), 0.8, [])
        assert result.tier == RecommendationTier.STRONG_MATCH

    def test_high_score_but_low_confidence_must_not_read_as_strong_match(self):
        # The invariant this whole milestone exists to enforce.
        result = recommend(_score(0.9), 0.3, [])
        assert result.tier != RecommendationTier.STRONG_MATCH
        assert result.tier == RecommendationTier.POTENTIAL_MATCH

    def test_moderate_score_reasonable_confidence_few_moderate_gaps_is_good_match(self):
        gaps = [_gap(GapSeverity.MODERATE), _gap(GapSeverity.MODERATE)]
        result = recommend(_score(0.6), 0.6, gaps)
        assert result.tier == RecommendationTier.GOOD_MATCH

    def test_moderate_score_but_several_moderate_gaps_downgrades_to_potential(self):
        gaps = [_gap(GapSeverity.MODERATE) for _ in range(3)]
        result = recommend(_score(0.6), 0.6, gaps)
        assert result.tier == RecommendationTier.POTENTIAL_MATCH

    def test_moderate_score_low_confidence_is_potential_match(self):
        result = recommend(_score(0.6), 0.3, [])
        assert result.tier == RecommendationTier.POTENTIAL_MATCH

    def test_low_but_above_floor_score_no_critical_gaps_is_potential_match(self):
        result = recommend(_score(0.35), 0.9, [])
        assert result.tier == RecommendationTier.POTENTIAL_MATCH


class TestConfidenceLabel:
    def test_high_confidence_label(self):
        assert recommend(_score(0.5), 0.75, []).confidence_label == ConfidenceLabel.HIGH

    def test_moderate_confidence_label(self):
        assert recommend(_score(0.5), 0.55, []).confidence_label == ConfidenceLabel.MODERATE

    def test_low_confidence_label(self):
        assert recommend(_score(0.5), 0.2, []).confidence_label == ConfidenceLabel.LOW


class TestRecommendGapCounts:
    def test_gap_counts_are_derived_correctly(self):
        gaps = [
            _gap(GapSeverity.CRITICAL),
            _gap(GapSeverity.MODERATE),
            _gap(GapSeverity.MODERATE),
            _gap(GapSeverity.LOW_IMPACT),
            _gap(GapSeverity.NICE_TO_HAVE),
        ]
        result = recommend(_score(0.5), 0.5, gaps)
        assert result.critical_gap_count == 1
        assert result.moderate_gap_count == 2


# ─── Full pipeline integration: the Milestone 8 checkpoint ───────────────

class TestFullPipelineRecommendation:
    """
    Runs the complete deterministic engine end to end -- adapt, normalize,
    match, score, confidence, gap analysis, recommendation -- with zero AI
    involvement. This is the demoable checkpoint the roadmap calls for.
    """

    def test_strong_candidate_is_potential_match_gated_by_confidence(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)

        score = score_match(matches, AS_OF)
        confidence = overall_confidence(matches, candidate, AS_OF)
        gaps = analyze_gaps(matches, AS_OF)
        result = recommend(score, confidence, gaps)

        # Grounded in the actual computed pipeline output, not assumed:
        # every required skill matches exactly (score ~0.80, well above the
        # Strong Match score bar), but overall confidence (~0.53) is pulled
        # down by the weaker transferable TensorFlow evidence and doesn't
        # clear the Strong Match confidence bar -- exactly the "confidence
        # gates the tier" behavior this milestone exists to enforce, not a
        # defect. Assertions use bounds, not brittle exact floats.
        assert score.overall_score > 0.75
        assert 0.4 < confidence < 0.7
        assert result.critical_gap_count == 0
        assert result.tier == RecommendationTier.POTENTIAL_MATCH
        assert result.confidence_label == ConfidenceLabel.MODERATE

    def test_sparse_unrelated_candidate_is_low_match(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_sparse_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)

        score = score_match(matches, AS_OF)
        confidence = overall_confidence(matches, candidate, AS_OF)
        gaps = analyze_gaps(matches, AS_OF)
        result = recommend(score, confidence, gaps)

        assert score.overall_score == 0.0
        assert result.critical_gap_count >= 2
        assert result.tier == RecommendationTier.LOW_MATCH
