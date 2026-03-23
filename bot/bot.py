from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import argparse
import os

from config import AppConfig
from handlers import route_input


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
        lms_api_url=os.getenv("LMS_API_URL", "http://localhost:42002"),
        lms_api_key=os.getenv("LMS_API_KEY"),
        llm_api_key=os.getenv("LLM_API_KEY"),
        llm_api_base_url=os.getenv("LLM_API_BASE_URL", "http://localhost:42005/v1"),
        llm_api_model=os.getenv("LLM_API_MODEL", "qwen"),
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
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
        from telegram.ext import (
            Application,
            CallbackQueryHandler,
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

    def _make_start_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📚 Available labs", callback_data="what labs are available?"
                    ),
                    InlineKeyboardButton(
                        "👥 Enrolled students",
                        callback_data="how many students are enrolled?",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🏆 Top 5 students", callback_data="who are the top 5 students?"
                    ),
                    InlineKeyboardButton(
                        "📉 Lowest pass rate",
                        callback_data="which lab has the lowest pass rate?",
                    ),
                ],
                [
                    InlineKeyboardButton("🔄 Sync data", callback_data="sync the data"),
                    InlineKeyboardButton("❓ Help", callback_data="/help"),
                ],
            ]
        )

    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        response = route_input("/start", config)
        if update.message:
            await update.message.reply_text(
                response, reply_markup=_make_start_keyboard()
            )

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            await update.message.reply_text(route_input("/help", config))

    async def health_command(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if update.message:
            await update.message.reply_text(route_input("/health", config))

    async def labs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            await update.message.reply_text(route_input("/labs", config))

    async def scores_command(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        command_text = "/scores"
        if context.args:
            command_text += " " + " ".join(context.args)
        if update.message:
            await update.message.reply_text(route_input(command_text, config))

    async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        text = update.message.text if update.message and update.message.text else ""
        if update.message:
            await update.message.reply_text(route_input(text, config))

    async def button_callback(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        await query.answer()
        response = route_input(query.data or "", config)
        await query.edit_message_text(response)

    application = Application.builder().token(config.bot_token).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("health", health_command))
    application.add_handler(CommandHandler("labs", labs_command))
    application.add_handler(CommandHandler("scores", scores_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_message)
    )
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling()
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Telegram bot entry point")
    parser.add_argument(
        "--test",
        metavar="TEXT",
        help='Run offline test mode: --test "which lab has lowest pass rate?"',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.test is not None:
        return run_test_mode(args.test)
    return run_telegram_mode()


if __name__ == "__main__":
    raise SystemExit(main())
