"""
AI Provider Abstraction — per Chapter 2.10 / 4.16.

Nobody in the codebase calls Gemini or Groq directly. Everyone depends only
on AIProvider.complete_json(prompt). Today it defaults to MOCK mode so the
whole team can build and integrate without needing real API keys. Flip
AI_PROVIDER_MODE in .env to "gemini" or "groq" once keys are available —
no service-layer code changes needed.

    AIProvider
        |
    ----+----
    |       |
  Gemini   Groq   (auto-retries Groq if Gemini fails)
    |
  Mock (default — deterministic, offline, good for demos/tests)
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from abc import ABC, abstractmethod

from app.shared.exceptions import AIErrorApp

logger = logging.getLogger("radix.ai_provider")


class BaseAIClient(ABC):
    @abstractmethod
    def complete_json(self, prompt: str) -> dict:
        ...


class MockAIClient(BaseAIClient):
    """
    Deterministic offline stand-in for a real LLM. Uses light keyword
    heuristics so JD Analytics / Resume Parsing still produce *plausible*
    structured output without hitting a network. Swap this out once real
    keys are wired up — the service layer doesn't know the difference.
    """

    CATEGORY_KEYWORDS = {
        "DSA": ["data structure", "algorithm", "leetcode", "dsa"],
        "COD": ["coding", "programming", "python", "java", "c++", "golang", "javascript"],
        "OOD": ["object oriented", "design pattern", "oop", "solid principles"],
        "APTI": ["aptitude", "reasoning", "quantitative", "logical"],
        "COMM": ["communication", "stakeholder", "presentation", "collaborat"],
        "AI": ["machine learning", "ml", "ai", "tensorflow", "pytorch", "llm", "nlp", "deep learning"],
        "CLOUD": ["aws", "azure", "gcp", "cloud", "kubernetes", "docker", "terraform"],
        "SQL": ["sql", "postgres", "mysql", "database", "mongodb", "query"],
        "SWE": ["ci/cd", "testing", "git", "agile", "software engineering", "code review"],
        "SYSD": ["system design", "scalability", "architecture", "microservices", "distributed"],
        "NETW": ["networking", "tcp", "dns", "http", "load balancer"],
        "OS": ["operating system", "linux", "unix", "memory management", "threading"],
    }

    def complete_json(self, prompt: str) -> dict:
        text = _extract_source_text(prompt).lower()

        found_skills = []
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    found_skills.append({
                        "skill_name": kw.title(),
                        "category_code": category,
                        "evidence": _find_sentence_with(text, kw),
                        "confidence": "medium",
                    })
                    break  # one hit per category is enough for the mock

        if not found_skills:
            found_skills.append({
                "skill_name": "General Software Development",
                "category_code": "OTHER",
                "evidence": "No strong category keywords detected by mock AI",
                "confidence": "low",
            })

        title_match = re.search(r"(software engineer|data scientist|data analyst|"
                                 r"support analyst|associate software engineer)", text)

        return {
            "title": title_match.group(1).title() if title_match else "Unknown Role",
            "experience": "Not confidently extracted (mock provider)",
            "education": "Not confidently extracted (mock provider)",
            "skills": found_skills,
            "responsibilities": [],
            "technologies": [s["skill_name"] for s in found_skills],
            "soft_skills": ["Communication"] if "communicat" in text else [],
            "industry": "Technology",
        }


def _extract_source_text(prompt: str) -> str:
    marker = "TEXT TO ANALYZE:"
    if marker in prompt:
        return prompt.split(marker, 1)[1]
    return prompt


def _find_sentence_with(text: str, keyword: str) -> str:
    idx = text.find(keyword)
    if idx == -1:
        return keyword
    start = max(0, idx - 40)
    end = min(len(text), idx + 60)
    snippet = text[start:end].strip().replace("\n", " ")
    return f"...{snippet}..."


class GeminiAIClient(BaseAIClient):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def complete_json(self, prompt: str) -> dict:
        try:
            import google.generativeai as genai  # lazy import, optional dep
        except ImportError as e:
            raise AIErrorApp("google-generativeai package not installed") from e

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return _parse_json_response(response.text)


class GroqAIClient(BaseAIClient):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def complete_json(self, prompt: str) -> dict:
        try:
            from groq import Groq  # lazy import, optional dep
        except ImportError as e:
            raise AIErrorApp("groq package not installed") from e

        client = Groq(api_key=self.api_key)
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )
        return _parse_json_response(completion.choices[0].message.content)


def _parse_json_response(raw_text: str) -> dict:
    cleaned = re.sub(r"^```json|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise AIErrorApp("AI returned invalid JSON", errors=[str(e)]) from e


class AIProvider:
    """
    Single entry point every service layer should call:
        AIProvider().complete_json(prompt)

    Mode is controlled by AI_PROVIDER_MODE env var: "mock" (default),
    "gemini", or "groq". If Gemini fails and a Groq key is present, it
    automatically retries with Groq per Chapter 4.16.
    """

    def __init__(self):
        self.mode = os.getenv("AI_PROVIDER_MODE", "mock").lower()
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")

    def complete_json(self, prompt: str) -> dict:
        start = time.time()
        model_used = "mock"
        try:
            if self.mode == "gemini" and self.gemini_key:
                model_used = "gemini"
                result = GeminiAIClient(self.gemini_key).complete_json(prompt)
            elif self.mode == "groq" and self.groq_key:
                model_used = "groq"
                result = GroqAIClient(self.groq_key).complete_json(prompt)
            else:
                result = MockAIClient().complete_json(prompt)
        except AIErrorApp:
            if self.mode == "gemini" and self.groq_key:
                logger.warning("Gemini failed, retrying with Groq")
                model_used = "groq (fallback)"
                result = GroqAIClient(self.groq_key).complete_json(prompt)
            else:
                logger.warning("AI call failed, falling back to mock")
                model_used = "mock (fallback)"
                result = MockAIClient().complete_json(prompt)

        latency_ms = round((time.time() - start) * 1000, 1)
        logger.info(f"AI call complete | model_used={model_used} | latency_ms={latency_ms}")
        return result
