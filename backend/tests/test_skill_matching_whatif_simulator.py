"""
Skill Matching — Milestone 11 Unit Tests (whatif_simulator.py).

Covers simulate_added_skill: rerunning the deterministic pipeline with a
hypothetical skill added, and the resulting score/confidence/gap deltas.
"""

import json
from datetime import date
from pathlib import Path

from modules.skill_matching.adapters import adapt_candidate, adapt_job
from modules.skill_matching.innovation.whatif_simulator import simulate_added_skill
from modules.skill_matching.models import EvidenceDepth
from modules.skill_matching.normalization import normalize_candidate, normalize_job

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skill_matching"
AS_OF = date(2024, 12, 1)


def _load(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class TestSimulateAddedSkill:
    def test_adding_a_missing_required_skill_improves_score(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_sparse_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))

        result = simulate_added_skill(candidate, job, "Python", AS_OF)

        assert result.hypothetical_skill_recognized is True
        assert result.score_delta > 0
        assert result.projected.overall_score > result.baseline.overall_score

    def test_adding_a_missing_required_skill_resolves_a_critical_gap(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_sparse_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))

        result = simulate_added_skill(candidate, job, "Python", AS_OF)

        assert result.baseline.critical_gap_count == 4  # Python, FastAPI, Docker, SQL
        assert result.projected.critical_gap_count == 3
        assert result.critical_gaps_resolved == 1

    def test_unrecognized_hypothetical_skill_is_flagged_and_produces_no_score_change(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_sparse_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))

        result = simulate_added_skill(candidate, job, "Some Made Up Technology", AS_OF)

        assert result.hypothetical_skill_recognized is False
        assert result.score_delta == 0.0
        assert result.critical_gaps_resolved == 0

    def test_adding_a_skill_the_candidate_already_has_produces_only_a_negligible_change(self):
        # A duplicate claim isn't literally a no-op: the corroboration
        # combination (confidence.py's noisy-OR) gives it a tiny additional
        # weight, same as any other corroborating evidence would. The
        # meaningful property to assert is that this is negligible compared
        # to a genuinely new skill's improvement, not that it's exactly zero.
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        sparse_candidate = normalize_candidate(adapt_candidate(_load("candidate_sparse_fixture.json")))

        redundant_result = simulate_added_skill(candidate, job, "Python", AS_OF)
        genuinely_new_result = simulate_added_skill(sparse_candidate, job, "Python", AS_OF)

        assert redundant_result.hypothetical_skill_recognized is True
        assert redundant_result.critical_gaps_resolved == 0
        assert abs(redundant_result.score_delta) < 0.01
        assert redundant_result.score_delta < genuinely_new_result.score_delta

    def test_stronger_hypothetical_depth_produces_a_higher_or_equal_projected_confidence(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_sparse_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))

        weak = simulate_added_skill(candidate, job, "Python", AS_OF, hypothetical_depth=EvidenceDepth.MENTIONED)
        strong = simulate_added_skill(candidate, job, "Python", AS_OF, hypothetical_depth=EvidenceDepth.CENTRAL)

        assert strong.projected.overall_confidence >= weak.projected.overall_confidence

    def test_baseline_is_unaffected_by_the_hypothetical_addition(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_sparse_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))

        result = simulate_added_skill(candidate, job, "Python", AS_OF)
        # original candidate object must not have been mutated
        assert not any(s.raw_text == "Python" for s in candidate.skills)
        assert result.baseline.overall_score == 0.0
