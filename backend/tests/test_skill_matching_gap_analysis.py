"""
Skill Matching — Milestone 7 Unit Tests.

Covers gap_analysis.py: the deterministic rule table classifying every
non-exact match into Critical / Moderate / Low Impact / Nice-to-Have, plus
a full-fixture integration pass and an explicit reproduction of the
Docker/Kubernetes "reduces onboarding risk" worked example from the AI
reasoning design.
"""

import json
from datetime import date
from pathlib import Path

from modules.skill_matching.adapters import adapt_candidate, adapt_job
from modules.skill_matching.gap_analysis import GapSeverity, analyze_gaps, classify_gap_severity
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
        source_type=EvidenceSourceType.CERTIFICATION,
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
    relationship_confidence: float | None = None,
) -> SkillMatch:
    requirement = JobSkillRequirement(
        raw_text="req", canonical_skill_id="req", level=level, category=category
    )
    skills = [CandidateSkill(raw_text="s", canonical_skill_id="s", evidence=evidence or [])] if evidence else []
    return SkillMatch(
        requirement=requirement,
        match_type=match_type,
        matched_candidate_skills=skills,
        relationship_confidence=relationship_confidence,
    )


# ─── Rule table coverage ───────────────────────────────────────────────────

class TestClassifyGapSeverity:
    def test_required_core_technical_no_evidence_is_critical(self):
        match = _match(MatchType.NONE, level=RequirementLevel.REQUIRED, category=SkillCategory.CORE_TECHNICAL)
        assert classify_gap_severity(match, AS_OF) == GapSeverity.CRITICAL

    def test_required_unknown_category_no_evidence_is_still_critical(self):
        # Unknown (unmapped/emerging) skills must not be under-flagged just
        # because their category couldn't be determined.
        match = _match(MatchType.NONE, level=RequirementLevel.REQUIRED, category=SkillCategory.UNKNOWN)
        assert classify_gap_severity(match, AS_OF) == GapSeverity.CRITICAL

    def test_required_soft_skill_no_evidence_is_softened_to_moderate(self):
        match = _match(MatchType.NONE, level=RequirementLevel.REQUIRED, category=SkillCategory.SOFT_SKILL)
        assert classify_gap_severity(match, AS_OF) == GapSeverity.MODERATE

    def test_required_strong_transferable_evidence_is_moderate(self):
        strong_evidence = [_evidence(verified=True)]
        match = _match(
            MatchType.TRANSFERABLE,
            level=RequirementLevel.REQUIRED,
            category=SkillCategory.TOOL_PLATFORM,
            evidence=strong_evidence,
            relationship_confidence=0.7,
        )
        assert classify_gap_severity(match, AS_OF) == GapSeverity.MODERATE

    def test_required_weak_adjacent_evidence_stays_critical(self):
        weak_evidence = [_evidence(source_type=EvidenceSourceType.PROFILE_SUMMARY, depth=EvidenceDepth.MENTIONED)]
        match = _match(
            MatchType.ADJACENT,
            level=RequirementLevel.REQUIRED,
            category=SkillCategory.FRAMEWORK,
            evidence=weak_evidence,
            relationship_confidence=0.5,
        )
        assert classify_gap_severity(match, AS_OF) == GapSeverity.CRITICAL

    def test_preferred_core_technical_no_evidence_is_low_impact(self):
        match = _match(MatchType.NONE, level=RequirementLevel.PREFERRED, category=SkillCategory.CORE_TECHNICAL)
        assert classify_gap_severity(match, AS_OF) == GapSeverity.LOW_IMPACT

    def test_preferred_soft_skill_no_evidence_is_nice_to_have(self):
        match = _match(MatchType.NONE, level=RequirementLevel.PREFERRED, category=SkillCategory.SOFT_SKILL)
        assert classify_gap_severity(match, AS_OF) == GapSeverity.NICE_TO_HAVE

    def test_preferred_strong_transferable_evidence_is_nice_to_have(self):
        strong_evidence = [_evidence(verified=True)]
        match = _match(
            MatchType.TRANSFERABLE,
            level=RequirementLevel.PREFERRED,
            category=SkillCategory.FRAMEWORK,
            evidence=strong_evidence,
            relationship_confidence=0.7,
        )
        assert classify_gap_severity(match, AS_OF) == GapSeverity.NICE_TO_HAVE

    def test_preferred_weak_adjacent_evidence_stays_low_impact(self):
        weak_evidence = [_evidence(source_type=EvidenceSourceType.PROFILE_SUMMARY, depth=EvidenceDepth.MENTIONED)]
        match = _match(
            MatchType.ADJACENT,
            level=RequirementLevel.PREFERRED,
            category=SkillCategory.TOOL_PLATFORM,
            evidence=weak_evidence,
            relationship_confidence=0.5,
        )
        assert classify_gap_severity(match, AS_OF) == GapSeverity.LOW_IMPACT


# ─── analyze_gaps ──────────────────────────────────────────────────────────

class TestAnalyzeGaps:
    def test_exact_matches_are_excluded_entirely(self):
        matches = [_match(MatchType.EXACT, evidence=[_evidence()])]
        assert analyze_gaps(matches, AS_OF) == []

    def test_non_exact_matches_all_produce_a_gap_entry(self):
        matches = [
            _match(MatchType.NONE),
            _match(MatchType.TRANSFERABLE, evidence=[_evidence()], relationship_confidence=0.7),
            _match(MatchType.ADJACENT, evidence=[_evidence()], relationship_confidence=0.5),
        ]
        gaps = analyze_gaps(matches, AS_OF)
        assert len(gaps) == 3
        assert {g.match_type for g in gaps} == {MatchType.NONE, MatchType.TRANSFERABLE, MatchType.ADJACENT}

    def test_none_match_gap_has_empty_matched_via(self):
        gaps = analyze_gaps([_match(MatchType.NONE)], AS_OF)
        assert gaps[0].matched_via == []
        assert gaps[0].mitigating_confidence == 0.0

    def test_transferable_gap_carries_the_matched_candidate_skills(self):
        skill_evidence = [_evidence()]
        gaps = analyze_gaps(
            [_match(MatchType.TRANSFERABLE, evidence=skill_evidence, relationship_confidence=0.7)], AS_OF
        )
        assert len(gaps[0].matched_via) == 1


# ─── Flagship worked example: Docker gap mitigated by Kubernetes evidence ─

class TestDockerKubernetesWorkedExample:
    def test_docker_gap_mitigated_by_kubernetes_evidence_is_moderate_not_critical(self):
        kubernetes_evidence = [
            SkillEvidence(
                source_type=EvidenceSourceType.CERTIFICATION,
                source_reference="Kubernetes Fundamentals",
                depth=EvidenceDepth.CENTRAL,
                end_date=date(2023, 11, 1),
            )
        ]
        docker_requirement_via_kubernetes = _match(
            MatchType.TRANSFERABLE,
            level=RequirementLevel.REQUIRED,
            category=SkillCategory.TOOL_PLATFORM,
            evidence=kubernetes_evidence,
            relationship_confidence=0.6,  # docker<->kubernetes prior, see relationships.py
        )

        gap = analyze_gaps([docker_requirement_via_kubernetes], AS_OF)[0]

        # This is the exact scenario the AI reasoning design narrates as
        # "candidate demonstrates container concepts through Kubernetes
        # coursework, reducing onboarding risk" -- it must land as Moderate,
        # not Critical, or that walkthrough would be false in code.
        assert gap.severity == GapSeverity.MODERATE
        assert gap.match_type == MatchType.TRANSFERABLE


# ─── Full pipeline integration (Milestones 1, 3, 4, 5, 7 together) ───────

class TestFullPipelineGapAnalysis:
    def test_strong_candidate_has_no_required_gaps_and_a_transferable_preferred_gap(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)

        gaps = analyze_gaps(matches, AS_OF)
        gap_texts = {g.requirement.raw_text for g in gaps}

        # every required skill is an exact match in this fixture -- no
        # required gaps at all
        assert not any(g.requirement.level == RequirementLevel.REQUIRED for g in gaps)

        # TensorFlow (preferred) is only reachable via PyTorch transferable
        # evidence -- it must appear as a gap, softened by that evidence
        assert "TensorFlow" in gap_texts
        tensorflow_gap = next(g for g in gaps if g.requirement.raw_text == "TensorFlow")
        assert tensorflow_gap.match_type == MatchType.TRANSFERABLE
        assert tensorflow_gap.severity == GapSeverity.NICE_TO_HAVE

    def test_sparse_unrelated_candidate_has_all_required_skills_as_critical_gaps(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_sparse_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)

        gaps = analyze_gaps(matches, AS_OF)
        required_gaps = [g for g in gaps if g.requirement.level == RequirementLevel.REQUIRED]

        assert len(required_gaps) == 4  # Python, FastAPI, Docker, SQL
        assert all(g.severity == GapSeverity.CRITICAL for g in required_gaps)
