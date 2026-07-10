from __future__ import annotations

import asyncio
import logging
import tempfile
from contextlib import suppress
from pathlib import Path
from threading import Event

from telegram import BotCommand, Message, MessageEntity, Update
from telegram.constants import ChatAction
from telegram.error import BadRequest, NetworkError
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from yt_dlp.utils import DownloadError

from instagram_bot.config import ConfigError, Settings
from instagram_bot.downloader import NoVideoFoundError, download_videos
from instagram_bot.urls import extract_instagram_urls


LOGGER = logging.getLogger(__name__)
PRIVATE_OR_UNAVAILABLE = (
    "Не получилось скачать видео. Возможно, публикация приватная, удалена "
    "или Instagram требует авторизацию."
)


def _entity_urls(message: Message) -> list[str]:
    urls: list[str] = []
    for entity in (*(message.entities or ()), *(message.caption_entities or ())):
        if entity.type == MessageEntity.TEXT_LINK and entity.url:
            urls.append(entity.url)
    return urls


def _chat_is_allowed(settings: Settings, chat_id: int) -> bool:
    return not settings.allowed_chat_ids or chat_id in settings.allowed_chat_ids


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat:
        return

    settings: Settings = context.application.bot_data["settings"]
    if not _chat_is_allowed(settings, chat.id):
        return

    await message.reply_text(
        "Пришлите ссылку на Instagram Reel, публикацию или видео — "
        "я скачаю доступное видео и отправлю его сюда."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not message or not chat or (user and user.is_bot):
        return

    settings: Settings = context.application.bot_data["settings"]
    if not _chat_is_allowed(settings, chat.id):
        return

    urls = extract_instagram_urls(
        (message.text, message.caption),
        _entity_urls(message),
    )
    if not urls:
        return

    semaphore: asyncio.Semaphore = context.application.bot_data["download_semaphore"]
    for url in urls:
        await _download_and_send(message, context, settings, semaphore, url)


async def _download_and_send(
    message: Message,
    context: ContextTypes.DEFAULT_TYPE,
    settings: Settings,
    semaphore: asyncio.Semaphore,
    url: str,
) -> None:
    try:
        async with semaphore:
            await context.bot.send_chat_action(
                chat_id=message.chat_id,
                action=ChatAction.UPLOAD_VIDEO,
                message_thread_id=message.message_thread_id,
            )
            with tempfile.TemporaryDirectory(prefix="instagram-bot-") as directory:
                cancel_event = Event()
                download_task = asyncio.create_task(
                    asyncio.to_thread(
                        download_videos,
                        url,
                        Path(directory),
                        max_file_size_bytes=settings.max_file_size_bytes,
                        cookies_file=settings.instagram_cookies_file,
                        cancel_event=cancel_event,
                    )
                )
                try:
                    files = await asyncio.wait_for(
                        asyncio.shield(download_task),
                        timeout=settings.download_timeout_seconds,
                    )
                except TimeoutError:
                    # asyncio cannot force-stop a worker thread. Ask yt-dlp to
                    # abort through its progress hook and wait before deleting
                    # the temporary directory it may still be writing into.
                    cancel_event.set()
                    with suppress(Exception):
                        await download_task
                    raise
                for video_path in files:
                    await _send_file(message, video_path)
    except TimeoutError:
        LOGGER.warning("Instagram download timed out")
        await message.reply_text(
            "Загрузка заняла слишком много времени. Попробуйте ещё раз позже."
        )
    except (DownloadError, NoVideoFoundError):
        LOGGER.warning("Instagram download failed", exc_info=True)
        await message.reply_text(PRIVATE_OR_UNAVAILABLE)
    except (BadRequest, NetworkError):
        LOGGER.warning("Telegram rejected the downloaded video", exc_info=True)
        await message.reply_text(
            "Видео скачано, но Telegram не принял файл. "
            "Возможно, он превышает лимит 50 МБ."
        )


async def _send_file(message: Message, video_path: Path) -> None:
    with video_path.open("rb") as video:
        if video_path.suffix.lower() == ".mp4":
            await message.reply_video(
                video=video,
                supports_streaming=True,
                do_quote=True,
                read_timeout=120,
                write_timeout=120,
                connect_timeout=30,
                pool_timeout=30,
            )
        else:
            await message.reply_document(
                document=video,
                do_quote=True,
                read_timeout=120,
                write_timeout=120,
                connect_timeout=30,
                pool_timeout=30,
            )


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    LOGGER.error("Unhandled bot error", exc_info=context.error)


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Как пользоваться ботом"),
            BotCommand("help", "Помощь"),
        ]
    )


def build_application(settings: Settings) -> Application:
    application = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .concurrent_updates(max(4, settings.download_concurrency * 2))
        .connection_pool_size(max(8, settings.download_concurrency * 4))
        .pool_timeout(30)
        .post_init(post_init)
        .build()
    )
    application.bot_data["settings"] = settings
    application.bot_data["download_semaphore"] = asyncio.Semaphore(
        settings.download_concurrency
    )
    application.add_handler(CommandHandler(("start", "help"), start))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    application.add_error_handler(on_error)
    return application


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    try:
        settings = Settings.from_env()
    except ConfigError as exc:
        raise SystemExit(f"Ошибка настройки: {exc}") from exc

    LOGGER.info("Starting Instagram Telegram bot")
    application = build_application(settings)
    application.run_polling(
        allowed_updates=("message", "channel_post"),
        drop_pending_updates=False,
    )
