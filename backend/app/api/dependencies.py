"""
Backend API Dependencies.

Shared FastAPI dependency-injection providers used across module routers.
"""

from functools import lru_cache
from typing import Optional

from app.core.ai_provider import AICallError, AIProvider, AnthropicAIProvider


@lru_cache
def get_ai_provider() -> Optional[AIProvider]:
    """
    Resolve the AI provider once per process.

    Returns None if no provider is configured (SDK not installed, or no
    API key set) rather than raising — every AI-dependent code path in
    this codebase already treats a None provider as a valid, expected
    state that triggers graceful template-based fallback, never an error.
    This is what lets the API run correctly with zero AI configuration
    and start using real AI automatically the moment a key is set, with
    no code change.
    """
    try:
        return AnthropicAIProvider()
    except AICallError:
        return None
