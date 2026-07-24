"""LLM-based structured extraction from raw resume text.

Supports both OpenAI-compatible APIs and Google Gemini.
Falls back to rule-based extraction when no LLM is available.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from shared.logging import get_logger

logger = get_logger(__name__)

PARSER_VERSION = "1.0.0"

EXTRACTION_PROMPT = """\
You are an expert resume parser. Extract structured data from the following resume text.

Return ONLY a valid JSON object with these fields (use null for missing, [] for empty arrays):

personal_info: object with first_name, last_name, email (REQUIRED), phone, location, headline
summary: string or null
education: array of objects with institution, degree, field_of_study, start_date, end_date, gpa
experience: array of objects with company, title, location, start_date, end_date, description, highlights (array of strings)
skills: array of objects with name, category, proficiency
projects: array of objects with name, description, url, technologies (array), highlights (array)
certifications: array of objects with name, issuer, date_obtained, expiry_date, url
links: array of objects with label, url

Rules:
- first_name, last_name, email are REQUIRED
- Normalize dates to YYYY-MM format
- Infer skill category and proficiency from context
- Return ONLY the JSON object, no markdown, no explanation, NO template placeholders

Resume text:
{resume_text}
"""


def _extract_json_from_response(content: str) -> dict[str, Any]:
    """Parse JSON from LLM response, handling markdown code blocks."""
    content = content.strip()
    if content.startswith("```"):
        # Remove markdown code blocks
        parts = content.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{") or part.startswith("["):
                content = part
                break
        else:
            content = parts[-1] if len(parts) > 1 else content
    return json.loads(content)


async def _extract_with_openai(
    raw_text: str,
    model: str,
    api_key: str,
    base_url: str | None,
) -> dict[str, Any] | None:
    """Attempt extraction using OpenAI-compatible API."""
    try:
        from openai import AsyncOpenAI
        from openai import (
            APIError,
            APIConnectionError,
            AuthenticationError,
            BadRequestError,
            RateLimitError,
        )

        client_kwargs: dict = {"api_key": api_key.strip()}
        if base_url:
            client_kwargs["base_url"] = base_url.strip()

        client = AsyncOpenAI(**client_kwargs)
        prompt = EXTRACTION_PROMPT.format(resume_text=raw_text[:8000])

        # Try with JSON mode first, fallback if not supported
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise resume parser. Output only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
        except BadRequestError as e:
            if "response_format" in str(e).lower() or "json_object" in str(e).lower():
                logger.warning(
                    "Model does not support JSON mode, retrying without response_format",
                    model=model,
                )
                response = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a precise resume parser. Output only valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.0,
                )
            else:
                raise

        content = response.choices[0].message.content or "{}"
        data = _extract_json_from_response(content)

        logger.info(
            "OpenAI extraction completed successfully",
            model=model,
            sections=list(data.keys()),
        )
        return data

    except AuthenticationError as exc:
        logger.error(
            "OpenAI API authentication failed - check your OPENAI_API_KEY",
            error=str(exc),
            api_key_prefix=api_key[:10] + "..." if api_key else "None",
        )
        return None

    except RateLimitError as exc:
        error_msg = str(exc)
        if "insufficient_quota" in error_msg.lower() or "quota" in error_msg.lower():
            logger.warning(
                "OpenAI API quota exceeded - will try Gemini if available",
                error=error_msg,
            )
        else:
            logger.warning(
                "OpenAI API rate limit exceeded - will try Gemini if available",
                error=error_msg,
            )
        return None  # Signal to try next provider

    except APIConnectionError as exc:
        logger.error(
            "Failed to connect to OpenAI API - will try Gemini if available",
            error=str(exc),
        )
        return None

    except (BadRequestError, APIError) as exc:
        logger.error(
            "OpenAI API error - will try Gemini if available",
            error=str(exc),
            model=model,
        )
        return None

    except json.JSONDecodeError as exc:
        logger.error(
            "Failed to parse OpenAI response as JSON",
            error=str(exc),
        )
        return None

    except Exception as exc:
        logger.error(
            "Unexpected error during OpenAI extraction",
            error=str(exc),
            error_type=type(exc).__name__,
        )
        return None


async def _extract_with_gemini(
    raw_text: str,
    model: str,
    api_key: str,
) -> dict[str, Any] | None:
    """Attempt extraction using Google Gemini API via direct REST call
    (run in a thread executor to avoid blocking the event loop)."""
    prompt = EXTRACTION_PROMPT.format(resume_text=raw_text[:8000])

    def _sync_call() -> dict[str, Any] | None:
        """Synchronous REST call to Gemini."""
        import json as _json
        import urllib.request
        import urllib.error

        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={api_key.strip()}"
            )

            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": (
                                    "You are a precise resume parser. "
                                    "Output only valid JSON."
                                )
                            },
                        ],
                    },
                    {
                        "role": "user",
                        "parts": [{"text": prompt}],
                    },
                ],
                "generationConfig": {
                    "temperature": 0.0,
                },
            }

            body = _json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=120) as resp:
                response_data = _json.loads(resp.read())

            # Extract text from response
            candidates = response_data.get("candidates", [])
            if not candidates:
                logger.error("Gemini returned no candidates", raw=json.dumps(response_data)[:500])
                return None

            content = (
                candidates[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "{}")
            )

            # Try to parse JSON, with detailed logging on failure
            try:
                return _extract_json_from_response(content)
            except json.JSONDecodeError as json_err:
                logger.error(
                    "Failed to parse Gemini JSON response",
                    error=str(json_err),
                    raw_preview=content[:300],
                )
                return None

        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            error_str = error_body.lower()
            if exc.code == 429 or "quota" in error_str or "rate" in error_str:
                logger.warning(
                    "Gemini API quota/rate limit exceeded",
                    error=error_body[:300],
                )
            else:
                logger.error(
                    "Gemini API HTTP error",
                    status_code=exc.code,
                    response=error_body[:300],
                )
            return None

        except Exception as exc:
            error_str = str(exc).lower()
            if "quota" in error_str or "rate" in error_str or "429" in error_str:
                logger.warning(
                    "Gemini API quota/rate limit exceeded",
                    error=str(exc),
                )
            else:
                logger.error(
                    "Gemini API error",
                    error=str(exc),
                    error_type=type(exc).__name__,
                )
            return None

    # Run synchronous REST call in thread executor to not block the async loop
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, _sync_call)

    if result is not None:
        logger.info(
            "Gemini extraction completed successfully",
            model=model,
            sections=list(result.keys()),
        )

    return result


async def extract_structured_data(
    raw_text: str,
    ai_model: str | None = None,
) -> dict:
    """Send raw resume text to an LLM and return structured data.

    Tries providers in order:
    1. OpenAI-compatible (if OPENAI_API_KEY is set)
    2. Google Gemini (if GEMINI_API_KEY is set)
    3. Falls back to rule-based extraction if no LLM is available.
    """
    openai_model = ai_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # ── Try OpenAI ────────────────────────────────────────────────
    if openai_api_key and openai_api_key.strip():
        logger.info("Attempting OpenAI extraction", model=openai_model)
        result = await _extract_with_openai(
            raw_text, openai_model, openai_api_key, openai_base_url
        )
        if result is not None:
            return result
        logger.info("OpenAI extraction failed or unavailable, checking next provider")

    # ── Try Gemini ────────────────────────────────────────────────
    if gemini_api_key and gemini_api_key.strip():
        logger.info("Attempting Gemini extraction", model=gemini_model)
        result = await _extract_with_gemini(raw_text, gemini_model, gemini_api_key)
        if result is not None:
            return result
        logger.info("Gemini extraction failed or unavailable")

    # ── Fall back to rules ────────────────────────────────────────
    logger.warning(
        "No LLM available - using rule-based fallback extraction. "
        "Set OPENAI_API_KEY or GEMINI_API_KEY in .env to enable AI-powered parsing."
    )
    return _rule_based_extract(raw_text)


def _rule_based_extract(text: str) -> dict:
    """Fallback rule-based extraction when no LLM is available.

    Produces a basic structured result from heuristic parsing.
    """
    import re

    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    # ── Email ────────────────────────────────────────────────────
    email_match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    email = email_match.group(0) if email_match else "unknown@unknown.com"

    # ── Phone ────────────────────────────────────────────────────
    phone_match = re.search(r"\+?\d[\d\s\-\(\)]{7,15}", text)
    phone = phone_match.group(0).strip() if phone_match else None

    # ── Name (first meaningful line that isn't email/phone/section) ──
    first_name = "Unknown"
    last_name = "Candidate"
    for line in lines[:5]:
        clean = re.sub(r"[^\w\s]", "", line).strip()
        if not clean or len(clean) < 2:
            continue
        if "@" in clean or re.match(r"^\d", clean):
            continue
        if clean.upper() in {"RESUME", "CURRICULUM VITAE", "CV"}:
            continue
        words = clean.split()
        if len(words) >= 2:
            first_name = words[0]
            last_name = words[-1]
            break
        elif len(words) == 1:
            first_name = words[0]
            break

    # ── Section detection ────────────────────────────────────────
    section_keywords = {
        "experience": ["experience", "work history", "employment"],
        "education": ["education", "academic"],
        "skills": ["skills", "competencies", "technologies"],
        "projects": ["projects", "portfolio"],
        "certifications": ["certifications", "certificates", "licenses"],
    }

    sections: dict[str, list[str]] = {k: [] for k in section_keywords}
    current_section: str | None = None

    for line in lines:
        lower = line.lower().strip()
        matched = False
        for section_key, keywords in section_keywords.items():
            if any(kw in lower for kw in keywords) and len(line) < 40:
                current_section = section_key
                matched = True
                break
        if not matched and current_section:
            sections[current_section].append(line)

    # ── Skills ───────────────────────────────────────────────────
    skills: list[dict] = []
    for line in sections.get("skills", []):
        parts = re.split(r"[,•·|/]", line)
        for part in parts:
            skill = part.strip()
            if skill and len(skill) < 50:
                skills.append({"name": skill, "category": None, "proficiency": None})

    # ── Experience ───────────────────────────────────────────────
    experience: list[dict] = []
    for line in sections.get("experience", [])[:10]:
        if re.search(r"\b(at|@|–|-|present)\b", line, re.IGNORECASE):
            experience.append({
                "company": line,
                "title": "Unknown",
                "location": None,
                "start_date": None,
                "end_date": None,
                "description": None,
                "highlights": [],
            })

    # ── Education ────────────────────────────────────────────────
    education: list[dict] = []
    for line in sections.get("education", [])[:5]:
        education.append({
            "institution": line,
            "degree": None,
            "field_of_study": None,
            "start_date": None,
            "end_date": None,
            "gpa": None,
        })

    # ── Links ────────────────────────────────────────────────────
    links: list[dict] = []
    url_pattern = re.compile(r"https?://[^\s]+")
    for match in url_pattern.finditer(text):
        url = match.group(0).rstrip(".,;)")
        label = "Link"
        if "linkedin" in url.lower():
            label = "LinkedIn"
        elif "github" in url.lower():
            label = "GitHub"
        links.append({"label": label, "url": url})

    # ── Location (heuristic) ─────────────────────────────────────
    location = None
    location_match = re.search(
        r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z]{2})\b", text
    )
    if location_match:
        location = location_match.group(0)

    return {
        "personal_info": {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "location": location,
            "headline": None,
        },
        "summary": None,
        "education": education,
        "experience": experience,
        "skills": skills,
        "projects": [],
        "certifications": [],
        "links": links,
    }