from instagram_bot.urls import extract_instagram_urls, normalize_instagram_url


def test_extracts_supported_links_and_deduplicates() -> None:
    text = (
        "Смотри https://www.instagram.com/reel/ABC_123/?igsh=test и "
        "https://www.instagram.com/reel/ABC_123/?igsh=test"
    )

    assert extract_instagram_urls([text]) == [
        "https://www.instagram.com/reel/ABC_123/?igsh=test"
    ]


def test_accepts_link_without_scheme_and_trailing_punctuation() -> None:
    assert extract_instagram_urls(["instagram.com/p/CODE-1/). Текст"]) == [
        "https://instagram.com/p/CODE-1/"
    ]


def test_accepts_story_and_text_link_entity() -> None:
    assert extract_instagram_urls(
        ["Ссылка спрятана"],
        ["https://instagram.com/stories/user.name/1234567890/"],
    ) == ["https://instagram.com/stories/user.name/1234567890/"]


def test_rejects_profiles_and_lookalike_domains() -> None:
    assert normalize_instagram_url("https://instagram.com/some_profile") is None
    assert normalize_instagram_url("https://instagram.com.evil.example/reel/ABC") is None
    assert extract_instagram_urls(["https://evil.example/reel/ABC"]) == []


def test_accepts_share_reel() -> None:
    assert normalize_instagram_url("https://www.instagram.com/share/reel/XYZ/?x=1") == (
        "https://www.instagram.com/share/reel/XYZ/?x=1"
    )
