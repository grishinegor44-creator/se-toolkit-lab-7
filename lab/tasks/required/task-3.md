# Intent-Based Natural Language Routing

Slash commands work, but real users don't think in `/commands` — they ask questions like "which lab has the worst results?" In this task, you add an LLM-powered intent router: the user types plain text, and the bot figures out what data to fetch and how to answer.

This builds on Lab 6 — same tool use pattern (give the LLM tools, let it decide), but now embedded in a user-facing product instead of a CLI.

## Requirements targeted

- **P1.1** Natural language intent routing — plain text interpreted by LLM
- **P1.2** All 9 backend endpoints wrapped as LLM tools
- **P1.3** Inline keyboard buttons
- **P1.4** Multi-step reasoning (chaining API calls)

## What you will build

An intent router: user message → LLM with tool definitions → API calls → formatted response.

```terminal
$ uv run bot.py --test "which lab has the lowest pass rate?"
Based on the data, Lab 03 has the lowest average pass rate at 62.3%.
- Backend API: 58.1% (145 attempts)
- Security Hardening: 66.5% (132 attempts)
```

## How it works

```
User: "which lab has the worst results?"
  → bot sends message + tool definitions to LLM
  → LLM decides: call get_pass_rates for each lab
  → bot executes the API calls
  → feeds results back to LLM
  → LLM summarizes
  → bot sends response
```

The LLM receives the user's message, a list of tools (your backend endpoints as function schemas), and a system prompt. It responds with tool calls. Your bot executes them, feeds results back, and the LLM produces the final answer.

## Required tools

Define all 9 backend endpoints as LLM tools — this gives the router enough variety for diverse questions:

| Tool                  | Endpoint                                  | LLM description                      |
| --------------------- | ----------------------------------------- | ------------------------------------ |
| `get_items`           | `GET /items/`                             | List of labs and tasks               |
| `get_learners`        | `GET /learners/`                          | Enrolled students and groups         |
| `get_scores`          | `GET /analytics/scores?lab=`              | Score distribution (4 buckets)       |
| `get_pass_rates`      | `GET /analytics/pass-rates?lab=`          | Per-task averages and attempt counts |
| `get_timeline`        | `GET /analytics/timeline?lab=`            | Submissions per day                  |
| `get_groups`          | `GET /analytics/groups?lab=`              | Per-group scores and student counts  |
| `get_top_learners`    | `GET /analytics/top-learners?lab=&limit=` | Top N learners by score              |
| `get_completion_rate` | `GET /analytics/completion-rate?lab=`     | Completion rate percentage           |
| `trigger_sync`        | `POST /pipeline/sync`                     | Refresh data from autochecker        |

Example tool schema:

```python
{
    "type": "function",
    "function": {
        "name": "get_pass_rates",
        "description": "Get per-task average scores and attempt counts for a lab",
        "parameters": {
            "type": "object",
            "properties": {
                "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"}
            },
            "required": ["lab"],
        },
    },
}
```

## Scenarios

**Single API call:**

| Message                         | Behavior                                  |
| ------------------------------- | ----------------------------------------- |
| "what labs are available?"      | `get_items` → list labs                   |
| "show me scores for lab 4"      | `get_pass_rates(lab="lab-04")` → format   |
| "who are the top 5 students?"   | `get_top_learners(limit=5)` → leaderboard |
| "which group is best in lab 3?" | `get_groups(lab="lab-03")` → rank         |

**Multi-step:**

| Message                               | Behavior                                         |
| ------------------------------------- | ------------------------------------------------ |
| "which lab has the lowest pass rate?" | `get_items` → `get_pass_rates` per lab → compare |
| "compare group A and group B"         | `get_groups` → filter → compare                  |

**Fallback:**

| Message  | Behavior                                             |
| -------- | ---------------------------------------------------- |
| "hello"  | Greeting + capabilities hint                         |
| "asdfgh" | "I didn't understand. Here's what I can do..."       |
| "lab 4"  | "What about lab 4? I can show scores, pass rates..." |

## Inline buttons

Add keyboard buttons so users can discover actions without typing. For example, after `/start` show buttons for common queries.

## Verify

### Setup

If you filled in the LLM fields during setup (step 1.10), you're ready. If not, edit `.env.bot.secret` on your VM and set `LLM_API_KEY`, `LLM_API_BASE_URL`, and `LLM_API_MODEL` (see setup step 1.9 for values).

Verify the LLM is reachable before testing the bot:

```terminal
uv run poe query-qwen-code-api \
  --base-url localhost:42005 \
  --api-key YOUR_LLM_API_KEY \
  --model YOUR_MODEL \
  "hi"
```

If this returns JSON with a response — the LLM is working. If it returns an error, fix the LLM connection first.

### Debugging the tool calling loop

The hardest part of this task is the tool calling loop. To see what's happening, add debug logging to your `route()` method using `print(..., file=sys.stderr)`. Since `--test` mode only sends the bot's response to stdout, stderr is your debug channel.

Example of what debug output should look like:

```terminal
$ uv run bot.py --test "what labs are available"
[tool] LLM called: get_items({})                    ← stderr
[tool] Result: 44 items                              ← stderr
[summary] Feeding 1 tool result back to LLM          ← stderr
There are 6 main labs available:                      ← stdout (the actual response)
1. Lab 01 – Products, Architecture & Roles
...
```

For a multi-step query:

```terminal
$ uv run bot.py --test "which lab has the lowest pass rate"
[tool] LLM called: get_items({})                     ← stderr
[tool] Result: 44 items                               ← stderr
[tool] LLM called: get_pass_rates({"lab":"lab-01"})  ← stderr
[tool] Result: 8 tasks                                ← stderr
[tool] LLM called: get_pass_rates({"lab":"lab-02"})  ← stderr
[tool] Result: 4 tasks                                ← stderr
...
[summary] Feeding 7 tool results back to LLM          ← stderr
Based on the data, Lab 02 has the lowest pass rate... ← stdout
```

If you don't see `[tool]` lines — the LLM isn't calling tools. If you see tools called but the answer is wrong — check what data came back.

### Test mode — single-step queries

```terminal
cd ~/se-toolkit-lab-7/bot
uv run bot.py --test "what labs are available"
uv run bot.py --test "show me scores for lab 4"
uv run bot.py --test "who are the top 5 students in lab 4"
uv run bot.py --test "how many students are enrolled"
```

Each should return real data from your backend. Check stderr to confirm the LLM is calling the right tool for each query.

### Test mode — multi-step queries

These require the LLM to call multiple tools and reason across results:

```terminal
uv run bot.py --test "which lab has the lowest pass rate"
uv run bot.py --test "which group is doing best in lab 3"
```

The first query should call `get_items` to get all labs, then `get_pass_rates` for each, then compare. If the LLM only calls `get_items` and stops — your tool result feedback loop isn't working.

### Test mode — fallback and edge cases

```terminal
uv run bot.py --test "asdfgh"                # gibberish — helpful message, not crash
uv run bot.py --test "hello"                 # greeting — friendly response
uv run bot.py --test "lab 4"                 # ambiguous — should clarify what they want
```

### Common problems

| Symptom                                                 | Likely cause                                                                                                                                                           |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| "LLM error: HTTP 401"                                   | Qwen OAuth token expired. Fix: `cd ~/qwen-code-oai-proxy && docker compose restart`. Then test with `curl` again. This is NOT a code bug — tokens expire periodically. |
| LLM returns text instead of calling tools               | System prompt doesn't encourage tool use, or tool descriptions are unclear. Try making descriptions more specific.                                                     |
| LLM calls wrong tool                                    | Tool descriptions are ambiguous. Make them more specific.                                                                                                              |
| LLM calls `get_items` but doesn't continue              | Tool results aren't being fed back to the LLM. Check that your loop appends tool results to the conversation and calls the LLM again.                                  |
| Answer has no data, just "I don't have the information" | Tool results are in the conversation but the LLM isn't reading them. Check the `role: tool` message format matches what the API expects.                               |

> [!TIP]
> **Qwen token expiration.** The Qwen Code OAuth token expires every few hours. When it does, the proxy returns 401 until restarted. This will happen — it's not a bug in your code. Just restart the proxy: `cd ~/qwen-code-oai-proxy && docker compose restart`.

### Deploy and verify in Telegram

```terminal
cd ~/se-toolkit-lab-7 && git pull
cd bot && pkill -f "bot.py" 2>/dev/null; nohup uv run bot.py > bot.log 2>&1 &
```

In Telegram, try:

1. "what labs are available?" — should list labs
2. "show me scores for lab 4" — should show per-task data
3. "which lab has the lowest pass rate" — should name a specific lab with a number
4. "asdfgh" — should get a helpful response, not silence

Check `bot.log` for the debug output — same `[tool]` lines you saw in `--test` mode.

## Acceptance criteria

- [ ] `--test "what labs are available"` returns non-empty answer (at least 20 chars).
- [ ] `--test "which lab has the lowest pass rate"` mentions a specific lab.
- [ ] `--test "asdfgh"` returns a helpful message, no crash.
- [ ] Source code contains keyboard/button setup.
- [ ] Source code defines at least 9 tool/function schemas.
- [ ] The LLM decides which tool to call — no regex or keyword matching in the routing path. After the LLM returns tool calls, results are fed back to the LLM for the final answer.
- [ ] Git workflow followed.
