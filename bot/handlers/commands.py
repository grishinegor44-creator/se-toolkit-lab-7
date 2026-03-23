from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from config import AppConfig


# ──────────────────────────────────────────────
# Backend HTTP helpers
# ──────────────────────────────────────────────


def _get(config: "AppConfig", path: str, params: dict | None = None) -> list | dict:
    url = (config.lms_api_url or "http://localhost:42002").rstrip("/") + path
    headers = {"Authorization": f"Bearer {config.lms_api_key}"}
    resp = httpx.get(url, headers=headers, params=params, timeout=10.0)
    resp.raise_for_status()
    return resp.json()


def _post(config: "AppConfig", path: str, body: dict | None = None) -> list | dict:
    url = (config.lms_api_url or "http://localhost:42002").rstrip("/") + path
    headers = {"Authorization": f"Bearer {config.lms_api_key}"}
    resp = httpx.post(url, headers=headers, json=body or {}, timeout=10.0)
    resp.raise_for_status()
    return resp.json()


def _fmt_error(e: Exception, url: str) -> str:
    if isinstance(e, httpx.ConnectError):
        return f"Backend error: connection refused ({url}). Check that the services are running."
    if isinstance(e, httpx.HTTPStatusError):
        return (
            f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}."
        )
    return f"Backend error: {e}."


def _execute_tool(config: "AppConfig", name: str, args: dict) -> object:
    """Execute a named tool and return a JSON-serializable result."""
    try:
        if name == "get_items":
            return _get(config, "/items/")
        if name == "get_learners":
            return _get(config, "/learners/")
        if name == "get_scores":
            return _get(
                config, "/analytics/scores", params={"lab": args.get("lab", "")}
            )
        if name == "get_pass_rates":
            return _get(
                config, "/analytics/pass-rates", params={"lab": args.get("lab", "")}
            )
        if name == "get_timeline":
            return _get(
                config, "/analytics/timeline", params={"lab": args.get("lab", "")}
            )
        if name == "get_groups":
            return _get(
                config, "/analytics/groups", params={"lab": args.get("lab", "")}
            )
        if name == "get_top_learners":
            params: dict = {}
            if "lab" in args:
                params["lab"] = args["lab"]
            if "limit" in args:
                params["limit"] = args["limit"]
            return _get(config, "/analytics/top-learners", params=params)
        if name == "get_completion_rate":
            return _get(
                config,
                "/analytics/completion-rate",
                params={"lab": args.get("lab", "")},
            )
        if name == "trigger_sync":
            return _post(config, "/pipeline/sync")
        return {"error": f"Unknown tool: {name}"}
    except Exception as e:
        return {"error": str(e)}


# ──────────────────────────────────────────────
# LLM tool schemas  (9 endpoints)
# ──────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_items",
            "description": "Get the complete list of labs and tasks available in the LMS",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_learners",
            "description": "Get the list of enrolled students and their group assignments",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_scores",
            "description": "Get score distribution across grade buckets for a specific lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01'",
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pass_rates",
            "description": "Get per-task average scores and attempt counts for a specific lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01'",
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_timeline",
            "description": "Get the number of submissions per day for a specific lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01'",
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_groups",
            "description": "Get per-group average scores and student counts for a specific lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01'",
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_learners",
            "description": "Get the top N learners ranked by score for a specific lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01'. Omit to query globally.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "How many top learners to return (default 10)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_completion_rate",
            "description": "Get the overall completion rate percentage for a specific lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01'",
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_sync",
            "description": "Trigger a data refresh/sync from the autochecker to update all analytics",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

SYSTEM_PROMPT = (
    "You are a helpful LMS assistant bot for a university lab course. "
    "Use the provided tools to answer questions about labs, learners, scores, and analytics. "
    "Always call the appropriate tools — never guess data. "
    "For questions comparing multiple labs (e.g. 'which lab has the lowest pass rate'), "
    "first call get_items to discover all lab IDs, then call the relevant tool for each lab, "
    "then compare the results. "
    "If the user says hello or sends gibberish, respond politely and list what you can do. "
    "Format responses with bullet points and numbers where useful."
)


# ──────────────────────────────────────────────
# LLM tool-calling loop
# ──────────────────────────────────────────────


def handle_natural_language(config: "AppConfig", text: str) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        return (
            "LLM routing requires the 'openai' package.\n"
            "Add it to pyproject.toml and run: uv sync"
        )

    if not config.llm_api_key:
        return (
            "LLM is not configured. Set LLM_API_KEY in .env.bot.secret.\n"
            "Use /help to see available slash commands."
        )

    client = OpenAI(
        api_key=config.llm_api_key,
        base_url=(config.llm_api_base_url or "http://localhost:42005/v1"),
    )
    model = config.llm_api_model or "qwen"

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]

    for _iteration in range(15):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
        except Exception as e:
            err = str(e)
            if "401" in err:
                return (
                    "LLM error: authentication failed (HTTP 401).\n"
                    "Restart the Qwen proxy:\n"
                    "  cd ~/qwen-code-oai-proxy && docker compose restart"
                )
            return f"LLM error: {e}"

        choice = response.choices[0]

        # Append assistant turn (must include tool_calls if present)
        assistant_msg: dict = {"role": "assistant", "content": choice.message.content}
        if choice.message.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in choice.message.tool_calls
            ]
        messages.append(assistant_msg)

        # No tool calls → final answer
        if choice.finish_reason != "tool_calls" or not choice.message.tool_calls:
            return choice.message.content or "I couldn't generate a response."

        # Execute every tool call and feed results back
        print(
            f"[summary] Feeding {len(choice.message.tool_calls)} tool result(s) back to LLM",
            file=sys.stderr,
        )
        for tc in choice.message.tool_calls:
            func_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            print(f"[tool] LLM called: {func_name}({args})", file=sys.stderr)
            result = _execute_tool(config, func_name, args)
            result_str = json.dumps(result)
            print(f"[tool] Result: {len(result_str)} chars", file=sys.stderr)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str,
                }
            )

    return "Sorry, I couldn't complete the request after multiple reasoning steps."


# ──────────────────────────────────────────────
# Slash command handlers
# ──────────────────────────────────────────────


def handle_start(_: "AppConfig", __: str) -> str:
    return (
        "👋 Welcome to LMS Bot!\n\n"
        "I can answer questions in plain language — no commands needed.\n\n"
        "Try asking:\n"
        "  • what labs are available?\n"
        "  • which lab has the lowest pass rate?\n"
        "  • who are the top 5 students?\n"
        "  • show scores for lab 4\n\n"
        "Use the buttons below to get started, or just type any question.\n"
        "/help — see all slash commands"
    )


def handle_help(_: "AppConfig", __: str) -> str:
    return (
        "Slash commands:\n"
        "  /start  — welcome message\n"
        "  /help   — this help\n"
        "  /health — check backend status\n"
        "  /labs   — list all available labs\n"
        "  /scores <lab-id> — per-task pass rates\n\n"
        "Or type any question in plain text:\n"
        "  • which lab has the worst results?\n"
        "  • compare groups in lab 3\n"
        "  • who are the top 10 students in lab 2?"
    )


def handle_health(config: "AppConfig", __: str) -> str:
    base_url = (config.lms_api_url or "http://localhost:42002").rstrip("/")
    try:
        items = _get(config, "/items/")
        return f"✅ Backend is healthy. {len(items)} items available."
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
            lines.append(f"  • {lab_id} — {name}")
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
            lines.append(f"  • {name}: {rate_pct:.1f}% ({attempts} attempts)")
        return "\n".join(lines)
    except Exception as e:
        return _fmt_error(e, base_url)


def handle_unknown(_: "AppConfig", text: str) -> str:
    return f"Unknown command: {text}\nUse /help to see supported commands."


# ──────────────────────────────────────────────
# Main router
# ──────────────────────────────────────────────


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
