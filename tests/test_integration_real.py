"""Real-world integration tests marked as slow (optional)."""
import os
import pytest
from core.downloader_engine import DownloaderEngine


@pytest.mark.slow
def test_real_video_download_and_merge(temp_dir):
    """Downloads a short public video to verify end-to-end integration with real network and FFmpeg."""
    de = DownloaderEngine()
    
    # Public sample video for real integration testing
    test_url = "https://www.w3schools.com/html/mov_bbb.mp4"

    progress_events = []
    def on_progress(d):
        progress_events.append(d)

    result = de.download(
        url=test_url,
        output_dir=temp_dir,
        mode="video",
        quality="best",
        container="mp4",
        progress_callback=on_progress
    )

    assert result["success"] is True
    assert result["file_path"] is not None
    assert os.path.exists(result["file_path"])
    assert os.path.getsize(result["file_path"]) > 1000
    assert len(progress_events) > 0


@pytest.mark.slow
def test_real_audio_extraction(temp_dir):
    """Downloads and converts audio from a public test video to MP3."""
    de = DownloaderEngine()
    test_url = "https://www.w3schools.com/html/mov_bbb.mp4"

    result = de.download(
        url=test_url,
        output_dir=temp_dir,
        mode="audio",
        quality="best",
        container="mp3"
    )

    assert result["success"] is True
    assert result["file_path"] is not None
    assert result["file_path"].endswith(".mp3")
    assert os.path.exists(result["file_path"])
