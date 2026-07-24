"""
Skill Matching — Milestone 13 Testing Hardening Pass.

Not first-time test-writing: every stage already ships with its own
tests. This is a deliberate sweep for interactions between stages that
per-milestone tests wouldn't naturally exercise -- edge cases from
algorithm design §9 run through the REAL end-to-end pipeline rather than
constructed objects, a wider fixture matrix stress-testing the
recommendation tiers between the two extremes already covered, and a
basic sanity check against the O(J + C·E) complexity expectation from
algorithm design §10.

One real defect was found and fixed while building this pass (see
test_skill_matching_normalization.py's TestRequirementLevelConflictResolution
and normalization.py's _resolve_requirement_level_conflicts) -- exactly
the kind of thing this milestone exists to catch.
"""

import json
import time
from datetime import date
from pathlib import Path

from modules.skill_matching.adapters import adapt_candidate, adapt_job
from modules.skill_matching.confidence import overall_confidence
from modules.skill_matching.gap_analysis import GapSeverity, analyze_gaps
from modules.skill_matching.matching import MatchType, match_job
from modules.skill_matching.normalization import normalize_candidate, normalize_job
from modules.skill_matching.recommendation import RecommendationTier, recommend
from modules.skill_matching.scoring import score_match

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skill_matching"
AS_OF = date(2024, 12, 1)


def _load(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _run_pipeline(candidate_payload: dict, job_payload: dict):
    candidate = normalize_candidate(adapt_candidate(candidate_payload))
    job = normalize_job(adapt_job(job_payload))
    matches = match_job(job, candidate)
    score = score_match(matches, AS_OF)
    confidence = overall_confidence(matches, candidate, AS_OF)
    gaps = analyze_gaps(matches, AS_OF)
    recommendation = recommend(score, confidence, gaps)
    return matches, score, confidence, gaps, recommendation


# ─── Wider fixture matrix: an intermediate case between the two extremes ─

class TestPartialMatchEndToEnd:
    """
    Every prior milestone's fixture-driven tests used either the strong,
    fully-evidenced candidate or the fully unrelated sparse one -- the two
    extremes. This exercises the real middle ground: 3 of 4 required
    skills present with real evidence, one genuinely missing, through the
    complete real pipeline (not constructed SkillMatch/Gap objects).
    """

    def test_produces_needs_upskilling_with_exactly_one_critical_gap(self):
        matches, score, confidence, gaps, recommendation = _run_pipeline(
            _load("candidate_partial_fixture.json"), _load("job_fixture.json")
        )

        critical_gaps = [g for g in gaps if g.severity == GapSeverity.CRITICAL]
        assert len(critical_gaps) == 1
        assert critical_gaps[0].requirement.raw_text == "Docker"
        assert recommendation.tier == RecommendationTier.NEEDS_UPSKILLING

    def test_three_of_four_required_skills_are_exact_matches(self):
        matches, *_ = _run_pipeline(_load("candidate_partial_fixture.json"), _load("job_fixture.json"))
        exact = [m.requirement.raw_text for m in matches if m.match_type == MatchType.EXACT]
        assert set(exact) == {"Python", "FastAPI", "SQL"}

    def test_score_is_meaningfully_between_the_two_extremes(self):
        _, strong_score, *_ = _run_pipeline(_load("candidate_fixture.json"), _load("job_fixture.json"))
        _, partial_score, *_ = _run_pipeline(_load("candidate_partial_fixture.json"), _load("job_fixture.json"))
        _, sparse_score, *_ = _run_pipeline(_load("candidate_sparse_fixture.json"), _load("job_fixture.json"))

        assert sparse_score.overall_score < partial_score.overall_score < strong_score.overall_score


# ─── Edge cases from algorithm design §9, through the real pipeline ──────

class TestEmergingTechnologyEndToEnd:
    def test_unmapped_required_skill_never_silently_disappears(self):
        job_payload = {"id": "j-emerging", "required_skills": ["Python", "Some Emerging Framework XYZ"]}
        candidate_payload = {"id": "c-emerging", "skills": ["Python"]}

        matches, score, confidence, gaps, recommendation = _run_pipeline(candidate_payload, job_payload)

        assert any(m.requirement.raw_text == "Some Emerging Framework XYZ" for m in matches)
        unmapped_gap = next(g for g in gaps if g.requirement.raw_text == "Some Emerging Framework XYZ")
        assert unmapped_gap.severity == GapSeverity.CRITICAL
        # a single unmapped-but-required gap must not silently produce a
        # falsely perfect score
        assert score.overall_score < 1.0


class TestCorroboratingEvidenceEndToEnd:
    """
    A genuine verification CONFLICT (mixed verified=True/False on one
    skill's evidence, tested at the unit level in Milestone 5) turns out
    not to be reachable through the real pipeline at all: adapters.py
    never sets `verified` (always None), and service.py's
    apply_trust_signal only ever moves it None -> True, by design, never
    to False -- Talent Check's verified_skill_ids schema (as adapted,
    unverified against a real upstream contract) is a positive-only list,
    structurally incapable of expressing "confirmed false." That's a
    real, worth-recording finding from this hardening pass, not a gap to
    silently paper over with a misleading test: if a real Talent Check
    contract later needs to express failed verification, the schema
    assumption in adapters.py's adapt_trust_signal is exactly where that
    change belongs. What IS reachable end-to-end, and worth covering
    here, is corroboration -- multiple real evidence sources for the same
    skill combining through the full pipeline, not just at the
    skill_confidence unit level.
    """

    def test_multiple_evidence_sources_for_one_skill_score_higher_than_a_single_source(self):
        single_source = {
            "id": "c-single",
            "skills": ["Python"],
            "experience": [{"company": "A", "title": "Eng", "technologies": ["Python"]}],
        }
        multi_source = {
            "id": "c-multi",
            "skills": ["Python"],
            "experience": [{"company": "A", "title": "Eng", "technologies": ["Python"]}],
            "projects": [{"name": "Side Project", "technologies": ["Python"]}],
            "certifications": [{"name": "Python Certification"}],
        }
        job_payload = {"id": "j-corroboration", "required_skills": ["Python"]}

        _, single_score, *_ = _run_pipeline(single_source, job_payload)
        _, multi_score, *_ = _run_pipeline(multi_source, job_payload)

        assert multi_score.overall_score > single_score.overall_score


# ─── Complexity sanity check (algorithm design §10) ───────────────────────

class TestPerformanceSanityCheck:
    """
    Not a full performance suite (Milestone 14's job) -- a basic sanity
    check that the deterministic pipeline behaves like the O(J + C·E) the
    algorithm design promises rather than something accidentally
    quadratic, at a scale larger than any fixture used elsewhere.
    """

    def test_full_pipeline_completes_quickly_at_moderate_scale(self):
        # 30 required skills, 40 candidate skills, each with 2 evidence
        # sources -- comfortably larger than any real JD/resume in practice.
        required_skills = [f"Skill{i}" for i in range(30)]
        candidate_skills = [f"Skill{i}" for i in range(40)]
        experience = [
            {"company": f"Company{i}", "title": "Engineer", "technologies": candidate_skills[i : i + 5]}
            for i in range(8)
        ]

        job_payload = {"id": "j-scale", "required_skills": required_skills}
        candidate_payload = {"id": "c-scale", "skills": candidate_skills, "experience": experience}

        started = time.perf_counter()
        _run_pipeline(candidate_payload, job_payload)
        elapsed_seconds = time.perf_counter() - started

        assert elapsed_seconds < 0.5  # generous bound -- this should take low milliseconds in practice
