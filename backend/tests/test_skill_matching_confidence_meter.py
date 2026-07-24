"""
Skill Matching — Milestone 11 Unit Tests (confidence_meter.py).

Covers compute_confidence_meter: a pure repackaging of already-computed
confidence values, never a recomputation.
"""

import json
from datetime import date
from pathlib import Path

from modules.skill_matching.adapters import adapt_candidate, adapt_job
from modules.skill_matching.confidence import overall_confidence, requirement_confidence
from modules.skill_matching.gap_analysis import analyze_gaps
from modules.skill_matching.innovation.confidence_meter import compute_confidence_meter
from modules.skill_matching.matching import match_job
from modules.skill_matching.normalization import normalize_candidate, normalize_job
from modules.skill_matching.recommendation import recommend
from modules.skill_matching.scoring import score_match

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skill_matching"
AS_OF = date(2024, 12, 1)


def _load(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class TestComputeConfidenceMeter:
    def test_per_requirement_entries_match_confidence_py_values_exactly(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)
        score = score_match(matches, AS_OF)
        confidence = overall_confidence(matches, candidate, AS_OF)
        gaps = analyze_gaps(matches, AS_OF)
        rec = recommend(score, confidence, gaps)

        meter = compute_confidence_meter(matches, rec, AS_OF)

        for entry, match in zip(meter.per_requirement, matches):
            assert entry.confidence == requirement_confidence(match, AS_OF)

    def test_overall_confidence_and_label_come_from_recommendation(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)
        score = score_match(matches, AS_OF)
        confidence = overall_confidence(matches, candidate, AS_OF)
        gaps = analyze_gaps(matches, AS_OF)
        rec = recommend(score, confidence, gaps)

        meter = compute_confidence_meter(matches, rec, AS_OF)
        assert meter.overall_confidence == rec.overall_confidence
        assert meter.overall_confidence_label == rec.confidence_label.value

    def test_weakest_requirement_excludes_none_matches(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_sparse_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)  # all NONE -- unrelated candidate
        score = score_match(matches, AS_OF)
        confidence = overall_confidence(matches, candidate, AS_OF)
        gaps = analyze_gaps(matches, AS_OF)
        rec = recommend(score, confidence, gaps)

        meter = compute_confidence_meter(matches, rec, AS_OF)
        assert meter.weakest_requirement is None  # no actual matches to compare

    def test_weakest_requirement_is_the_lowest_confidence_non_gap_match(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)
        score = score_match(matches, AS_OF)
        confidence = overall_confidence(matches, candidate, AS_OF)
        gaps = analyze_gaps(matches, AS_OF)
        rec = recommend(score, confidence, gaps)

        meter = compute_confidence_meter(matches, rec, AS_OF)
        # TensorFlow (transferable, ceiling-capped) should be the weakest
        # actual match in this fixture -- much lower confidence than any
        # exact match.
        assert meter.weakest_requirement is not None
        assert meter.weakest_requirement.skill == "TensorFlow"
