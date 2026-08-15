from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ROOT / ".env")
    leaseclear_base_url: str
    leaseclear_api_key: str | None = None


settings = Settings()  # pyright: ignore[reportCallIssue]
