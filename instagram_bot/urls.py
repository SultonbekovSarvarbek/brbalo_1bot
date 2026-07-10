from __future__ import annotations

import re
from collections.abc import Iterable
from urllib.parse import urlsplit, urlunsplit


INSTAGRAM_URL_RE = re.compile(
    r"(?i)(?<![\w@])(?:https?://)?(?:www\.|m\.)?"
    r"(?:instagram\.com|instagr\.am)/[^\s<>{}\[\]\"']+"
)
SUPPORTED_PATH_RE = re.compile(
    r"^/(?:reel|reels|p|tv)/[A-Za-z0-9_-]+/?$"
    r"|^/share/(?:reel|p)/[A-Za-z0-9_-]+/?$"
    r"|^/stories/[A-Za-z0-9._-]+/[0-9]+/?$",
    re.IGNORECASE,
)
TRAILING_PUNCTUATION = ".,;:!?)]}»”"
ALLOWED_HOSTS = frozenset(
    {
        "instagram.com",
        "www.instagram.com",
        "m.instagram.com",
        "instagr.am",
        "www.instagr.am",
    }
)


def normalize_instagram_url(candidate: str) -> str | None:
    """Return a safe canonical Instagram media URL, or None when unsupported."""
    candidate = candidate.strip().rstrip(TRAILING_PUNCTUATION)
    if not candidate:
        return None
    if not re.match(r"(?i)^https?://", candidate):
        candidate = f"https://{candidate}"

    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return None

    if parsed.scheme.lower() not in {"http", "https"}:
        return None
    hostname = (parsed.hostname or "").lower()
    if hostname not in ALLOWED_HOSTS or not SUPPORTED_PATH_RE.fullmatch(parsed.path):
        return None

    # Fragments are never needed by the downloader. Keep the query because
    # Instagram share links can use it while resolving a publication.
    return urlunsplit(("https", hostname, parsed.path, parsed.query, ""))


def extract_instagram_urls(
    texts: Iterable[str | None], entity_urls: Iterable[str | None] = ()
) -> list[str]:
    """Extract supported links in their original order without duplicates."""
    candidates: list[str] = []
    for text in texts:
        if text:
            candidates.extend(match.group(0) for match in INSTAGRAM_URL_RE.finditer(text))
    candidates.extend(url for url in entity_urls if url)

    result: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = normalize_instagram_url(candidate)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
