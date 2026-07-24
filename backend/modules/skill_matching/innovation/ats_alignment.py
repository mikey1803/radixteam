"""
Skill Matching — ATS Keyword Alignment.

A narrowly-scoped feature per the intelligence design's own scoping
decision: does this specific JD's literal skill text appear, verbatim, in
the candidate's listed skills? This simulates what a naive keyword-
scanning ATS would see, in deliberate contrast to this module's actual
matching (canonical/alias resolution, transferable evidence) — showing a
recruiter exactly where the smarter engine found real signal that a
naive keyword scanner would have missed entirely.

Deliberately NOT a general resume-formatting or completeness audit — that
would duplicate Profile Builder's territory (its own completeness
scoring) and drift outside "skill matching for this JD" into a different
module's job, exactly the anti-pattern flagged in the accepted analysis.
This only ever compares this job's literal skill strings against this
candidate's literal skill strings — a matching-module question, not a
resume-quality one.
"""

from pydantic import BaseModel, Field

from ..models import Candidate, Job
from ..normalization import normalize_text


class ATSAlignment(BaseModel):
    """How a naive literal-keyword-scanning ATS would read this candidate against this JD."""

    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    keyword_match_rate: float = 0.0


def compute_ats_alignment(candidate: Candidate, job: Job) -> ATSAlignment:
    """
    Compares literal skill text only — no canonical/alias/transferable
    resolution — to simulate what a naive keyword-matching ATS would see.
    A skill this module resolves via transferable evidence (e.g. PyTorch
    covering a TensorFlow requirement) will still show as "missing" here,
    which is the point: it's the exact contrast that demonstrates this
    module isn't just keyword matching.
    """
    candidate_texts = {normalize_text(skill.raw_text) for skill in candidate.skills}

    matched = [s.raw_text for s in job.skills if normalize_text(s.raw_text) in candidate_texts]
    missing = [s.raw_text for s in job.skills if normalize_text(s.raw_text) not in candidate_texts]

    match_rate = len(matched) / len(job.skills) if job.skills else 0.0

    return ATSAlignment(matched_keywords=matched, missing_keywords=missing, keyword_match_rate=match_rate)
