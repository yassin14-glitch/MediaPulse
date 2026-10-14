"""Unit tests for URL parsing, metadata extraction, and human error message mapping."""
import pytest
from unittest.mock import MagicMock
from yt_dlp.utils import DownloadError, ExtractorError

from core.downloader_engine import DownloaderEngine
from core.errors import map_error_to_human_message


def test_empty_url():
    de = DownloaderEngine()
    with pytest.raises(RuntimeError) as exc_info:
        de.fetch_info("")
    assert "No URL provided" in str(exc_info.value)

    res = de.download(url="", output_dir="dummy")
    assert res["success"] is False
    assert "No URL provided" in res["error"]


def test_malformed_url(monkeypatch):
    de = DownloaderEngine()
    
    # Mock yt_dlp to simulate unsupported/malformed URL
    def mock_extract_info(self, url, download=False):
        raise DownloadError(f"ERROR: '{url}' is not a valid URL or unsupported.")

    monkeypatch.setattr("yt_dlp.YoutubeDL.extract_info", mock_extract_info)

    with pytest.raises(RuntimeError) as exc_info:
        de.fetch_info("http://not_a_valid_video_url_xyz123")
    assert "not a valid or supported video URL" in str(exc_info.value)


def test_url_with_no_video_404(monkeypatch):
    de = DownloaderEngine()

    def mock_extract_info(self, url, download=False):
        raise DownloadError("ERROR: [generic] HTTP Error 404: Not Found")

    monkeypatch.setattr("yt_dlp.YoutubeDL.extract_info", mock_extract_info)

    with pytest.raises(RuntimeError) as exc_info:
        de.fetch_info("https://example.com/no-video-here")
    assert "no longer available" in str(exc_info.value) or "404" in str(exc_info.value)


def test_private_video_error(monkeypatch):
    de = DownloaderEngine()

    def mock_extract_info(self, url, download=False):
        raise DownloadError("ERROR: [youtube] yrWZsNT8ogU: Private video. Sign in if you've been granted access to this video")

    monkeypatch.setattr("yt_dlp.YoutubeDL.extract_info", mock_extract_info)

    with pytest.raises(RuntimeError) as exc_info:
        de.fetch_info("https://www.youtube.com/watch?v=private_id")
    assert "This video is private" in str(exc_info.value)


def test_age_restricted_video_error(monkeypatch):
    de = DownloaderEngine()

    def mock_extract_info(self, url, download=False):
        raise DownloadError("ERROR: [youtube] abc123xyz: Sign in to confirm your age. This video may be inappropriate for some users.")

    monkeypatch.setattr("yt_dlp.YoutubeDL.extract_info", mock_extract_info)

    with pytest.raises(RuntimeError) as exc_info:
        de.fetch_info("https://www.youtube.com/watch?v=age_restricted_id")
    assert "This video is age-restricted" in str(exc_info.value)


def test_region_blocked_video_error(monkeypatch):
    de = DownloaderEngine()

    def mock_extract_info(self, url, download=False):
        raise DownloadError("ERROR: [youtube] abc123xyz: The uploader has not made this video available in your country.")

    monkeypatch.setattr("yt_dlp.YoutubeDL.extract_info", mock_extract_info)

    with pytest.raises(RuntimeError) as exc_info:
        de.fetch_info("https://www.youtube.com/watch?v=region_blocked_id")
    assert "not available in your geographical region" in str(exc_info.value)


def test_playlist_detection(monkeypatch):
    de = DownloaderEngine()

    mock_playlist = {
        "title": "My Test Playlist",
        "uploader": "Test Channel",
        "entries": [
            {"title": "Video 1", "duration": 120, "uploader": "Test Channel"},
            {"title": "Video 2", "duration": 180, "uploader": "Test Channel"}
        ]
    }

    monkeypatch.setattr("yt_dlp.YoutubeDL.extract_info", lambda self, url, download=False: mock_playlist)

    info = de.fetch_info("https://www.youtube.com/playlist?list=PL12345")
    assert info["is_playlist"] is True
    assert info["count"] == 2
    assert info["title"] == "My Test Playlist"
    assert info["duration"] == 300


def test_normalize_video_url():
    from core.downloader_engine import normalize_video_url
    
    # Instagram reels plural to singular
    raw_ig = "https://www.instagram.com/reels/DecR0l8BSWP/?igsh=MWQ1ZGUxMzBkMA=="
    normalized_ig = normalize_video_url(raw_ig)
    assert normalized_ig == "https://www.instagram.com/reel/DecR0l8BSWP/"

    # TikTok tracking params stripped
    raw_tt = "https://www.tiktok.com/@user/video/1234567890123456789?is_from_webapp=1&sender_device=pc"
    normalized_tt = normalize_video_url(raw_tt)
    assert normalized_tt == "https://www.tiktok.com/@user/video/1234567890123456789/"

    # Regular YouTube URL untouched
    yt = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert normalize_video_url(yt) == yt


def test_candidate_browsers_selection(monkeypatch):
    from core.downloader_engine import DownloaderEngine

    # Test when setting is specific browser
    monkeypatch.setattr("core.downloader_engine.get_browser_cookies_setting", lambda: "firefox")
    assert DownloaderEngine.get_candidate_browsers() == ["firefox"]

    # Test when setting is none
    monkeypatch.setattr("core.downloader_engine.get_browser_cookies_setting", lambda: "none")
    assert DownloaderEngine.get_candidate_browsers() == []

    # Test auto mode
    monkeypatch.setattr("core.downloader_engine.get_browser_cookies_setting", lambda: "auto")
    monkeypatch.setattr("core.downloader_engine.get_installed_browsers", lambda: ["firefox", "edge"])
    DownloaderEngine._cached_working_browser = "firefox"
    candidates = DownloaderEngine.get_candidate_browsers()
    assert candidates[0] == "firefox"
    assert "edge" in candidates

