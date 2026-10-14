"""Unit tests for FastAPI endpoints and JavaScript-to-Python bridge stability."""
import pytest
from fastapi.testclient import TestClient
from web.server import app

client = TestClient(app)


def test_api_status():
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "ffmpeg_available" in data
    assert "download_dir" in data
    assert "ytdlp_version" in data


def test_api_open_folder_invalid_path():
    """Bridge should return success=False gracefully without 500 server crash."""
    resp = client.post("/api/open-folder", json={"path": "Z:\\NonExistent\\Drive\\Path"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False


def test_api_play_file_missing_file():
    """Bridge should return 404 error cleanly without 500 server crash."""
    resp = client.post("/api/play-file", json={"path": "C:\\fake_missing_video.mp4"})
    assert resp.status_code == 404
    data = resp.json()
    assert "File does not exist" in data["detail"]


def test_api_youtube_info_empty_url():
    """Bridge should return 400 clean message on empty input."""
    resp = client.post("/api/youtube/info", json={"url": ""})
    assert resp.status_code == 400
    data = resp.json()
    assert "No URL provided" in data["detail"]


def test_api_download_status_nonexistent_task():
    """Bridge should return 404 cleanly on invalid task id."""
    resp = client.get("/api/download/status/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Task not found"


def test_api_cancel_nonexistent_task():
    """Bridge should return 404 cleanly on cancelling invalid task id."""
    resp = client.post("/api/download/cancel/999999")
    assert resp.status_code == 404


def test_api_queue_endpoints():
    """Tests adding, pausing, resuming, and clearing queue via REST API."""
    add_resp = client.post("/api/queue/add", json={
        "url": "https://example.com/api_queue_test",
        "title": "API Queue Item",
        "mode": "video",
        "quality": "best",
        "container": "mp4"
    })
    assert add_resp.status_code == 200
    task_id = add_resp.json()["task"]["id"]

    # Check queue list
    list_resp = client.get("/api/queue")
    assert list_resp.status_code == 200
    task_ids = [t["id"] for t in list_resp.json()["tasks"]]
    assert task_id in task_ids

    # Pause
    pause_resp = client.post(f"/api/queue/pause/{task_id}")
    assert pause_resp.status_code == 200

    # Resume
    resume_resp = client.post(f"/api/queue/resume/{task_id}")
    assert resume_resp.status_code == 200

    # Cancel & Remove
    cancel_resp = client.post(f"/api/queue/cancel/{task_id}")
    assert cancel_resp.status_code == 200
    remove_resp = client.post(f"/api/queue/remove/{task_id}")
    assert remove_resp.status_code == 200


def test_api_updater_status():
    resp = client.get("/api/update/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "checked" in data
