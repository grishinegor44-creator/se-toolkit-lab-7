from __future__ import annotations
from dataclasses import dataclass


@dataclass
class AppConfig:
    bot_token: str | None
    lms_api_url: str | None
    lms_api_key: str | None
    llm_api_key: str | None
    llm_api_base_url: str | None
    llm_api_model: str | None
