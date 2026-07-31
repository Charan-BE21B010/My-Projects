from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    llm_provider: str = "auto"
    max_enrich_requests: int = 20
    request_timeout_seconds: int = 20
    user_agent: str = (
        "ImporterDiscoveryBot/1.0 (+research; respectful crawl; contact via README)"
    )

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key.strip())

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key.strip())

    @property
    def has_llm(self) -> bool:
        return self.has_openai or self.has_gemini

    def resolve_provider(self) -> str:
        pref = self.llm_provider.strip().lower()
        if pref == "openai" and self.has_openai:
            return "openai"
        if pref == "gemini" and self.has_gemini:
            return "gemini"
        if self.has_openai:
            return "openai"
        if self.has_gemini:
            return "gemini"
        return "none"


@lru_cache
def get_settings() -> Settings:
    # Also accept GOOGLE_API_KEY as Gemini alias
    if not os.getenv("GEMINI_API_KEY") and os.getenv("GOOGLE_API_KEY"):
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
    return Settings()