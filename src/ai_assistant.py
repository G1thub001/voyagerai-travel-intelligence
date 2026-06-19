import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

MODEL = "openrouter/free"

TRAVEL_SYSTEM_PROMPT = """
You are a helpful AI travel assistant.
Give concise and useful travel advice.
"""

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def ask(prompt, system_prompt=TRAVEL_SYSTEM_PROMPT):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        max_tokens=500,
    )

    return response.choices[0].message.content