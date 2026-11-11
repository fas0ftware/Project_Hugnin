"""Hugnin Telegram bot: RSI signal reports on demand and scheduled alerts for new signals.

Commands
  /scan [group]     scan now and report OVERSOLD / OVERBOUGHT assets
  /groups           list watchlist groups
  /subscribe [min]  alert this chat when a NEW signal appears (default every 60 min)
  /unsubscribe      stop alerts
  /help             show this help

Security: set ALLOWED_CHAT_IDS in .env (comma-separated). If it is empty the
bot refuses everyone, so a leaked or guessed bot username cannot be abused.
"""

from __future__ import annotations

import asyncio
import html
import logging
import os
import time

import scanner
import watchlist

MAX_MESSAGE = 4000          # Telegram's hard limit is 4096 characters
SCAN_COOLDOWN = 60          # seconds between manual scans per chat
MIN_ALERT_MINUTES = 15
MAX_ALERT_MINUTES = 24 * 60

log = logging.getLogger("hugnin.bot")


# --- pure helpers (unit-tested, no Telegram dependency) ------------------------------

def parse_allowed(raw: str | None) -> set[int]:
    ids = set()
    for part in (raw or "").replace(" ", "").split(","):
        if part:
            try:
                ids.add(int(part))
            except ValueError:
                log.warning("Ignoring invalid chat id in ALLOWED_CHAT_IDS: %r", part)
    return ids


def format_signal(row) -> str:
    title = "🟢 <b>OVERSOLD</b>" if row["signal"] == "OVERSOLD" else "🔴 <b>OVERBOUGHT</b>"
    return (f"{title} | <code>{html.escape(row['symbol'])}</code>\n"
            f"   └ Price {row['price']:.2f} ({row['change_pct']:+.2f}%) · RSI {row['rsi']:.1f} · "
            f"Trend {html.escape(row['trend'])}")


def build_report(rows, group: str, scanned: int, total: int, header="📡 <b>Hugnin signal report</b>") -> str:
    flagged = scanner.select(rows, sort="rsi", signals_only=True)
    head = f"{header}\nGroup <code>{html.escape(group)}</code> · scanned {scanned}/{total}\n\n"
    if not flagged:
        body = "✅ Market is calm: nothing outside the RSI 30–70 range right now."
    else:
        body = "\n\n".join(format_signal(r) for r in flagged)
    return head + body + "\n\n<i>Not investment advice – algorithm output.</i>"


def chunk_message(text: str, limit: int = MAX_MESSAGE) -> list[str]:
    """Split on blank lines so no message exceeds Telegram's limit and no tag is cut."""
    chunks, current = [], ""
    for block in text.split("\n\n"):
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        while len(block) > limit:  # a single gigantic block: hard split on lines
            cut = block.rfind("\n", 0, limit)
            cut = cut if cut > 0 else limit
            chunks.append(block[:cut])
            block = block[cut:].lstrip("\n")
        current = block
    if current:
        chunks.append(current)
    return chunks


class Cooldown:
    def __init__(self, seconds: float, clock=time.monotonic):
        self.seconds, self.clock, self.last = seconds, clock, {}

    def remaining(self, key) -> float:
        left = self.seconds - (self.clock() - self.last.get(key, -1e18))
        return max(0.0, left)

    def hit(self, key) -> bool:
        """True (and start the timer) if allowed now."""
        if self.remaining(key) > 0:
            return False
        self.last[key] = self.clock()
        return True


def resolve_group(args, default: str) -> str:
    group = (args[0] if args else default).lower()
    watchlist.get_symbols(group)  # raises ValueError for unknown groups
    return group


# --- Telegram wiring -------------------------------------------------------------------

def build_app(token: str, allowed: set[int], default_group: str):
    from telegram import Update
    from telegram.constants import ParseMode
    from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

    cooldown = Cooldown(SCAN_COOLDOWN)

    def authorized(update: Update) -> bool:
        chat = update.effective_chat
        ok = chat is not None and chat.id in allowed
        if not ok:
            log.warning("Rejected chat %s", chat.id if chat else "?")
        return ok

    async def send(context, chat_id, text):
        for part in chunk_message(text):
            await context.bot.send_message(chat_id, part, parse_mode=ParseMode.HTML,
                                           disable_web_page_preview=True)

    async def run_scan(group):
        symbols = watchlist.get_symbols(group)
        rows, _missing = await asyncio.to_thread(scanner.scan, symbols)
        return rows, len(symbols)

    async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not authorized(update):
            return await update.message.reply_text("⛔ This bot is private.")
        await update.message.reply_text(html.escape(__doc__.split("Security:")[0].strip()),
                                        parse_mode=ParseMode.HTML)

    async def cmd_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not authorized(update):
            return
        lines = [f"<code>{n}</code> – {len(watchlist.get_symbols(n))} symbols"
                 for n in ["all", "us"] + watchlist.group_names()]
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

    async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not authorized(update):
            return await update.message.reply_text("⛔ This bot is private.")
        chat_id = update.effective_chat.id
        try:
            group = resolve_group(context.args, default_group)
        except ValueError as exc:
            return await update.message.reply_text(str(exc))
        if not cooldown.hit(chat_id):
            return await update.message.reply_text(
                f"⏳ Please wait {cooldown.remaining(chat_id):.0f}s before the next scan.")
        await update.message.reply_text(f"🦅 Scanning {html.escape(group)}…")
        try:
            rows, total = await run_scan(group)
        except Exception:
            log.exception("scan failed")
            return await update.message.reply_text("⚠️ Market data is unavailable right now. Try again later.")
        await send(context, chat_id, build_report(rows, group, len(rows), total))

    async def alert_job(context: ContextTypes.DEFAULT_TYPE):
        job = context.job
        group = job.data["group"]
        try:
            rows, total = await run_scan(group)
        except Exception:
            log.exception("scheduled scan failed")
            return
        fresh = scanner.new_signals(job.data.get("previous"), rows)
        job.data["previous"] = rows
        if fresh:
            await send(context, job.chat_id,
                       build_report(fresh, group, len(rows), total, header="🚨 <b>New Hugnin signals</b>"))

    async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not authorized(update):
            return
        chat_id = update.effective_chat.id
        try:
            minutes = int(context.args[0]) if context.args else 60
        except ValueError:
            return await update.message.reply_text("Usage: /subscribe [minutes]")
        minutes = min(max(minutes, MIN_ALERT_MINUTES), MAX_ALERT_MINUTES)
        for job in context.job_queue.get_jobs_by_name(str(chat_id)):
            job.schedule_removal()
        context.job_queue.run_repeating(alert_job, interval=minutes * 60, first=5, chat_id=chat_id,
                                        name=str(chat_id), data={"group": default_group, "previous": None})
        await update.message.reply_text(f"🔔 Alerts on: every {minutes} min, only for new signals.")

    async def cmd_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not authorized(update):
            return
        jobs = context.job_queue.get_jobs_by_name(str(update.effective_chat.id))
        for job in jobs:
            job.schedule_removal()
        await update.message.reply_text("🔕 Alerts off." if jobs else "No alerts were active.")

    app = ApplicationBuilder().token(token).build()
    for names, fn in ((["start", "help"], cmd_help), (["scan", "analiz"], cmd_scan),
                      (["groups"], cmd_groups), (["subscribe"], cmd_subscribe),
                      (["unsubscribe"], cmd_unsubscribe)):
        app.add_handler(CommandHandler(names, fn))
    return app


def main():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)  # its INFO lines contain the bot token URL

    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_TOKEN is missing in .env")
    allowed = parse_allowed(os.getenv("ALLOWED_CHAT_IDS"))
    if not allowed:
        log.warning("ALLOWED_CHAT_IDS is empty: every chat will be refused. "
                    "Send /start, read your chat id in this log, then add it to .env.")
    group = os.getenv("HUGNIN_GROUP", "all")
    watchlist.get_symbols(group)
    print("Hugnin signal bot running… 🚀")
    build_app(token, allowed, group).run_polling()


if __name__ == "__main__":
    main()
