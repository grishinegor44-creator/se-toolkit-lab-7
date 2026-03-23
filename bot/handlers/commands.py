from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import AppConfig


def handle_start(_: "AppConfig", __: str) -> str:
    return "Welcome to the LMS bot scaffold!\nUse /help to see available commands."


def handle_help(_: "AppConfig", __: str) -> str:
    return (
        "Available commands:\n"
        "/start - show welcome message\n"
        "/help - show this help\n"
        "/health - check bot configuration status\n"
        "/labs - list available labs\n"
        "/scores - show lab scores (placeholder)"
    )


def handle_health(config: "AppConfig", __: str) -> str:
    lms_status = (
        "configured" if config.lms_api_url and config.lms_api_key else "not configured"
    )
    llm_status = "configured" if config.llm_api_key else "not configured"
    return f"Bot status: OK\nLMS API: {lms_status}\nLLM API: {llm_status}"


def handle_labs(_: "AppConfig", __: str) -> str:
    return "Labs list is not implemented yet."


def handle_scores(_: "AppConfig", text: str) -> str:
    parts = text.split(maxsplit=1)
    if len(parts) == 1:
        return "Usage: /scores <lab-id>"

    lab_id = parts[1].strip()
    if not lab_id:
        return "Usage: /scores <lab-id>"

    return f"Scores for '{lab_id}' are not implemented yet."


def handle_natural_language(_: "AppConfig", text: str) -> str:
    return f"Natural-language routing is not implemented yet: {text}"


def handle_unknown(_: "AppConfig", text: str) -> str:
    return f"Unknown command: {text}\nUse /help to see supported commands."


def route_input(text: str, config: "AppConfig") -> str:
    normalized = (text or "").strip()

    if not normalized:
        return "Empty input. Use /start or /help."

    if normalized.startswith("/"):
        command = normalized.split()[0].lower()

        if command == "/start":
            return handle_start(config, normalized)
        if command == "/help":
            return handle_help(config, normalized)
        if command == "/health":
            return handle_health(config, normalized)
        if command == "/labs":
            return handle_labs(config, normalized)
        if command == "/scores":
            return handle_scores(config, normalized)

        return handle_unknown(config, normalized)

    return handle_natural_language(config, normalized)
