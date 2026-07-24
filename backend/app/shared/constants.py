"""
Shared constants used across every module.
Nobody duplicates this — import from here.
"""

# The 12 RADIX skill categories (+ OTHER catch-all), per the hackathon brief.
CATEGORY_CODES = [
    "DSA",    # Data Structures & Algorithms
    "COD",    # Coding
    "OOD",    # Object-Oriented Design
    "APTI",   # Aptitude
    "COMM",   # Communication
    "AI",     # AI / ML
    "CLOUD",  # Cloud
    "SQL",    # SQL / Databases
    "SWE",    # Software Engineering practices
    "SYSD",   # System Design
    "NETW",   # Networking
    "OS",     # Operating Systems
    "OTHER",  # Anything that doesn't map cleanly
]

CONFIDENCE_LEVELS = ["high", "medium", "low"]

# Skill name normalization map — extend as you encounter new variants.
SKILL_MAPPING = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "java script": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "node js": "Node.js",
    "py": "Python",
    "python3": "Python",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "psql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "docker": "Docker",
    "aws": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "azure": "Azure",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "fastapi": "FastAPI",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "scikit learn": "Scikit-learn",
    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
}

MAX_UPLOAD_SIZE_MB = 10
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
