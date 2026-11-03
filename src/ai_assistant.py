
import os

from dotenv import load_dotenv
from openai import OpenAI


MODEL = "openrouter/free"

TRAVEL_SYSTEM_PROMPT = """
You are a helpful AI travel assistant.
Give concise and useful travel advice.
"""

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def get_client() -> OpenAI:
    """Create an OpenRouter client using the configured API key."""
    load_dotenv()

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured. "
            "Add it to your local .env file before making AI requests."
        )

    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
    )


def ask(
    prompt: str,
    system_prompt: str = TRAVEL_SYSTEM_PROMPT,
    client: OpenAI | None = None,
) -> str:
    """Send a prompt to the configured AI model."""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    active_client = client or get_client()

    response = active_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        max_tokens=500,
        timeout=30,
    )

    answer = response.choices[0].message.content

    if not answer:
        raise RuntimeError("The AI model returned an empty response.")

    return answer
