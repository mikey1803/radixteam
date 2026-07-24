# Skill Matching Module (STUB — Role 5)

Real fuzzy matching is already wired: substring + `difflib.SequenceMatcher`
similarity (threshold 0.75), no AI call required to work standalone.

**Role 5 owner, if you have time:** replace `_skills_match` with an
`AIProvider().complete_json(...)` call for genuine semantic matching (e.g.
"Postgres" JD skill vs "Relational Databases" candidate skill) — same
AIProvider used by JD Analytics, so no new plumbing needed.
