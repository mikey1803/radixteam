"""
Skill Matching — Domain Validators.

Domain-level validation beyond Pydantic's type validation, applied to the
internal models (models.py) produced by adapters.py. Raises the shared
ValidationError (app.shared.exceptions) for genuinely invalid input, so
the same global exception handler wired up in Milestone 12 converts it to
the standard APIResponse error shape.

Deliberately narrow scope: per the algorithm design's edge-case handling,
a sparse or even empty candidate profile is valid input — it degrades
confidence downstream, it is never rejected here. An empty job (zero
skill requirements of any kind) is the one genuinely invalid case: a
score against zero requirements is undefined, not perfect, so it is
rejected rather than silently producing a fabricated 100% match.
"""

from app.shared.exceptions import ValidationError

from .models import Job, MatchContext


def validate_job(job: Job) -> None:
    """Reject a job with no skill requirements at all (required or preferred)."""
    if not job.skills:
        raise ValidationError(
            "Job has no skill requirements to match against.",
            errors=[f"job_id={job.job_id!r} has zero required and preferred skills"],
        )


def validate_match_context(context: MatchContext) -> None:
    """
    Validate a fully-adapted MatchContext before it enters the pipeline.

    No candidate-side check is applied here by design — a sparse or empty
    candidate profile is valid input (see module docstring); only the job
    side has a genuinely invalid state at this layer.
    """
    validate_job(context.job)
