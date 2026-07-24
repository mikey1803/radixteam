"""
Skill Matching — Milestone 4 Unit Tests.

Covers relationships.py (curated relationship graph lookups) and
matching.py (deterministic exact/transferable/adjacent classification),
built on top of the normalization pipeline from Milestone 3.
"""

import json
from pathlib import Path

from modules.skill_matching.adapters import adapt_candidate, adapt_job
from modules.skill_matching.matching import MatchType, match_job, match_requirement
from modules.skill_matching.models import Candidate, CandidateSkill, Job, JobSkillRequirement
from modules.skill_matching.normalization import normalize_candidate, normalize_job
from modules.skill_matching.relationships import RelationshipType, get_relationship

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skill_matching"


def _load(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _normalized_candidate(fixture_name: str) -> Candidate:
    return normalize_candidate(adapt_candidate(_load(fixture_name)))


def _normalized_job(fixture_name: str) -> Job:
    return normalize_job(adapt_job(_load(fixture_name)))


# ─── Relationship graph ───────────────────────────────────────────────────

class TestGetRelationship:
    def test_known_transferable_pair(self):
        relationship = get_relationship("pytorch", "tensorflow")
        assert relationship is not None
        rel_type, confidence = relationship
        assert rel_type == RelationshipType.TRANSFERABLE
        assert 0 < confidence <= 1

    def test_lookup_is_symmetric(self):
        assert get_relationship("pytorch", "tensorflow") == get_relationship("tensorflow", "pytorch")

    def test_known_adjacent_pair(self):
        rel_type, _ = get_relationship("django", "fastapi")
        assert rel_type == RelationshipType.ADJACENT

    def test_unknown_pair_returns_none(self):
        assert get_relationship("python", "aws") is None

    def test_identical_skill_returns_none(self):
        assert get_relationship("python", "python") is None


# ─── match_requirement (unit) ─────────────────────────────────────────────

class TestMatchRequirement:
    def test_exact_match(self):
        requirement = JobSkillRequirement(raw_text="Python", canonical_skill_id="python")
        candidate_by_canonical = {
            "python": [CandidateSkill(raw_text="Python", canonical_skill_id="python")]
        }
        match = match_requirement(requirement, candidate_by_canonical)

        assert match.match_type == MatchType.EXACT
        assert len(match.matched_candidate_skills) == 1
        assert match.relationship_confidence is None

    def test_transferable_match(self):
        requirement = JobSkillRequirement(raw_text="TensorFlow", canonical_skill_id="tensorflow")
        candidate_by_canonical = {
            "pytorch": [CandidateSkill(raw_text="PyTorch", canonical_skill_id="pytorch")]
        }
        match = match_requirement(requirement, candidate_by_canonical)

        assert match.match_type == MatchType.TRANSFERABLE
        assert match.matched_candidate_skills[0].raw_text == "PyTorch"
        assert match.relationship_confidence == 0.7

    def test_adjacent_match(self):
        requirement = JobSkillRequirement(raw_text="Django", canonical_skill_id="django")
        candidate_by_canonical = {
            "fastapi": [CandidateSkill(raw_text="FastAPI", canonical_skill_id="fastapi")]
        }
        match = match_requirement(requirement, candidate_by_canonical)

        assert match.match_type == MatchType.ADJACENT

    def test_transferable_preferred_over_adjacent_when_both_available(self):
        # Requirement is tensorflow; candidate has both pytorch (transferable)
        # and django (unrelated to tensorflow) -- only pytorch should win,
        # and it must win as TRANSFERABLE, not be shadowed by anything weaker.
        requirement = JobSkillRequirement(raw_text="TensorFlow", canonical_skill_id="tensorflow")
        candidate_by_canonical = {
            "pytorch": [CandidateSkill(raw_text="PyTorch", canonical_skill_id="pytorch")],
            "django": [CandidateSkill(raw_text="Django", canonical_skill_id="django")],
        }
        match = match_requirement(requirement, candidate_by_canonical)
        assert match.match_type == MatchType.TRANSFERABLE
        assert match.matched_candidate_skills[0].raw_text == "PyTorch"

    def test_no_match(self):
        requirement = JobSkillRequirement(raw_text="AWS", canonical_skill_id="aws")
        candidate_by_canonical = {
            "python": [CandidateSkill(raw_text="Python", canonical_skill_id="python")]
        }
        match = match_requirement(requirement, candidate_by_canonical)

        assert match.match_type == MatchType.NONE
        assert match.matched_candidate_skills == []

    def test_unmapped_requirement_still_produces_a_match_result(self):
        # canonical_skill_id=None -- e.g. an unknown/emerging technology.
        # Per algorithm doc §9 this must still surface, never disappear.
        requirement = JobSkillRequirement(raw_text="Some New Framework", canonical_skill_id=None)
        match = match_requirement(requirement, {})

        assert match.match_type == MatchType.NONE
        assert match.requirement.raw_text == "Some New Framework"

    def test_duplicate_candidate_skill_entries_are_all_preserved(self):
        requirement = JobSkillRequirement(raw_text="Python", canonical_skill_id="python")
        candidate_by_canonical = {
            "python": [
                CandidateSkill(raw_text="Python", canonical_skill_id="python"),
                CandidateSkill(raw_text="python", canonical_skill_id="python"),
            ]
        }
        match = match_requirement(requirement, candidate_by_canonical)
        assert len(match.matched_candidate_skills) == 2


# ─── match_job (integration with Milestones 1 & 3) ────────────────────────

class TestMatchJob:
    def test_full_fixture_pipeline(self):
        candidate = _normalized_candidate("candidate_fixture.json")
        job = _normalized_job("job_fixture.json")

        matches = {m.requirement.raw_text: m for m in match_job(job, candidate)}

        # required skills the candidate has directly
        assert matches["Python"].match_type == MatchType.EXACT
        assert matches["FastAPI"].match_type == MatchType.EXACT
        assert matches["Docker"].match_type == MatchType.EXACT
        assert matches["SQL"].match_type == MatchType.EXACT

        # preferred: candidate has Kubernetes directly (via certification)
        assert matches["Kubernetes"].match_type == MatchType.EXACT

        # preferred: candidate lacks TensorFlow outright, but has PyTorch --
        # the flagship transferable case from the design docs, now running
        # end to end against real fixture data.
        assert matches["TensorFlow"].match_type == MatchType.TRANSFERABLE
        assert matches["TensorFlow"].matched_candidate_skills[0].raw_text == "PyTorch"

    def test_sparse_candidate_produces_all_none_without_crashing(self):
        candidate = _normalized_candidate("candidate_sparse_fixture.json")
        job = _normalized_job("job_fixture.json")

        matches = match_job(job, candidate)

        assert len(matches) == 6  # 4 required + 2 preferred
        assert all(m.match_type == MatchType.NONE for m in matches)

    def test_empty_job_produces_empty_match_list(self):
        candidate = _normalized_candidate("candidate_fixture.json")
        job = _normalized_job("job_empty_fixture.json")

        assert match_job(job, candidate) == []
