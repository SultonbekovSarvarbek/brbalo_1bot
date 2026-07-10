from __future__ import annotations

from pathlib import Path
from threading import Event

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


VIDEO_SUFFIXES = frozenset({".mp4", ".mov", ".mkv", ".webm"})


class NoVideoFoundError(RuntimeError):
    """Raised when yt-dlp completes without producing a video file."""


def download_videos(
    url: str,
    destination: Path,
    *,
    max_file_size_bytes: int,
    cookies_file: Path | None = None,
    cancel_event: Event | None = None,
) -> list[Path]:
    """Download up to ten videos from one Instagram post into destination."""
    destination.mkdir(parents=True, exist_ok=True)
    format_selector = (
        f"best[ext=mp4][filesize<{max_file_size_bytes}]"
        f"/best[ext=mp4][filesize_approx<{max_file_size_bytes}]"
        f"/best[filesize<{max_file_size_bytes}]"
        "/best"
    )
    def stop_when_cancelled(_: dict[str, object]) -> None:
        if cancel_event and cancel_event.is_set():
            raise DownloadError("загрузка остановлена по таймауту")

    options: dict[str, object] = {
        "format": format_selector,
        "outtmpl": str(destination / "%(id)s-%(playlist_index|0)s.%(ext)s"),
        "merge_output_format": "mp4",
        "max_filesize": max_file_size_bytes,
        "playlistend": 10,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,
        "restrictfilenames": True,
        "progress_hooks": [stop_when_cancelled],
    }
    if cookies_file:
        options["cookiefile"] = str(cookies_file)

    with YoutubeDL(options) as downloader:
        downloader.download([url])

    files = sorted(
        path
        for path in destination.iterdir()
        if path.is_file()
        and path.suffix.lower() in VIDEO_SUFFIXES
        and path.stat().st_size <= max_file_size_bytes
    )
    if not files:
        raise NoVideoFoundError("загрузчик не создал подходящий видеофайл")
    return files
