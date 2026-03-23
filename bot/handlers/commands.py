from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from config import AppConfig


def _get(config: "AppConfig", path: str, params: dict | None = None) -> list | dict:
    url = (config.lms_api_url or "http://localhost:42002").rstrip("/") + path
    headers = {"Authorization": f"Bearer {config.lms_api_key}"}
    resp = httpx.get(url, headers=headers, params=params, timeout=5.0)
    resp.raise_for_status()
    return resp.json()


def _fmt_error(e: Exception, url: str) -> str:
    if isinstance(e, httpx.ConnectError):
        return f"Backend error: connection refused ({url}). Check that the services are running."
    if isinstance(e, httpx.HTTPStatusError):
        return f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down."
    return f"Backend error: {e}."


def handle_start(_: "AppConfig", __: str) -> str:
    return "Welcome to LMS Bot!\nUse /help to see available commands."


def handle_help(_: "AppConfig", __: str) -> str:
    return (
        "Available commands:\n"
        "/start   — show welcome message\n"
        "/help    — show this help\n"
        "/health  — check backend status\n"
        "/labs    — list available labs\n"
        "/scores <lab-id>  — show per-task pass rates for a lab"
    )


def handle_health(config: "AppConfig", __: str) -> str:
    base_url = (config.lms_api_url or "http://localhost:42002").rstrip("/")
    try:
        items = _get(config, "/items/")
        return f"Backend is healthy. {len(items)} items available."
    except Exception as e:
        return _fmt_error(e, base_url)


def handle_labs(config: "AppConfig", __: str) -> str:
    base_url = (config.lms_api_url or "http://localhost:42002").rstrip("/")
    try:
        items = _get(config, "/items/")
        labs = [item for item in items if item.get("type") == "lab"]
        if not labs:
            return "No labs found in the backend."
        lines = ["Available labs:"]
        for lab in labs:
            lab_id = lab.get("id", "?")
            name = lab.get("name") or lab.get("title", "Unnamed")
            lines.append(f"- {lab_id} — {name}")
        return "\n".join(lines)
    except Exception as e:
        return _fmt_error(e, base_url)


def handle_scores(config: "AppConfig", text: str) -> str:
    parts = text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return "Usage: /scores <lab-id>  (e.g. /scores lab-04)"
    lab_id = parts[1].strip()
    base_url = (config.lms_api_url or "http://localhost:42002").rstrip("/")
    try:
        data = _get(config, "/analytics/pass-rates", params={"lab": lab_id})
        if not data:
            return f"No scores found for '{lab_id}'. The lab ID may not exist."
        lines = [f"Pass rates for {lab_id}:"]
        for task in data:
            name = (
                task.get("task_name")
                or task.get("task")
                or task.get("name", "Unknown task")
            )
            rate = task.get("pass_rate") or task.get("rate") or 0.0
            rate_pct = rate * 100 if rate <= 1.0 else rate
            attempts = task.get("attempts") or task.get("total_attempts", "?")
            lines.append(f"- {name}: {rate_pct:.1f}% ({attempts} attempts)")
        return "\n".join(lines)
    except Exception as e:
        return _fmt_error(e, base_url)


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
