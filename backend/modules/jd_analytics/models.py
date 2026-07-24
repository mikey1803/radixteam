"""
Persistence-shape reference for the 'jobs' table (JSON-file backed today).
Kept for parity with the Chapter 4.4 folder structure; if/when this module
moves to a real Postgres table via SQLAlchemy, the ORM model goes here and
repository.py swaps its JSONTable calls for session queries — service.py
does not change.
"""

JOB_RECORD_SHAPE = {
    "id": "uuid",
    "filename": "str",
    "extracted": "ExtractedSkillList (see app/shared/schemas/skill.py)",
}
