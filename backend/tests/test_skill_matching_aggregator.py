"""
Skill Matching — Milestone 9 Unit Tests (aggregator.py).

Covers assemble_match_report: pure merging of already-computed pipeline
output into one MatchReport. No pipeline execution or AI calls happen
here -- this file only checks the merge itself.
"""

from datetime import date

from modules.skill_matching.aggregator import assemble_match_report
from modules.skill_matching.gap_analysis import Gap, GapSeverity
from modules.skill_matching.matching import MatchType, SkillMatch
from modules.skill_matching.models import JobSkillRequirement
from modules.skill_matching.reasoning import ExplanationResult
from modules.skill_matching.recommendation import recommend
from modules.skill_matching.scoring import ScoreResult


def _match() -> SkillMatch:
    return SkillMatch(
        requirement=JobSkillRequirement(raw_text="Python", canonical_skill_id="python"),
        match_type=MatchType.EXACT,
    )


def _gap() -> Gap:
    requirement = JobSkillRequirement(raw_text="SQL", canonical_skill_id="sql")
    return Gap(requirement=requirement, match_type=MatchType.NONE, severity=GapSeverity.CRITICAL, mitigating_confidence=0.0)


class TestAssembleMatchReport:
    def test_merges_every_field_correctly(self):
        matches = [_match()]
        score = ScoreResult(overall_score=0.8)
        gaps = [_gap()]
        rec = recommend(score, 0.6, gaps)
        explanation = ExplanationResult(text="Some explanation.", source="template")

        report = assemble_match_report(
            candidate_id="cand-1", job_id="job-1", matches=matches, match_confidences=[1.0],
            score=score, confidence=0.6, gaps=gaps, recommendation=rec, explanation=explanation,
        )

        assert report.candidate_id == "cand-1"
        assert report.job_id == "job-1"
        assert report.matches == matches
        assert report.match_confidences == [1.0]
        assert report.score == score
        assert report.overall_confidence == 0.6
        assert report.gaps == gaps
        assert report.recommendation == rec
        assert report.explanation == "Some explanation."
        assert report.explanation_source == "template"

    def test_insights_defaults_to_none(self):
        score = ScoreResult(overall_score=0.5)
        rec = recommend(score, 0.5, [])
        explanation = ExplanationResult(text="x", source="template")

        report = assemble_match_report(
            candidate_id="c", job_id="j", matches=[], match_confidences=[], score=score,
            confidence=0.5, gaps=[], recommendation=rec, explanation=explanation,
        )
        assert report.insights is None
