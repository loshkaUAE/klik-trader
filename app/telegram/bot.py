from __future__ import annotations

from collections.abc import Callable

from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import settings
from app.models import Signal


class TelegramNotifier:
    def __init__(self, status_provider: Callable[[], dict] | None = None, latest_signals_provider: Callable[[], list[dict]] | None = None) -> None:
        self.enabled = bool(settings.telegram_token and settings.telegram_chat_id)
        self.bot = Bot(token=settings.telegram_token) if self.enabled else None
        self._status_provider = status_provider or (lambda: {})
        self._latest_signals_provider = latest_signals_provider or (lambda: [])
        self._app: Application | None = None

    async def start_bot_host(self) -> None:
        if not self.enabled:
            return
        app = Application.builder().token(settings.telegram_token).build()
        app.add_handler(CommandHandler("status", self._status_cmd))
        app.add_handler(CommandHandler("signals", self._signals_cmd))
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        self._app = app

    async def stop_bot_host(self) -> None:
        if self._app is None:
            return
        await self._app.updater.stop()
        await self._app.stop()
        await self._app.shutdown()

    async def _status_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._authorized(update):
            return
        status = self._status_provider()
        lines = [f"{k}: {v}" for k, v in status.items()]
        await update.message.reply_text("System status\n" + "\n".join(lines))

    async def _signals_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._authorized(update):
            return
        signals = self._latest_signals_provider()[:5]
        if not signals:
            await update.message.reply_text("No signals in history.")
            return
        text = "\n\n".join(
            [
                f"{s['created_at']} | {s['symbol']} {s['direction']} conf={s['confidence']:.1f}% rr={s['rr']:.2f}"
                for s in signals
            ]
        )
        await update.message.reply_text(text)

    @staticmethod
    def _authorized(update: Update) -> bool:
        if not settings.telegram_admin_user_id:
            return True
        return str(update.effective_user.id) == settings.telegram_admin_user_id

    async def send_signal(self, signal: Signal) -> None:
        if not self.enabled or self.bot is None:
            return
        message = (
            "🚨 *High-Probability Signal*\n"
            f"Symbol: `{signal.symbol}`\n"
            f"Direction: *{signal.direction}*\n"
            f"Entry: `{signal.entry:.2f}`\n"
            f"SL: `{signal.stop_loss:.2f}`\n"
            f"TP1: `{signal.tp1:.2f}`\n"
            f"TP2: `{signal.tp2:.2f}`\n"
            f"TP3: `{signal.tp3:.2f}`\n"
            f"R:R: `{signal.rr:.2f}`\n"
            f"Confidence: *{signal.confidence:.1f}%*\n"
            f"Why: {signal.why}"
        )
        await self.bot.send_message(chat_id=settings.telegram_chat_id, text=message, parse_mode="Markdown")

    async def send_event(self, text: str) -> None:
        if not self.enabled or self.bot is None:
            return
        await self.bot.send_message(chat_id=settings.telegram_chat_id, text=text)
