# Talent Check Module (STUB — Role 4)

Real (if simple) scoring logic is already wired: a category is a "gap" if
`candidate_level < required_level`; `readiness_score` = % of the 12
categories with no gap.

**Needs from you:**
1. `talent_check_company_skillsets.json` — ask your facilitator, drop it in
   `backend/db/data/`. Shape: `{ "Google": {"DSA": 8, "CLOUD": 6, ...}, ... }`.
   Without it, this stub uses a flat default bar of 6 for every category so
   the endpoint still works end-to-end.
2. A better `candidate_level` estimate than "8 if they have any skill in
   this category else 2" — e.g. weight by confidence, or count of skills
   per category.
