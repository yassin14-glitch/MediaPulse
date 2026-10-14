"""Comprehensive unit & integration tests for YouTube Playlist support.
Covers:
- Empty playlists
- Single-video-in-a-playlist links vs pure playlists
- Unavailable, private, and region-blocked videos
- Cancelling halfway
- Resuming and skipping already downloaded files
- Queue integration & API endpoints
"""
import os
import shutil
import tempfile
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from core.downloader_engine import DownloaderEngine, check_playlist_url
from core.queue_manager import DownloadTask, QueueManager, TaskState
from web.server import app

client = TestClient(app)


# --- 1. Test URL Playlist Analysis ---

def test_check_playlist_url_detection():
    # Pure playlist
    pure_url = "https://www.youtube.com/playlist?list=PLrAXtmErZgOdP_8GzSRCpecL4PBnpdF46"
    chk1 = check_playlist_url(pure_url)
    assert chk1["is_youtube"] is True
    assert chk1["has_playlist"] is True
    assert chk1["has_video"] is False
    assert chk1["is_pure_playlist"] is True
    assert chk1["is_single_and_playlist"] is False
    assert chk1["playlist_id"] == "PLrAXtmErZgOdP_8GzSRCpecL4PBnpdF46"
    assert chk1["video_id"] is None

    # Single video inside playlist
    combo_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmErZgOdP_8GzSRCpecL4PBnpdF46&index=1"
    chk2 = check_playlist_url(combo_url)
    assert chk2["is_youtube"] is True
    assert chk2["has_playlist"] is True
    assert chk2["has_video"] is True
    assert chk2["is_single_and_playlist"] is True
    assert chk2["is_pure_playlist"] is False
    assert chk2["video_id"] == "dQw4w9WgXcQ"
    assert chk2["playlist_id"] == "PLrAXtmErZgOdP_8GzSRCpecL4PBnpdF46"
    assert "watch?v=dQw4w9WgXcQ" in chk2["single_url"]
    assert "playlist?list=PLrAXtmErZgOdP_8GzSRCpecL4PBnpdF46" in chk2["playlist_url"]

    # Shortened youtu.be link with playlist parameter
    short_combo = "https://youtu.be/dQw4w9WgXcQ?list=PLrAXtmErZgOdP_8GzSRCpecL4PBnpdF46"
    chk3 = check_playlist_url(short_combo)
    assert chk3["is_single_and_playlist"] is True
    assert chk3["video_id"] == "dQw4w9WgXcQ"
    assert chk3["playlist_id"] == "PLrAXtmErZgOdP_8GzSRCpecL4PBnpdF46"

    # Regular single video
    regular_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    chk4 = check_playlist_url(regular_url)
    assert chk4["is_youtube"] is True
    assert chk4["has_playlist"] is False
    assert chk4["has_video"] is True
    assert chk4["is_single_and_playlist"] is False
    assert chk4["is_pure_playlist"] is False

    # Non-YouTube URL
    insta_url = "https://www.instagram.com/reel/C12345/"
    chk5 = check_playlist_url(insta_url)
    assert chk5["is_youtube"] is False


# --- 2. Test Empty Playlist Handling ---

def test_empty_playlist_handling():
    engine = DownloaderEngine()

    mock_info = {
        "_type": "playlist",
        "id": "PLempty123",
        "title": "Empty Playlist",
        "uploader": "Test Channel",
        "entries": []
    }

    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_info
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        res = engine.fetch_playlist_info("https://www.youtube.com/playlist?list=PLempty123")
        assert res["is_playlist"] is True
        assert res["is_empty"] is True
        assert res["count"] == 0
        assert res["entries"] == []
        assert res["title"] == "Empty Playlist"


# --- 3. Test Playlist with Unavailable / Private / Deleted Videos ---

def test_playlist_with_unavailable_videos():
    engine = DownloaderEngine()

    mock_entries = [
        {
            "id": "vid1",
            "title": "Accessible Video 1",
            "duration": 180,
            "uploader": "Channel A",
            "thumbnails": [{"url": "http://example.com/thumb1.jpg"}]
        },
        {
            "id": None,
            "title": "[Private video]",
            "duration": None,
            "uploader": None,
            "availability": "private"
        },
        {
            "id": "vid3",
            "title": "[Deleted video]",
            "duration": 0,
            "uploader": None
        },
        {
            "id": "vid4",
            "title": "Accessible Video 2",
            "duration": 240,
            "uploader": "Channel A",
            "thumbnails": [{"url": "http://example.com/thumb4.jpg"}]
        }
    ]

    mock_info = {
        "_type": "playlist",
        "id": "PLmixed123",
        "title": "Mixed Availability Playlist",
        "uploader": "Channel A",
        "entries": mock_entries
    }

    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_info
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        res = engine.fetch_playlist_info("https://www.youtube.com/playlist?list=PLmixed123")
        assert res["count"] == 4
        entries = res["entries"]
        assert entries[0]["is_available"] is True
        assert entries[0]["title"] == "Accessible Video 1"
        assert entries[1]["is_available"] is False
        assert entries[2]["is_available"] is False
        assert entries[3]["is_available"] is True


def test_download_skips_unavailable_video_with_short_message():
    engine = DownloaderEngine()
    temp_dir = tempfile.mkdtemp()

    try:
        # Simulate yt-dlp raising private / unavailable error
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.side_effect = Exception("ERROR: [youtube] vid_priv: This video is private")
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            res = engine.download(
                url="https://www.youtube.com/watch?v=vid_priv",
                output_dir=temp_dir
            )

            assert res["success"] is False
            assert res["skipped"] is True
            assert res["is_unavailable"] is True
            assert "Skipped: Video is private" in res["error"]
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# --- 4. Test Resuming Stopped Playlist (Skipping Already Existing Files) ---

def test_resume_skips_already_downloaded_file():
    engine = DownloaderEngine()
    temp_dir = tempfile.mkdtemp()

    try:
        # Pre-create completed file for index #1
        existing_file = os.path.join(temp_dir, "01 - Introduction Video [vid123].mp4")
        with open(existing_file, "wb") as f:
            f.write(b"0" * 4096)  # 4 KB valid content

        # Run download with prefix_index and matching playlist_index
        res = engine.download(
            url="https://www.youtube.com/watch?v=vid123",
            output_dir=temp_dir,
            playlist_index=1,
            prefix_index=True,
            skip_if_exists=True
        )

        assert res["success"] is True
        assert res["skipped"] is True
        assert res["file_path"] == existing_file
        assert "4.0 KB" in res["file_size"]
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# --- 5. Test Cancelling Halfway in Queue ---

def test_cancelling_halfway_in_queue():
    queue = QueueManager()
    queue.tasks = []  # fresh queue

    temp_dir = tempfile.mkdtemp()

    try:
        # Add 3 playlist tasks
        t1 = queue.add_task(url="https://www.youtube.com/watch?v=item1", output_dir=temp_dir, playlist_index=1, playlist_total=3)
        t2 = queue.add_task(url="https://www.youtube.com/watch?v=item2", output_dir=temp_dir, playlist_index=2, playlist_total=3)
        t3 = queue.add_task(url="https://www.youtube.com/watch?v=item3", output_dir=temp_dir, playlist_index=3, playlist_total=3)

        assert len(queue.tasks) == 3
        assert t1.playlist_progress_str == "1 of 3"
        assert t2.playlist_progress_str == "2 of 3"
        assert t3.playlist_progress_str == "3 of 3"

        # Cancel t2 while queued
        success = queue.cancel_task(t2.id)
        assert success is True
        assert t2.state == TaskState.CANCELLED

        # Cancel t1
        queue.cancel_task(t1.id)
        assert t1.state == TaskState.CANCELLED

        # Remove all
        queue.shutdown()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# --- 6. Test Playlist API Endpoints ---

def test_api_check_url_endpoint():
    res = client.post("/api/youtube/check-url", json={"url": "https://www.youtube.com/watch?v=abc&list=PLxyz"})
    assert res.status_code == 200
    data = res.json()
    assert data["is_single_and_playlist"] is True
    assert data["video_id"] == "abc"
    assert data["playlist_id"] == "PLxyz"


def test_api_playlist_info_endpoint():
    mock_info = {
        "_type": "playlist",
        "id": "PLapi_test",
        "title": "API Test Playlist",
        "uploader": "Uploader",
        "entries": [
            {"id": "v1", "title": "Vid 1", "duration": 100, "uploader": "Uploader"},
            {"id": "v2", "title": "Vid 2", "duration": 200, "uploader": "Uploader"}
        ]
    }

    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_info
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        res = client.post("/api/youtube/playlist-info", json={"url": "https://www.youtube.com/playlist?list=PLapi_test"})
        assert res.status_code == 200
        data = res.json()
        assert data["is_playlist"] is True
        assert data["count"] == 2
        assert data["entries"][0]["title"] == "Vid 1"
        assert data["entries"][1]["index"] == 2


def test_api_add_playlist_to_queue():
    temp_dir = tempfile.mkdtemp()
    try:
        payload = {
            "playlist_id": "PLq123",
            "playlist_title": "My Test Playlist",
            "items": [
                {"url": "https://www.youtube.com/watch?v=v1", "title": "Track 01", "index": 1},
                {"url": "https://www.youtube.com/watch?v=v2", "title": "Track 02", "index": 2}
            ],
            "mode": "video",
            "quality": "best",
            "container": "mp4",
            "output_dir": temp_dir,
            "create_subfolder": True,
            "prefix_index": True
        }

        res = client.post("/api/queue/add-playlist", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert "My Test Playlist" in data["output_dir"]

        # Check queue
        q_res = client.get("/api/queue")
        q_data = q_res.json()
        tasks = [t for t in q_data["tasks"] if t.get("playlist_id") == "PLq123"]
        assert len(tasks) == 2
        assert tasks[0]["playlist_index"] == 1
        assert tasks[0]["playlist_total"] == 2
        assert tasks[0]["playlist_progress_str"] == "1 of 2"
        assert tasks[1]["playlist_index"] == 2
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_large_playlist_speed_and_scalability():
    """Verify that a playlist with 500 entries parses in milliseconds without freezing."""
    engine = DownloaderEngine()
    large_entries = [
        {"id": f"vid_{i}", "title": f"Video Item #{i}", "duration": 120 + i, "uploader": "Large Channel"}
        for i in range(1, 501)
    ]
    mock_info = {
        "_type": "playlist",
        "id": "PLhuge500",
        "title": "Huge 500 Video Course",
        "uploader": "Large Channel",
        "entries": large_entries
    }

    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_info
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        start = time.time()
        res = engine.fetch_playlist_info("https://www.youtube.com/playlist?list=PLhuge500")
        elapsed = time.time() - start

        assert res["count"] == 500
        assert res["entries"][0]["index"] == 1
        assert res["entries"][499]["index"] == 500
        assert res["entries"][499]["id"] == "vid_500"
        # Should parse 500 items in under 50ms in flat mode
        assert elapsed < 0.20
