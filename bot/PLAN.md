# Bot Development Plan

## Goal

The goal of this task is to prepare a clean and testable foundation for the Telegram bot before implementing full functionality. The bot must support an offline `--test` mode so that command handlers can be executed without a Telegram connection. This will make local verification, CI checks, and debugging much simpler.

## Project structure

The bot will be placed in the `bot/` directory as an isolated Python project. The main entry point will be `bot.py`. Command logic will be stored in `handlers/`, configuration loading in `config.py`, and integrations with external systems in `services/`. This separation is important because handlers should not depend directly on Telegram-specific objects. Instead, they should accept plain input values and return plain text responses.

## Scaffold approach

At the first stage, I will create the minimal working scaffold:

- `bot.py` for startup and CLI test mode;
- `handlers/` for command handlers such as `/start`, `/help`, `/health`, and `/labs`;
- `services/` for LMS API and future LLM integration;
- `config.py` for reading environment variables;
- `pyproject.toml` for dependencies and `uv` support.

Initially, handlers may return placeholder responses, but the architecture must already support reuse in both CLI and Telegram runtime.

## Backend integration

The bot will communicate with the backend through a dedicated service layer. Instead of calling the LMS API directly from handlers, handlers will use service functions or classes. This makes the code easier to test and replace. Configuration such as `LMS_API_URL` and `LMS_API_KEY` will be read from environment files. In test mode, backend calls should fail gracefully and return understandable messages instead of crashing.

## Intent routing

The first routing layer will be command-based: `/start`, `/help`, `/health`, `/labs`, and later `/scores`. The `--test` mode will pass the input string into the same routing logic. In future tasks, this routing can be extended with natural-language intent detection so that inputs like “what labs are available” are mapped to the correct handler. This design avoids duplicated logic between Telegram updates and offline tests.

## Deployment plan

After local verification, the bot will be deployed on the VM in `~/se-toolkit-lab-7/bot`. Dependencies will be installed with `uv sync`. Runtime secrets will be stored in `.env.bot.secret`, while `.env.bot.example` will document required variables. The bot process will be started in the background, and logs will be written to `bot.log` for troubleshooting. After each change, I will verify both `uv run bot.py --test "/start"` and the real Telegram `/start` response.

## Validation

The scaffold is considered ready when:

- `uv sync` completes successfully;
- `uv run bot.py --test "/start"` prints a non-empty response and exits with code 0;
- other basic commands also return text without tracebacks;
- the bot starts correctly on the VM and responds in Telegram.

This plan creates a simple but extensible architecture that supports the current lab requirements and reduces risk for later tasks.
