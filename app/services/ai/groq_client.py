"""
Thin wrapper around the Groq API. Every AI feature (match explanation,
outreach drafts, etc.) calls through this one function — keeps the model
name, error handling, and client setup in one place.
"""
from groq import Groq

from app.config import settings

_client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None

MODEL = "openai/gpt-oss-120b"  # llama-3.3-70b-versatile was deprecated/shut down Aug 2026


def generate(system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str:
    if not _client:
        raise RuntimeError("groq_api_key is not set in .env — AI features need it to run.")

    response = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.4,
        reasoning_effort="low",  # gpt-oss is a reasoning model — low effort leaves more tokens for the actual answer
    )
    content = response.choices[0].message.content
    return content.strip() if content else ""
