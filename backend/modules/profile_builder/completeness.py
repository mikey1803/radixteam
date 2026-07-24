"""
Profile Builder — Completeness Scoring Engine.

Calculates a profile completeness score (0–100%) based on weighted sections.

Section weights:
    Personal Information  — 20%
    Skills               — 20%
    Education            — 15%
    Experience           — 20%
    Projects             — 15%
    Certifications       —  5%
    Links                —  5%

Profile status mapping:
    0–40%    → Incomplete
    41–70%   → Average
    71–90%   → Good
    91–100%  → Excellent
"""


# Section weights (must sum to 100)
WEIGHTS = {
    "personal_info": 20.0,
    "skills": 20.0,
    "education": 15.0,
    "experience": 20.0,
    "projects": 15.0,
    "certifications": 5.0,
    "links": 5.0,
}


def _score_personal_info(profile: dict) -> float:
    """
    Score personal information section (max 20%).

    5% each for: name, email, phone, location.
    """
    score = 0.0
    if profile.get("name"):
        score += 5.0
    if profile.get("email"):
        score += 5.0
    if profile.get("phone"):
        score += 5.0
    if profile.get("location"):
        score += 5.0
    return score


def _score_skills(profile: dict) -> float:
    """
    Score skills section (max 20%).

    Full score if at least one skill is present.
    """
    skills = profile.get("skills", [])
    if skills and len(skills) > 0:
        return WEIGHTS["skills"]
    return 0.0


def _score_education(profile: dict) -> float:
    """
    Score education section (max 15%).

    Full score if at least one education entry is present.
    """
    education = profile.get("education", [])
    if education and len(education) > 0:
        return WEIGHTS["education"]
    return 0.0


def _score_experience(profile: dict) -> float:
    """
    Score experience section (max 20%).

    Base: 10% if at least one entry exists.
    Detail bonus: up to 10% based on completeness of first entry.
        - Has description: +4%
        - Has technologies: +3%
        - Has start_date/end_date: +3%
    """
    experience = profile.get("experience", [])
    if not experience or len(experience) == 0:
        return 0.0

    score = 10.0  # Base score for having experience

    # Check detail completeness of the first entry
    first = experience[0]
    if isinstance(first, dict):
        if first.get("description"):
            score += 4.0
        if first.get("technologies") and len(first.get("technologies", [])) > 0:
            score += 3.0
        if first.get("start_date") or first.get("end_date"):
            score += 3.0

    return min(score, WEIGHTS["experience"])


def _score_projects(profile: dict) -> float:
    """
    Score projects section (max 15%).

    Full score if at least one project is present.
    """
    projects = profile.get("projects", [])
    if projects and len(projects) > 0:
        return WEIGHTS["projects"]
    return 0.0


def _score_certifications(profile: dict) -> float:
    """
    Score certifications section (max 5%).

    Full score if at least one certification is present.
    """
    certifications = profile.get("certifications", [])
    if certifications and len(certifications) > 0:
        return WEIGHTS["certifications"]
    return 0.0


def _score_links(profile: dict) -> float:
    """
    Score links section (max 5%).

    ~1.67% each for: linkedin, github, portfolio.
    """
    links = profile.get("links", {})
    if not links:
        return 0.0

    score = 0.0
    per_link = WEIGHTS["links"] / 3.0  # ~1.67%

    if links.get("linkedin"):
        score += per_link
    if links.get("github"):
        score += per_link
    if links.get("portfolio"):
        score += per_link

    return round(score, 2)


def calculate_completeness(profile: dict) -> float:
    """
    Calculate the overall profile completeness score (0–100).

    Aggregates weighted scores from all sections.

    Args:
        profile: Dict containing profile data (from ORM .to_dict() or merged data).

    Returns:
        Float between 0.0 and 100.0.
    """
    total = 0.0
    total += _score_personal_info(profile)
    total += _score_skills(profile)
    total += _score_education(profile)
    total += _score_experience(profile)
    total += _score_projects(profile)
    total += _score_certifications(profile)
    total += _score_links(profile)

    return round(min(total, 100.0), 2)


def get_profile_status(score: float) -> str:
    """
    Map a completeness score to a human-readable status.

    Status mapping:
        0–40%    → Incomplete
        41–70%   → Average
        71–90%   → Good
        91–100%  → Excellent
    """
    if score <= 40:
        return "Incomplete"
    elif score <= 70:
        return "Average"
    elif score <= 90:
        return "Good"
    else:
        return "Excellent"
