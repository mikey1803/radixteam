"""
Skill Matching — Tunable Constants.

Every weight, ceiling, and threshold used by the deterministic engine
lives here, named and in one place, rather than scattered as inline magic
numbers through evidence.py / confidence.py (and, from Milestone 6 onward,
scoring.py / gap_analysis.py / recommendation.py too).

Every value below is a reasoned starting point, not data calibrated
against real hiring outcomes yet — see the algorithm design's Future
Calibration section. That is a deliberate, honest position for this
stage: the formulas these constants feed are fixed and auditable
regardless of what these specific numbers are, and recalibrating later
means changing values here, never the shape of the computation.
"""

from .matching import MatchType
from .models import EvidenceDepth, EvidenceSourceType, RequirementLevel, SkillCategory

# ─── Evidence scoring ─────────────────────────────────────────────────────

SOURCE_TYPE_WEIGHT: dict[EvidenceSourceType, float] = {
    EvidenceSourceType.EXPERIENCE: 1.0,
    EvidenceSourceType.PROJECT: 0.85,
    EvidenceSourceType.HACKATHON: 0.7,
    EvidenceSourceType.CERTIFICATION: 0.65,
    EvidenceSourceType.EDUCATION: 0.45,
    EvidenceSourceType.RESUME_TEXT: 0.35,
    EvidenceSourceType.PROFILE_SUMMARY: 0.25,
}

DEPTH_MULTIPLIER: dict[EvidenceDepth, float] = {
    EvidenceDepth.CENTRAL: 1.0,
    EvidenceDepth.DESCRIBED: 0.85,
    EvidenceDepth.MENTIONED: 0.6,
}

# Discrete recency buckets (years since the evidence's most recent relevant
# date). Deliberately coarse and deliberately never near-zero, even for old
# evidence -- an aggressive decay risks penalizing candidates with career
# gaps or older-but-still-valid experience (a fairness risk flagged in the
# algorithm design's critique). Missing date info is treated as neutral,
# not as a penalty -- an adapter that couldn't parse a date shouldn't read
# the same as genuinely stale evidence.
RECENCY_NO_DATE_WEIGHT = 0.8
RECENCY_CURRENT_YEARS = 2
RECENCY_CURRENT_WEIGHT = 1.0
RECENCY_RECENT_YEARS = 5
RECENCY_RECENT_WEIGHT = 0.85
RECENCY_AGING_YEARS = 8
RECENCY_AGING_WEIGHT = 0.65
RECENCY_OLD_WEIGHT = 0.5  # floor for anything older than RECENCY_AGING_YEARS

VERIFIED_BOOST = 1.2
UNVERIFIED_PENALTY = 0.5  # only applied when Talent Check explicitly returns verified=False
CONFLICT_PENALTY = 0.6  # applied when evidence for one skill disagrees on verification status

# ─── Confidence aggregation ───────────────────────────────────────────────

MATCH_TYPE_CEILING: dict[MatchType, float] = {
    MatchType.EXACT: 1.0,
    MatchType.TRANSFERABLE: 0.75,
    MatchType.ADJACENT: 0.5,
    MatchType.NONE: 0.0,
}

REQUIREMENT_LEVEL_WEIGHT: dict[RequirementLevel, float] = {
    RequirementLevel.REQUIRED: 1.0,
    RequirementLevel.PREFERRED: 0.4,
}

CATEGORY_WEIGHT: dict[SkillCategory, float] = {
    SkillCategory.CORE_TECHNICAL: 1.0,
    SkillCategory.FRAMEWORK: 0.85,
    SkillCategory.TOOL_PLATFORM: 0.8,
    SkillCategory.DOMAIN_KNOWLEDGE: 0.75,
    SkillCategory.CERTIFICATION_COMPLIANCE: 0.7,
    SkillCategory.SOFT_SKILL: 0.6,
    SkillCategory.UNKNOWN: 0.5,
}

# How strongly Overall Confidence is biased toward the weakest requirement
# rather than the criticality-weighted mean (see confidence.py). 1.0 would
# be a pure minimum; 0.0 would be a plain weighted average.
OVERALL_CONFIDENCE_MIN_BIAS = 0.7

# ─── Scoring ──────────────────────────────────────────────────────────────

# How much required-skill coverage dominates the overall score over
# preferred-skill coverage when both are present. Required skills should
# dominate by a wide, deliberate margin (algorithm design §4) -- a JD with
# several required skills and a couple of preferred ones shouldn't let
# strong preferred-skill matches paper over a required-skill gap.
REQUIRED_DOMINANCE_WEIGHT = 0.8

# Additional per-match-type dampening applied ONLY to the score's per-
# requirement contribution -- NOT to confidence.py's MATCH_TYPE_CEILING,
# which answers a different question (how much do we trust this evidence)
# than scoring does (how much should this count toward the requirement).
# Adjacent matches are deliberately suppressed further here: letting an
# adjacent relationship meaningfully move the numeric score would
# reproduce the "score inflation with no calibration" failure mode the
# algorithm design explicitly warns against -- adjacent matches should
# soften gap severity and explanation framing, not meaningfully raise the
# score. Combined with MATCH_TYPE_CEILING, an adjacent match can never
# contribute more than MATCH_TYPE_CEILING[ADJACENT] * 0.4 to a score, even
# with perfect underlying evidence.
SCORE_CONTRIBUTION_MULTIPLIER: dict[MatchType, float] = {
    MatchType.EXACT: 1.0,
    MatchType.TRANSFERABLE: 1.0,
    MatchType.ADJACENT: 0.4,
    MatchType.NONE: 1.0,  # irrelevant -- requirement_confidence is already 0 for NONE
}

# ─── Gap severity ─────────────────────────────────────────────────────────

# Minimum requirement_confidence (confidence.py -- the UNDAMPENED value,
# not scoring.py's further-dampened score contribution) for transferable/
# adjacent evidence to be treated as genuinely mitigating a gap, softening
# its severity by one tier. Set so the Docker/Kubernetes worked example
# from the AI reasoning design (a required Docker gap, mitigated by
# certification-level Kubernetes evidence, computing to ~0.39 requirement
# confidence) correctly crosses into Moderate as that walkthrough commits
# to -- weak or merely-adjacent evidence generally should not cross it.
GAP_MITIGATION_FLOOR = 0.35

# Categories where a REQUIRED-but-unmet skill is treated one tier less
# severely than the default (Moderate instead of Critical), and a
# PREFERRED-but-unmet skill is treated as Nice-to-Have even without strong
# mitigating evidence. Soft skills are typically assessed through
# interview/other signals rather than structured resume evidence, so their
# absence from structured data is less informative than for a required
# technology or certification.
GAP_SEVERITY_SOFTENING_CATEGORIES: frozenset[SkillCategory] = frozenset({SkillCategory.SOFT_SKILL})

# ─── Recommendation ───────────────────────────────────────────────────────

# Below this overall_score, there isn't enough genuine overlap for any tier
# above Low Match / Needs Upskilling to be honest, regardless of gap count.
MEANINGFUL_OVERLAP_SCORE_FLOOR = 0.3

RECOMMENDATION_SCORE_HIGH = 0.75
RECOMMENDATION_SCORE_MODERATE = 0.5

# Reused for both tier-gating (does this score/gap profile qualify for
# Strong/Good Match) and for labeling overall_confidence as High/Moderate/
# Low for display -- the same underlying claim about what counts as
# trustworthy either way.
RECOMMENDATION_CONFIDENCE_HIGH = 0.7
RECOMMENDATION_CONFIDENCE_REASONABLE = 0.5

# "Several" moderate gaps, per the algorithm design's Potential Match
# definition ("moderate score, no critical gaps but several moderate
# ones") -- at or above this count, a moderate-score match is downgraded
# from Good Match to Potential Match even with reasonable confidence.
SEVERAL_MODERATE_GAPS_THRESHOLD = 3

# ─── AI reasoning ─────────────────────────────────────────────────────────

# Low temperature: explanations should be consistent framings of fixed
# facts, not creative writing. Short timeout: a slow AI call must never
# be allowed to dominate the request's latency budget -- the deterministic
# result is always available regardless of what the AI call does.
AI_EXPLANATION_TEMPERATURE = 0.2
AI_EXPLANATION_TIMEOUT_SECONDS = 8.0
AI_RELATIONSHIP_TEMPERATURE = 0.1  # even more deterministic -- this is a classification, not prose
AI_RELATIONSHIP_TIMEOUT_SECONDS = 6.0

# ─── Interview Intelligence ───────────────────────────────────────────────

# Below this skill_confidence, an EXACT match's evidence is "weak enough"
# to warrant an evidence-depth-verification interview question at all.
INTERVIEW_EVIDENCE_QUESTION_THRESHOLD = 0.6

# Within that weak range (and for a transferability-verification question's
# related-skill evidence), confidence at or above this counts as "some real
# signal" worth a harder, PROBING question; below it, start FOUNDATIONAL.
INTERVIEW_STRONG_EVIDENCE_THRESHOLD = 0.35
