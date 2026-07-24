"""
Skill Matching — Curated Skill Relationship Graph.

Tier 1 of the semantic matching design (intelligence doc §2): a small,
hand-verified table of relationships between DIFFERENT canonical skills.
This lets the matching engine recognize that a candidate lacking a
required skill outright may still have credible, quantifiable evidence
toward it via a related skill they DO have — without ever calling an LLM
for well-known relationships. AI-assisted discovery for pairs *not* in
this graph is Tier 2, built in Milestone 9, not here.

Distinct from taxonomy.py's aliases: an alias is a different SPELLING of
the SAME skill (ReactJS = React); a relationship here connects two
DIFFERENT skills (PyTorch is not TensorFlow, but experience with one
transfers partially to the other). Confusing the two would let unrelated
skills silently merge, which normalization.py is specifically designed
to prevent.

RelationshipType.TRANSFERABLE — strong conceptual/domain overlap; the
possessed skill covers most of what the required skill actually tests
for:
  - pytorch <-> tensorflow: both deep learning frameworks, sharing the
    core concepts of tensors, autograd, and training loops — the API
    surface differs, the underlying competency mostly doesn't. This is
    the flagship example used throughout the design docs.
  - docker <-> kubernetes: containerization concepts (images, isolation,
    the container runtime model) transfer meaningfully into understanding
    orchestration, even though the tools solve different problems. This
    is the same pairing used in the AI reasoning design's worked example
    ("candidate demonstrates container concepts through Kubernetes
    coursework, reducing onboarding risk") — kept consistent with that
    walkthrough rather than reclassified here.

RelationshipType.ADJACENT — same ecosystem, weaker overlap, real ramp-up
still expected:
  - django <-> fastapi: both Python web frameworks, but different enough
    in design philosophy (sync/ORM-heavy vs. async/schema-first) that the
    overlap is real without being a close substitute.

base_confidence is a prior for that specific pair, not a final score —
scoring.py (Milestone 6) combines it with the candidate's actual evidence
strength for the possessed skill. These are reasoned starting points, not
calibrated data — the same "documented default, refine later" discipline
used for every other constant in this module (see Future Calibration in
the algorithm design). Deliberately kept small: a curated graph this size
is reviewable by a human in minutes; padding it with speculative pairs
(e.g. "React relates to Node.js because both are JavaScript") would
reintroduce exactly the curator-bias risk the design docs flag.
"""

from enum import Enum
from typing import Optional


class RelationshipType(str, Enum):
    TRANSFERABLE = "transferable"
    ADJACENT = "adjacent"


# Stored once per unordered pair; queried symmetrically (A relates to B the
# same way B relates to A). If a pair is ever found to genuinely be
# asymmetric, that needs an explicit modeling decision, not a workaround here.
RELATIONSHIP_GRAPH: dict[frozenset[str], tuple[RelationshipType, float]] = {
    frozenset({"pytorch", "tensorflow"}): (RelationshipType.TRANSFERABLE, 0.7),
    frozenset({"docker", "kubernetes"}): (RelationshipType.TRANSFERABLE, 0.6),
    frozenset({"django", "fastapi"}): (RelationshipType.ADJACENT, 0.5),
}


def get_relationship(skill_a: str, skill_b: str) -> Optional[tuple[RelationshipType, float]]:
    """Look up the curated relationship between two canonical skill IDs, if any."""
    if skill_a == skill_b:
        return None
    return RELATIONSHIP_GRAPH.get(frozenset({skill_a, skill_b}))
