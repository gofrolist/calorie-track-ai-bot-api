import json
from typing import Any

from openai import OpenAI

from .config import APP_ENV, OPENAI_API_KEY, OPENAI_MODEL

# Initialize OpenAI client only if configuration is available
client: OpenAI | None = None

if OPENAI_API_KEY is not None:
    client = OpenAI(api_key=OPENAI_API_KEY)
elif APP_ENV == "dev":
    # In development mode, allow missing OpenAI config
    print("WARNING: OpenAI configuration not set. AI estimation functionality will be disabled.")
    print("To enable AI estimation, set the following environment variable:")
    print("- OPENAI_API_KEY")
else:
    raise ValueError("OPENAI_API_KEY must be set")

SCHEMA = {
    "type": "object",
    "properties": {
        "kcal_mean": {"type": "number"},
        "kcal_min": {"type": "number"},
        "kcal_max": {"type": "number"},
        "confidence": {"type": "number"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "kcal": {"type": "number"},
                    "confidence": {"type": "number"},
                },
                "required": ["label", "kcal", "confidence"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["kcal_mean", "kcal_min", "kcal_max", "confidence", "items"],
    "additionalProperties": False,
}


async def estimate_from_image_url(image_url: str) -> dict[str, Any]:
    if client is None:
        raise RuntimeError(
            "OpenAI configuration not available. AI estimation functionality is disabled."
        )

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Estimate meal calories. Return structured JSON."},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "Estimate", "schema": SCHEMA, "strict": True},
        },
    )
    content = resp.choices[0].message.content
    if content is None:
        raise ValueError("No content returned from OpenAI")
    return json.loads(content)
