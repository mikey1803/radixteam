"""
Skill Matching — Canonical Skill Taxonomy.

A small, hand-curated taxonomy scoped to what the current demo data
actually needs, per the algorithm design's documented hackathon-scope
decision — deliberately not an attempt at general-purpose coverage.
Extend it by adding a tuple entry; nothing else in normalization.py needs
to change.

Each canonical skill lists every known surface form (its natural spelling
plus true aliases — same underlying skill, different text). These are
NOT semantic/transferable relationships (e.g. Docker~Containers,
PyTorch~TensorFlow) — those describe *different* skills that are related,
and belong to the relationship graph built in Milestone 4, not here.
Getting that distinction wrong here would let unrelated skills silently
merge into one, which is a correctness bug, not a taxonomy gap.

A couple of curation calls worth being explicit about: "js" is included
as a Javascript alias and "node"/"k8s" as shorthand for Node.js/Kubernetes
-- common in real resumes and JDs, but loose enough to be worth a second
look if the taxonomy grows and starts seeing false positives.
"""

from .models import SkillCategory

# canonical_skill_id -> (category, [surface forms, including the natural spelling])
TAXONOMY: dict[str, tuple[SkillCategory, list[str]]] = {
    "python": (SkillCategory.CORE_TECHNICAL, ["python"]),
    "sql": (SkillCategory.CORE_TECHNICAL, ["sql"]),
    "javascript": (SkillCategory.CORE_TECHNICAL, ["javascript", "js"]),
    "fastapi": (SkillCategory.FRAMEWORK, ["fastapi", "fast api"]),
    "django": (SkillCategory.FRAMEWORK, ["django"]),
    "react": (SkillCategory.FRAMEWORK, ["react", "reactjs", "react.js", "react js"]),
    "nodejs": (SkillCategory.FRAMEWORK, ["nodejs", "node.js", "node js", "node"]),
    "pytorch": (SkillCategory.FRAMEWORK, ["pytorch", "py torch", "torch"]),
    "tensorflow": (SkillCategory.FRAMEWORK, ["tensorflow", "tensor flow"]),
    "docker": (SkillCategory.TOOL_PLATFORM, ["docker"]),
    "kubernetes": (SkillCategory.TOOL_PLATFORM, ["kubernetes", "k8s"]),
    "aws": (SkillCategory.TOOL_PLATFORM, ["aws", "amazon web services"]),
    "machine_learning": (SkillCategory.DOMAIN_KNOWLEDGE, ["machine learning"]),
    "communication": (SkillCategory.SOFT_SKILL, ["communication"]),
    "leadership": (SkillCategory.SOFT_SKILL, ["leadership"]),
}
