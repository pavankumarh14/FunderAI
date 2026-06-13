from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM provider selection: "azure" | "openai" | "gemini" | "grok"
    llm_provider: str = "azure"

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-02-01"
    azure_openai_chat_deployment: str = "gpt-4o"

    # OpenAI
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o"

    # Gemini
    gemini_api_key: str = ""
    gemini_chat_model: str = "gemini-1.5-pro"

    # X.AI Grok
    grok_api_key: str = ""
    grok_chat_model: str = "grok-2-latest"

    # App
    app_env: str = "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
