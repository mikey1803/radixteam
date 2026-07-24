"""
Skill Matching — Milestone 10 Unit Tests.

Covers innovation/interview_intelligence.py: purpose-tagged question
generation, the CRITICAL/MODERATE-only severity filter, difficulty
scaling with evidence strength, and a full fixture-driven integration
pass across a strong (well-evidenced) and a sparse (unrelated) candidate.
"""

import json
from datetime import date
from pathlib import Path

from modules.skill_matching.adapters import adapt_candidate, adapt_job
from modules.skill_matching.gap_analysis import Gap, GapSeverity, analyze_gaps
from modules.skill_matching.innovation.interview_intelligence import (
    QuestionDifficulty,
    QuestionPurpose,
    generate_interview_questions,
)
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

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skill_matching"
AS_OF = date(2024, 12, 1)


def _load(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _evidence(**overrides) -> SkillEvidence:
    defaults = dict(
        source_type=EvidenceSourceType.PROJECT,
        source_reference="ref",
        depth=EvidenceDepth.DESCRIBED,
        end_date=date(2024, 6, 1),
    )
    defaults.update(overrides)
    return SkillEvidence(**defaults)


def _requirement(raw_text: str, level=RequirementLevel.REQUIRED, category=SkillCategory.CORE_TECHNICAL) -> JobSkillRequirement:
    return JobSkillRequirement(raw_text=raw_text, canonical_skill_id=raw_text.lower(), level=level, category=category)


def _gap(raw_text: str, severity: GapSeverity, match_type=MatchType.NONE, matched_via=None) -> Gap:
    return Gap(
        requirement=_requirement(raw_text),
        match_type=match_type,
        severity=severity,
        mitigating_confidence=0.0,
        matched_via=matched_via or [],
    )


def _exact_match(raw_text: str, evidence: list[SkillEvidence]) -> SkillMatch:
    skill = CandidateSkill(raw_text=raw_text, canonical_skill_id=raw_text.lower(), evidence=evidence)
    return SkillMatch(requirement=_requirement(raw_text), match_type=MatchType.EXACT, matched_candidate_skills=[skill])


# ─── Severity filter: only CRITICAL/MODERATE gaps generate questions ─────

class TestSeverityFilter:
    def test_critical_gap_produces_a_question(self):
        gaps = [_gap("Docker", GapSeverity.CRITICAL)]
        questions = generate_interview_questions([], gaps, AS_OF)
        assert len(questions) == 1

    def test_moderate_gap_produces_a_question(self):
        gaps = [_gap("Docker", GapSeverity.MODERATE)]
        questions = generate_interview_questions([], gaps, AS_OF)
        assert len(questions) == 1

    def test_low_impact_gap_produces_no_question(self):
        gaps = [_gap("Docker", GapSeverity.LOW_IMPACT)]
        assert generate_interview_questions([], gaps, AS_OF) == []

    def test_nice_to_have_gap_produces_no_question(self):
        gaps = [_gap("Docker", GapSeverity.NICE_TO_HAVE)]
        assert generate_interview_questions([], gaps, AS_OF) == []


# ─── Purpose routing ───────────────────────────────────────────────────────

class TestPurposeRouting:
    def test_none_match_gap_is_gap_verification(self):
        gaps = [_gap("Docker", GapSeverity.CRITICAL, match_type=MatchType.NONE)]
        questions = generate_interview_questions([], gaps, AS_OF)
        assert questions[0].purpose == QuestionPurpose.GAP_VERIFICATION
        assert questions[0].related_skill == "Docker"

    def test_transferable_gap_with_evidence_is_transferability_verification(self):
        related_skill = CandidateSkill(
            raw_text="Kubernetes", canonical_skill_id="kubernetes", evidence=[_evidence(depth=EvidenceDepth.CENTRAL)]
        )
        gaps = [_gap("Docker", GapSeverity.MODERATE, match_type=MatchType.TRANSFERABLE, matched_via=[related_skill])]
        questions = generate_interview_questions([], gaps, AS_OF)
        assert questions[0].purpose == QuestionPurpose.TRANSFERABILITY_VERIFICATION
        assert questions[0].related_skill == "Docker"

    def test_adjacent_gap_with_evidence_is_also_transferability_verification(self):
        related_skill = CandidateSkill(
            raw_text="FastAPI", canonical_skill_id="fastapi", evidence=[_evidence(depth=EvidenceDepth.CENTRAL)]
        )
        gaps = [_gap("Django", GapSeverity.MODERATE, match_type=MatchType.ADJACENT, matched_via=[related_skill])]
        questions = generate_interview_questions([], gaps, AS_OF)
        assert questions[0].purpose == QuestionPurpose.TRANSFERABILITY_VERIFICATION

    def test_weak_exact_match_is_evidence_depth_verification(self):
        weak_evidence = [_evidence(source_type=EvidenceSourceType.PROFILE_SUMMARY, depth=EvidenceDepth.MENTIONED)]
        matches = [_exact_match("Python", weak_evidence)]
        questions = generate_interview_questions(matches, [], AS_OF)
        assert len(questions) == 1
        assert questions[0].purpose == QuestionPurpose.EVIDENCE_DEPTH_VERIFICATION
        assert questions[0].related_skill == "Python"

    def test_strong_exact_match_produces_no_question(self):
        strong_evidence = [_evidence(source_type=EvidenceSourceType.EXPERIENCE, depth=EvidenceDepth.CENTRAL, verified=True)]
        matches = [_exact_match("Python", strong_evidence)]
        assert generate_interview_questions(matches, [], AS_OF) == []


# ─── Difficulty scaling ─────────────────────────────────────────────────────

class TestDifficultyScaling:
    def test_transferability_question_is_probing_with_strong_related_evidence(self):
        related_skill = CandidateSkill(
            raw_text="Kubernetes", canonical_skill_id="kubernetes",
            evidence=[_evidence(source_type=EvidenceSourceType.EXPERIENCE, depth=EvidenceDepth.CENTRAL, verified=True)],
        )
        gaps = [_gap("Docker", GapSeverity.MODERATE, match_type=MatchType.TRANSFERABLE, matched_via=[related_skill])]
        questions = generate_interview_questions([], gaps, AS_OF)
        assert questions[0].difficulty == QuestionDifficulty.PROBING

    def test_transferability_question_is_foundational_with_weak_related_evidence(self):
        related_skill = CandidateSkill(
            raw_text="Kubernetes", canonical_skill_id="kubernetes",
            evidence=[_evidence(source_type=EvidenceSourceType.PROFILE_SUMMARY, depth=EvidenceDepth.MENTIONED)],
        )
        gaps = [_gap("Docker", GapSeverity.MODERATE, match_type=MatchType.TRANSFERABLE, matched_via=[related_skill])]
        questions = generate_interview_questions([], gaps, AS_OF)
        assert questions[0].difficulty == QuestionDifficulty.FOUNDATIONAL

    def test_evidence_depth_question_is_probing_with_moderate_confidence(self):
        # Just under the question threshold but above the strong-evidence
        # floor -- PROJECT + DESCRIBED with no date info: 0.85 * 0.85 * 0.8 = 0.578
        # (explicitly no end_date -- the helper's default end_date would put
        # this in the "current" recency bucket at 0.7225, above the question
        # threshold entirely, and generate no question at all).
        moderate_evidence = [
            _evidence(source_type=EvidenceSourceType.PROJECT, depth=EvidenceDepth.DESCRIBED, end_date=None)
        ]
        matches = [_exact_match("Python", moderate_evidence)]
        questions = generate_interview_questions(matches, [], AS_OF)
        assert len(questions) == 1
        assert questions[0].difficulty == QuestionDifficulty.PROBING

    def test_evidence_depth_question_is_foundational_with_very_weak_confidence(self):
        weak_evidence = [_evidence(source_type=EvidenceSourceType.PROFILE_SUMMARY, depth=EvidenceDepth.MENTIONED)]
        matches = [_exact_match("Python", weak_evidence)]
        questions = generate_interview_questions(matches, [], AS_OF)
        assert questions[0].difficulty == QuestionDifficulty.FOUNDATIONAL

    def test_gap_verification_question_is_always_foundational(self):
        gaps = [_gap("Docker", GapSeverity.CRITICAL, match_type=MatchType.NONE)]
        questions = generate_interview_questions([], gaps, AS_OF)
        assert questions[0].difficulty == QuestionDifficulty.FOUNDATIONAL


# ─── Full pipeline integration (Milestones 1, 3, 4, 5, 7, 10 together) ────

class TestFullPipelineInterviewQuestions:
    def test_strong_well_evidenced_candidate_needs_no_questions(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)
        gaps = analyze_gaps(matches, AS_OF)

        questions = generate_interview_questions(matches, gaps, AS_OF)
        # every required skill is strongly evidenced and exactly matched;
        # the one gap (TensorFlow) is NICE_TO_HAVE, below the priority
        # threshold -- a clean match needs no clarifying questions.
        assert questions == []

    def test_sparse_unrelated_candidate_gets_gap_verification_questions(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_sparse_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)
        gaps = analyze_gaps(matches, AS_OF)

        questions = generate_interview_questions(matches, gaps, AS_OF)
        assert len(questions) == 4  # Python, FastAPI, Docker, SQL -- all CRITICAL, all NONE
        assert all(q.purpose == QuestionPurpose.GAP_VERIFICATION for q in questions)
        assert all(q.difficulty == QuestionDifficulty.FOUNDATIONAL for q in questions)
        assert {q.related_skill for q in questions} == {"Python", "FastAPI", "Docker", "SQL"}
