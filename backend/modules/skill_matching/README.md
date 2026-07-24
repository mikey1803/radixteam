# Skill Matching Module

This module is the candidate-to-job matching engine for the backend. It does not just compare keywords. It runs a staged pipeline that normalizes the input, matches requirements, scores the result, estimates confidence, finds gaps, builds a recommendation, creates an explanation, and adds a small innovation layer for extra insights.

The important design rule is that this module separates three concerns:

1. `schemas.py` defines the public API contract.
2. `service.py` controls the pipeline order.
3. `api.py` turns the internal result into an HTTP response.

That means the module can evolve internally without breaking client code as long as the public schema stays backward compatible.

## What the module is doing

At a high level, the module answers two questions:

1. How well does this candidate match this job?
2. What would happen if the candidate had one extra hypothetical skill?

The main match flow is:

1. Accept raw job and candidate payloads.
2. Adapt those payloads into internal domain models.
3. Validate the combined context.
4. Normalize the data.
5. Reconcile trust signals from Talent Check.
6. Match job requirements to candidate skills.
7. Score the match.
8. Estimate confidence.
9. Detect gaps.
10. Produce a recommendation.
11. Generate an explanation.
12. Compute optional innovation-layer insights.
13. Assemble the internal report.
14. Convert that report into the public API response.

## File roles

### `schemas.py`

This file defines the public request and response shapes.

It is intentionally stable and additive. New fields should be added without removing or renaming existing ones, so downstream teams can integrate early and keep working as the module grows.

### `service.py`

This is the orchestration layer. It decides the execution order of the pipeline and connects the public request contract to the internal domain pipeline.

### `api.py`

This is the HTTP layer. It exposes FastAPI endpoints and wraps the result in the shared `APIResponse` envelope used across the backend.

### `aggregator.py`

This file gathers already-computed results into one internal `MatchReport` object.

### `models.py`, `normalization.py`, `matching.py`, `scoring.py`, `confidence.py`, `gap_analysis.py`, `recommendation.py`, `reasoning.py`

These files hold the real business logic. Each one owns one stage of the pipeline.

### `innovation/`

This folder contains additive features such as interview questions, candidate insights, ATS alignment, confidence meter output, and the what-if simulator.

## Public request contract

### `SkillMatchRequest`

This is the standard request body for a match.

It accepts:

- `job`: raw JD Analytics output
- `candidate`: raw Resume Parser or Profile Builder output
- `talent_check`: optional raw Talent Check output

The request uses `dict[str, Any]` instead of tightly typed upstream schemas because the upstream contracts are still evolving. The adapter layer is the only place that interprets those raw payloads.

### `WhatIfRequest`

This is a separate request type for the what-if endpoint.

It uses the same `job` and `candidate` payloads, but adds:

- `hypothetical_skill`: the extra skill to simulate

It is separate because the input shape is genuinely different, even though it reuses the same engine.

## Public response contract

### `SkillMatchResponse`

This is the main response returned by the match endpoint.

Core fields:

- `schema_version`: version of the public response contract
- `candidate_id`: stable candidate identifier
- `job_id`: stable job identifier
- `overall_score`: match score
- `overall_confidence`: confidence in the match result
- `matched_skills`: resolved requirements that were matched
- `gaps`: unresolved requirements
- `recommendation`: final decision tier
- `explanation`: human-readable summary
- `explanation_source`: whether the explanation came from AI or a template
- `insights`: optional additive innovation-layer output

The fields after `job_id` are intentionally optional in the schema so the contract can exist before every milestone is fully implemented. That lets clients integrate early without waiting for the final version of every stage.

### `WhatIfResponseOut`

This is the response for the what-if endpoint.

It reports:

- the skill that was simulated
- whether that skill was recognized
- baseline score and projected score
- score delta
- baseline confidence and projected confidence
- confidence delta
- how many critical gaps were resolved

## Detailed schema behavior

### `SkillEvidenceOut`

Represents one piece of supporting evidence for a matched skill.

Fields:

- `source_type`: where the evidence came from
- `source_reference`: a pointer or label for the evidence source
- `depth`: how direct or indirect the evidence is
- `verified`: optional trust signal from Talent Check

### `MatchedSkillOut`

Represents one job requirement that was matched to one or more candidate skills.

Fields:

- `skill`: the requirement text as exposed publicly
- `match_type`: how the match was established
- `confidence`: confidence for that match
- `evidence`: list of supporting evidence objects

### `GapOut`

Represents one unresolved requirement.

Fields:

- `skill`: the missing or weak requirement
- `severity`: how important the gap is
- `reason`: optional explanation of why the gap exists

### `RecommendationOut`

Represents the final decision tier from the deterministic recommendation logic.

Fields:

- `tier`: the recommendation category
- `confidence_label`: a human-friendly label for certainty

### `InterviewQuestionOut`

Represents one generated interview question used by the innovation layer.

Fields:

- `question`: the prompt to ask
- `purpose`: why the question exists
- `difficulty`: how hard the question is
- `related_skill`: which skill it targets

### `MatchInsightsOut`

Optional extra insights built from already computed results.

Fields:

- `weakest_matched_skill`: the weakest matched requirement, if any
- `candidate_bonus_skills`: skills that are useful but not required
- `interview_questions`: generated interview questions
- `ats_keyword_match_rate`: keyword overlap score for ATS alignment

This layer is additive only. It does not create new truth; it repackages information that already exists in the pipeline.

## End-to-end flow

### Match endpoint

The match endpoint in `api.py` calls `service.run_match()`.

Inside `service.py`, the pipeline does the following:

1. Builds an internal match context from raw payloads.
2. Validates the context.
3. Applies per-skill trust signals from Talent Check.
4. Normalizes candidate and job data.
5. Matches requirements.
6. Computes per-match confidence values.
7. Scores the overall match.
8. Calculates overall confidence.
9. Detects gaps.
10. Generates a recommendation.
11. Creates an explanation.
12. Computes innovation-layer output.
13. Assembles a `MatchReport`.

Then `api.py` maps that report into `SkillMatchResponse` and returns it inside `APIResponse`.

### What-if endpoint

The what-if endpoint runs a baseline match and a hypothetical match, then compares them.

It answers questions like:

- How much does one extra skill improve the score?
- Does it improve confidence too?
- Which critical gaps disappear?

## Why the architecture is shaped this way

The module is designed this way so that:

- the public contract remains stable
- the pipeline stages stay testable in isolation
- the HTTP layer stays thin
- upstream payload changes can be handled in one adapter
- future milestones can add fields without breaking old clients

The biggest design choice is that the schemas are public, but the real logic stays internal. That keeps the response predictable while still allowing the implementation to evolve.

## Short version

If you want the simplest summary, this module:

- receives a job and a candidate
- normalizes and matches their skills
- scores the fit
- measures confidence and gaps
- recommends a decision tier
- explains the result
- exposes all of that through a stable API schema
