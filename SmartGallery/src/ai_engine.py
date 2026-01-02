"""AI integration for image analysis.

Provides a mock response when heavy models are unavailable and a live path for
calling an Ollama endpoint when enabled. Designed to fail gracefully so the UI
remains responsive on mobile devices.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, Dict

import requests

from .config import settings

MOCK_RESPONSE: dict[str, Any] = {
    "description": "[DEV] A placeholder description of a cat.",
    "tags": ["test", "cat", "1girl", "indoors"],
    "nsfw": False,
}


class AIEngine:
    """Encapsulates AI calls and mock fallbacks."""

    def __init__(self, use_real_ai: bool | None = None) -> None:
        self.use_real_ai = settings.use_real_ai if use_real_ai is None else use_real_ai

    def analyze_image(self, image_path: Path) -> Dict[str, Any]:
        """Return analysis data for an image path.

        If mock mode is enabled, the response is instantaneous. When the real
        AI endpoint is enabled, errors are caught and converted into a safe
        placeholder response so the UI never crashes.
        """

        if not self.use_real_ai:
            return MOCK_RESPONSE

        try:
            encoded = self._encode_image(image_path)
        except OSError:
            return {**MOCK_RESPONSE, "description": "[DEV] Unable to read image."}

        payload = {
            "model": "joy-caption-alpha-two",
            "prompt": settings.system_prompt,
            "stream": False,
            "options": {"temperature": 0.2},
            "input": {"image": encoded},
        }

        try:
            response = requests.post(settings.ollama_api_url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            parsed = self._parse_ai_response(data)
            return parsed or MOCK_RESPONSE
        except requests.RequestException:
            return {**MOCK_RESPONSE, "description": "[DEV] AI service unreachable."}
        except (json.JSONDecodeError, KeyError, TypeError):
            return {**MOCK_RESPONSE, "description": "[DEV] Unexpected AI response."}

    def _encode_image(self, image_path: Path) -> str:
        content = image_path.read_bytes()
        return base64.b64encode(content).decode("utf-8")

    def _parse_ai_response(self, response_data: Dict[str, Any]) -> Dict[str, Any] | None:
        """Extract structured data from the Ollama JSON response."""

        # Ollama's generate endpoint returns a flat object with a "response" field
        # containing text. We expect JSON in that field when the model is
        # configured for JSON mode.
        text = response_data.get("response")
        if not isinstance(text, str):
            return None

        try:
            parsed = json.loads(text)
            description = parsed.get("description") or parsed.get("caption")
            tags = parsed.get("tags") or []
            return {
                "description": description or MOCK_RESPONSE["description"],
                "tags": tags if isinstance(tags, list) else MOCK_RESPONSE["tags"],
                "nsfw": bool(parsed.get("nsfw", False)),
            }
        except json.JSONDecodeError:
            return None
