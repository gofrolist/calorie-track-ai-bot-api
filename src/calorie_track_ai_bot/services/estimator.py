import json
from typing import Any

from openai import OpenAI

from .config import OPENAI_API_KEY, OPENAI_MODEL

if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY must be set")

client = OpenAI(api_key=OPENAI_API_KEY)

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
            },
        },
    },
    "required": ["kcal_mean", "kcal_min", "kcal_max", "confidence", "items"],
}


async def estimate_from_image_url(image_url: str) -> dict[str, Any]:
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
