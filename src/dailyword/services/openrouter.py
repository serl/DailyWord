import json
import logging
from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class OpenRouterError(Exception):
    """Exception raised for OpenRouter API errors."""

    pass


@dataclass
class WordDefinition:
    """Generated word definition from AI."""

    word: str
    definition: str
    example_sentence: str
    pronunciation: str
    part_of_speech: str


class OpenRouterService:
    """
    Service for interacting with OpenRouter API.

    Supports both text generation (for word definitions) and image generation.
    """

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        if not self.api_key:
            raise OpenRouterError(
                "OpenRouter API key not configured. Set OPENROUTER_API_KEY in settings."
            )

    def _make_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Make a request to the OpenRouter API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(self.BASE_URL, json=payload, headers=headers)

        if response.status_code != 200:
            raise OpenRouterError(
                f"OpenRouter API error ({response.status_code}): {response.text}"
            )

        return response.json()

    def generate_word_list(
        self,
        prompt: str,
        count: int = 10,
    ) -> list[WordDefinition]:
        """
        Generate a list of words with definitions for a given prompt.

        Returns:
            List of WordDefinition objects
        """

        prompt = f"""Generate {count} {prompt}.

For each word, provide:
- word: the vocabulary word (lowercase if not a proper noun)
- definition: a clear, concise definition
- example_sentence: a sentence using the word naturally
- pronunciation: phonetic pronunciation
- part_of_speech: noun, verb, adjective, etc.

Return a JSON object with a "words" array containing these objects.
Return ONLY the JSON object, no markdown or other formatting."""

        payload = {
            "model": settings.OPENROUTER_TEXT_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "response_format": {"type": "json_object"},
        }

        response = self._make_request(payload)

        try:
            content = response["choices"][0]["message"]["content"]
            data = json.loads(content)
            words = data.get("words", [])
            return [
                WordDefinition(
                    word=w["word"],
                    definition=w["definition"],
                    example_sentence=w.get("example_sentence", ""),
                    pronunciation=w.get("pronunciation", ""),
                    part_of_speech=w.get("part_of_speech", ""),
                )
                for w in words
            ]
        except (KeyError, json.JSONDecodeError) as e:
            raise OpenRouterError(f"Failed to parse AI response: {e}") from e
