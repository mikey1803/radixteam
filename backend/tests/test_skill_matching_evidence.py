"""
Skill Matching — Milestone 5 Unit Tests (evidence.py).

Covers per-item evidence scoring: source-type weighting, depth
multiplier, recency decay, and verification boost/penalty.
"""

from datetime import date

from modules.skill_matching.evidence import evidence_item_weight, recency_modifier
from modules.skill_matching.models import EvidenceDepth, EvidenceSourceType, SkillEvidence

AS_OF = date(2024, 12, 1)


def _evidence(**overrides) -> SkillEvidence:
    defaults = dict(
        source_type=EvidenceSourceType.PROJECT,
        source_reference="ref",
        depth=EvidenceDepth.DESCRIBED,
    )
    defaults.update(overrides)
    return SkillEvidence(**defaults)


class TestSourceTypeOrdering:
    def test_experience_outweighs_project(self):
        exp = evidence_item_weight(_evidence(source_type=EvidenceSourceType.EXPERIENCE), AS_OF)
        proj = evidence_item_weight(_evidence(source_type=EvidenceSourceType.PROJECT), AS_OF)
        assert exp > proj

    def test_project_outweighs_certification(self):
        proj = evidence_item_weight(_evidence(source_type=EvidenceSourceType.PROJECT), AS_OF)
        cert = evidence_item_weight(_evidence(source_type=EvidenceSourceType.CERTIFICATION), AS_OF)
        assert proj > cert

    def test_certification_outweighs_education(self):
        cert = evidence_item_weight(_evidence(source_type=EvidenceSourceType.CERTIFICATION), AS_OF)
        edu = evidence_item_weight(_evidence(source_type=EvidenceSourceType.EDUCATION), AS_OF)
        assert cert > edu

    def test_education_outweighs_bare_mention(self):
        edu = evidence_item_weight(_evidence(source_type=EvidenceSourceType.EDUCATION), AS_OF)
        bare = evidence_item_weight(_evidence(source_type=EvidenceSourceType.PROFILE_SUMMARY), AS_OF)
        assert edu > bare


class TestDepthOrdering:
    def test_central_outweighs_described(self):
        central = evidence_item_weight(_evidence(depth=EvidenceDepth.CENTRAL), AS_OF)
        described = evidence_item_weight(_evidence(depth=EvidenceDepth.DESCRIBED), AS_OF)
        assert central > described

    def test_described_outweighs_mentioned(self):
        described = evidence_item_weight(_evidence(depth=EvidenceDepth.DESCRIBED), AS_OF)
        mentioned = evidence_item_weight(_evidence(depth=EvidenceDepth.MENTIONED), AS_OF)
        assert described > mentioned


class TestRecencyModifier:
    def test_current_evidence_gets_full_weight(self):
        recent = _evidence(end_date=date(2024, 6, 1))
        assert recency_modifier(recent, AS_OF) == 1.0

    def test_old_evidence_decays_but_never_near_zero(self):
        old = _evidence(end_date=date(2010, 1, 1))
        modifier = recency_modifier(old, AS_OF)
        assert 0 < modifier < 1.0
        assert modifier >= 0.5  # floor -- never a near-hard-exclusion

    def test_older_evidence_decays_more_than_recent_evidence(self):
        recent = _evidence(end_date=date(2023, 1, 1))
        old = _evidence(end_date=date(2012, 1, 1))
        assert recency_modifier(recent, AS_OF) > recency_modifier(old, AS_OF)

    def test_missing_date_is_neutral_not_penalized(self):
        no_date = _evidence()
        old = _evidence(end_date=date(2010, 1, 1))
        modifier = recency_modifier(no_date, AS_OF)
        assert modifier > recency_modifier(old, AS_OF)

    def test_ongoing_evidence_uses_start_date_when_no_end_date(self):
        ongoing = _evidence(start_date=date(2023, 1, 1), end_date=None)
        assert recency_modifier(ongoing, AS_OF) == 1.0


class TestVerification:
    def test_verified_true_boosts_weight(self):
        base = _evidence(verified=None)
        verified = _evidence(verified=True)
        assert evidence_item_weight(verified, AS_OF) > evidence_item_weight(base, AS_OF)

    def test_verified_false_penalizes_weight(self):
        base = _evidence(verified=None)
        unverified = _evidence(verified=False)
        assert evidence_item_weight(unverified, AS_OF) < evidence_item_weight(base, AS_OF)

    def test_unknown_verification_does_not_change_weight(self):
        # verified=None must be neutral: absence of verification is never
        # treated as evidence of dishonesty.
        base_weight = evidence_item_weight(_evidence(verified=None), AS_OF)
        assert 0 < base_weight <= 1.0

    def test_weight_is_clamped_to_one_even_with_boost(self):
        strong = _evidence(
            source_type=EvidenceSourceType.EXPERIENCE,
            depth=EvidenceDepth.CENTRAL,
            end_date=date(2024, 6, 1),
            verified=True,
        )
        assert evidence_item_weight(strong, AS_OF) == 1.0
