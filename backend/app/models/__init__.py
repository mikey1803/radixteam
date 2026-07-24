"""
Models package — import all models here so Base.metadata knows about them.
"""

from app.models.candidate import Candidate
from app.models.job_description import JobDescription
from app.models.talent_check_result import TalentCheckResult

__all__ = ["Candidate", "JobDescription", "TalentCheckResult"]
