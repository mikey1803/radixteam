"""
Profile Builder — Normalization Utilities.

Handles data normalization for locations, degrees, and auto-generation
of professional summaries.
"""

import uuid
import re


# ─── Location Normalization Map ─────────────────────────────────────────

LOCATION_MAP: dict[str, str] = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "b'lore": "Bengaluru",
    "blore": "Bengaluru",
    "bombay": "Mumbai",
    "mumbai": "Mumbai",
    "madras": "Chennai",
    "chennai": "Chennai",
    "calcutta": "Kolkata",
    "kolkata": "Kolkata",
    "trivandrum": "Thiruvananthapuram",
    "thiruvananthapuram": "Thiruvananthapuram",
    "cochin": "Kochi",
    "kochi": "Kochi",
    "pune": "Pune",
    "hyderabad": "Hyderabad",
    "delhi": "New Delhi",
    "new delhi": "New Delhi",
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",
    "noida": "Noida",
}


# ─── Degree Normalization Map ───────────────────────────────────────────

DEGREE_MAP: dict[str, str] = {
    "be": "Bachelor of Engineering",
    "b.e": "Bachelor of Engineering",
    "b.e.": "Bachelor of Engineering",
    "bachelor of engineering": "Bachelor of Engineering",
    "btech": "Bachelor of Technology",
    "b.tech": "Bachelor of Technology",
    "b.tech.": "Bachelor of Technology",
    "bachelor of technology": "Bachelor of Technology",
    "bsc": "Bachelor of Science",
    "b.sc": "Bachelor of Science",
    "b.sc.": "Bachelor of Science",
    "bachelor of science": "Bachelor of Science",
    "bca": "Bachelor of Computer Applications",
    "b.c.a": "Bachelor of Computer Applications",
    "bachelor of computer applications": "Bachelor of Computer Applications",
    "mca": "Master of Computer Applications",
    "m.c.a": "Master of Computer Applications",
    "master of computer applications": "Master of Computer Applications",
    "me": "Master of Engineering",
    "m.e": "Master of Engineering",
    "m.e.": "Master of Engineering",
    "master of engineering": "Master of Engineering",
    "mtech": "Master of Technology",
    "m.tech": "Master of Technology",
    "m.tech.": "Master of Technology",
    "master of technology": "Master of Technology",
    "msc": "Master of Science",
    "m.sc": "Master of Science",
    "m.sc.": "Master of Science",
    "master of science": "Master of Science",
    "mba": "Master of Business Administration",
    "m.b.a": "Master of Business Administration",
    "master of business administration": "Master of Business Administration",
    "phd": "Doctor of Philosophy",
    "ph.d": "Doctor of Philosophy",
    "ph.d.": "Doctor of Philosophy",
    "doctor of philosophy": "Doctor of Philosophy",
    "diploma": "Diploma",
    "hsc": "Higher Secondary Certificate",
    "sslc": "Secondary School Leaving Certificate",
}


def normalize_location(location: str) -> str:
    """
    Normalize a location string to its canonical form.

    Examples:
        Bangalore → Bengaluru
        B'lore   → Bengaluru
        Bombay   → Mumbai
    """
    if not location:
        return location

    key = location.strip().lower()
    return LOCATION_MAP.get(key, location.strip())


def normalize_degree(degree: str) -> str:
    """
    Normalize a degree string to its full canonical form.

    Examples:
        BE            → Bachelor of Engineering
        B.Tech        → Bachelor of Technology
        M.Sc.         → Master of Science
    """
    if not degree:
        return degree

    key = degree.strip().lower().rstrip(".")
    # Try exact match first, then with trailing dot
    result = DEGREE_MAP.get(key) or DEGREE_MAP.get(key + ".")
    return result if result else degree.strip()


def generate_summary(profile_data: dict) -> str:
    """
    Auto-generate a professional summary (max 150 words) from profile data.

    Uses skills, education, and experience to create a concise summary.
    Only generated when the resume lacks one.

    Example output:
        "Computer Science student with strong experience in Python, FastAPI,
         Docker, PostgreSQL and AI-powered application development. Interested
         in backend engineering and cloud-native software."
    """
    parts: list[str] = []

    # Extract education context
    education = profile_data.get("education", [])
    if education:
        latest = education[0]
        field = latest.get("field_of_study", "")
        degree = latest.get("degree", "")
        if field:
            parts.append(f"{field} graduate")
        elif degree:
            parts.append(f"{degree} graduate")

    # Extract experience context
    experience = profile_data.get("experience", [])
    if experience:
        years = len(experience)
        latest_title = experience[0].get("title", "")
        if latest_title:
            parts.append(
                f"with experience as {latest_title}"
                + (f" across {years} roles" if years > 1 else "")
            )

    # Extract skills context
    skills = profile_data.get("skills", [])
    if skills:
        # Show up to 8 skills
        skill_list = skills[:8]
        if len(skills) > 8:
            skill_str = ", ".join(skill_list) + f", and {len(skills) - 8} more technologies"
        else:
            skill_str = ", ".join(skill_list[:-1]) + f" and {skill_list[-1]}" if len(skill_list) > 1 else skill_list[0]
        parts.append(f"with strong proficiency in {skill_str}")

    # Extract projects context
    projects = profile_data.get("projects", [])
    if projects:
        parts.append(
            f"having built {len(projects)} project{'s' if len(projects) > 1 else ''}"
        )

    # Assemble summary
    if not parts:
        return "Experienced professional seeking new opportunities."

    summary = " ".join(parts) + "."

    # Capitalize first letter
    summary = summary[0].upper() + summary[1:]

    # Enforce 150-word limit
    words = summary.split()
    if len(words) > 150:
        summary = " ".join(words[:150]) + "."

    return summary


def generate_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())
