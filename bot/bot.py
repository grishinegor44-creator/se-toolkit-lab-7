from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from handlers import route_input


@dataclass
class AppConfig:
    bot_token: str | None
    lms_api_url: str | None
    lms_api_key: str | None
    llm_api_key: str | None


def load_env_file(path: Path, *, overwrite: bool) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if overwrite or key not in os.environ:
            os.environ[key] = value


def load_config() -> AppConfig:
    root = Path(__file__).resolve().parent

    load_env_file(root / ".env.bot.example", overwrite=False)
    load_env_file(root / ".env.bot.secret", overwrite=True)

    return AppConfig(
        bot_token=os.getenv("BOT_TOKEN"),
        lms_api_url=os.getenv("LMS_API_URL"),
        lms_api_key=os.getenv("LMS_API_KEY"),
        llm_api_key=os.getenv("LLM_API_KEY"),
    )


def run_test_mode(text: str) -> int:
    config = load_config()
    response = route_input(text, config)
    print(response)
    return 0


def run_telegram_mode() -> int:
    config = load_config()

    if not config.bot_token:
        print("BOT_TOKEN is required to run Telegram mode.", file=sys.stderr)
        return 1

    try:
        from telegram import Update
        from telegram.ext import (
            Application,
            CommandHandler,
            ContextTypes,
            MessageHandler,
            filters,
        )
    except ImportError:
        print(
            "python-telegram-bot is not installed. Add it to pyproject.toml and run uv sync.",
            file=sys.stderr,
        )
        return 1

    async def reply_with_routed_text(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        forced_text: str | None = None,
    ) -> None:
        incoming_text = forced_text
        if incoming_text is None:
            incoming_text = (
                update.message.text if update.message and update.message.text else ""
            )

        response = route_input(incoming_text, config)

        if update.message:
            await update.message.reply_text(response)

    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await reply_with_routed_text(update, context, "/start")

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await reply_with_routed_text(update, context, "/help")

    async def health_command(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await reply_with_routed_text(update, context, "/health")

    async def labs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await reply_with_routed_text(update, context, "/labs")

    async def scores_command(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        command_text = "/scores"
        if context.args:
            command_text += " " + " ".join(context.args)
        await reply_with_routed_text(update, context, command_text)

    async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await reply_with_routed_text(update, context)

    application = Application.builder().token(config.bot_token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("health", health_command))
    application.add_handler(CommandHandler("labs", labs_command))
    application.add_handler(CommandHandler("scores", scores_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_message)
    )

    application.run_polling()
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Telegram bot entry point")
    parser.add_argument(
        "--test",
        metavar="TEXT",
        help='Run offline test mode, for example: --test "/start"',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.test is not None:
        return run_test_mode(args.test)

    return run_telegram_mode()


if __name__ == "__main__":
    raise SystemExit(main())
