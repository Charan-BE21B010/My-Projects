from __future__ import annotations

import json
import re
from typing import Any, Optional

from importer_engine.config import Settings, get_settings


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


class LLMClient:
    """Thin wrapper around OpenAI or Gemini. Returns plain text."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.provider = self.settings.resolve_provider()

    @property
    def available(self) -> bool:
        return self.provider != "none"

    def complete(self, system: str, user: str, temperature: float = 0.2) -> str:
        if self.provider == "openai":
            return self._openai(system, user, temperature)
        if self.provider == "gemini":
            return self._gemini(system, user, temperature)
        raise RuntimeError("No LLM API key configured")

    def complete_json(self, system: str, user: str, temperature: float = 0.1) -> Any:
        raw = self.complete(system, user + "\n\nRespond with valid JSON only.", temperature)
        return json.loads(_strip_fences(raw))

    def _openai(self, system: str, user: str, temperature: float) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key)
        resp = client.chat.completions.create(
            model=self.settings.openai_model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (resp.choices[0].message.content or "").strip()

    def _gemini(self, system: str, user: str, temperature: float) -> str:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError(
                "GEMINI_API_KEY is set but google-generativeai is not installed. "
                "Run: pip install google-generativeai"
            ) from exc

        genai.configure(api_key=self.settings.gemini_api_key)
        model = genai.GenerativeModel(
            self.settings.gemini_model,
            system_instruction=system,
        )
        resp = model.generate_content(
            user,
            generation_config={"temperature": temperature},
        )
        return (resp.text or "").strip()
