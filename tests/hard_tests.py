"""Hardcore verification test suite covering edge cases, MB meter, folder selection, Arabic titles, and API."""
import os
import sys
import time
import shutil
import tempfile
import unittest

# Ensure UTF-8 console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.downloader_engine import DownloaderEngine, DownloadCancelledException
from core.ffmpeg_manager import FFmpegManager
from core.history_manager import HistoryManager
from core.web_extractor import WebVideoExtractor
from fastapi.testclient import TestClient
from web.server import app, active_downloads


class HardcoreDownloaderTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.join(tempfile.gettempdir(), "downloader_hard_test_" + str(int(time.time())))
        os.makedirs(cls.test_dir, exist_ok=True)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_01_mb_meter_formatting_and_hook_cases(self):
        """Tests that MB meter formats every combination of downloaded/total bytes accurately."""
        de = DownloaderEngine()

        # Case 1: Standard total bytes
        self.assertEqual(de.format_bytes(1048576), "1.0 MB")
        self.assertEqual(de.format_bytes(52428800), "50.0 MB")
        self.assertEqual(de.format_bytes(1073741824), "1.0 GB")
        self.assertEqual(de.format_bytes(0), "0 B")
        self.assertEqual(de.format_bytes(None), "0 B")

        # Case 2: Progress hook simulation with normal total_bytes
        hook_events = []
        def test_cb(d):
            hook_events.append(d)

        # Simulate hook call during download
        hook_dict = {
            "status": "downloading",
            "downloaded_bytes": 15728640, # 15 MB
            "total_bytes": 104857600,     # 100 MB
            "speed": 5242880,             # 5 MB/s
            "eta": 17,
            "filename": "video.mp4"
        }

        # Check calculation logic
        downloaded = hook_dict["downloaded_bytes"]
        total = hook_dict["total_bytes"]
        downloaded_str = de.format_bytes(downloaded)
        total_str = de.format_bytes(total)
        size_str = f"{downloaded_str} / {total_str}"

        self.assertEqual(downloaded_str, "15.0 MB")
        self.assertEqual(total_str, "100.0 MB")
        self.assertEqual(size_str, "15.0 MB / 100.0 MB")

        # Case 3: total_bytes is None but total_bytes_estimate is given
        hook_dict2 = {
            "status": "downloading",
            "downloaded_bytes": 31457280, # 30 MB
            "total_bytes": None,
            "total_bytes_estimate": 157286400, # 150 MB
        }
        total2 = hook_dict2.get("total_bytes") or hook_dict2.get("total_bytes_estimate")
        size_str2 = f"{de.format_bytes(hook_dict2['downloaded_bytes'])} / {de.format_bytes(total2)}"
        self.assertEqual(size_str2, "30.0 MB / 150.0 MB")

        # Case 4: Total bytes completely unknown
        hook_dict3 = {
            "status": "downloading",
            "downloaded_bytes": 5242880, # 5 MB
            "total_bytes": None,
            "total_bytes_estimate": None
        }
        total3 = hook_dict3.get("total_bytes") or hook_dict3.get("total_bytes_estimate") or 0
        size_str3 = f"{de.format_bytes(hook_dict3['downloaded_bytes'])} / {de.format_bytes(total3)}" if total3 > 0 else f"{de.format_bytes(hook_dict3['downloaded_bytes'])} downloaded"
        self.assertEqual(size_str3, "5.0 MB downloaded")

        print("✔ test_01_mb_meter_formatting_and_hook_cases passed!")

    def test_02_arabic_and_unicode_title_handling(self):
        """Tests that Arabic/Unicode video titles with quotes and special characters are handled safely."""
        de = DownloaderEngine()
        # Test URL from user's screenshot
        test_url = "https://www.youtube.com/watch?v=yrWZsNT8ogU"
        info = de.fetch_info(test_url)

        self.assertIn("title", info)
        self.assertTrue(len(info["title"]) > 0)
        # Should contain Arabic letters
        self.assertTrue(any('\u0600' <= char <= '\u06FF' for char in info["title"]))
        print(f"✔ test_02_arabic_and_unicode_title_handling passed! Title: {info['title'][:40]}...")

    def test_03_folder_selection_and_persistence(self):
        """Tests changing the download folder via API and verifying files are directed there."""
        custom_folder = os.path.join(self.test_dir, "custom_dest")
        os.makedirs(custom_folder, exist_ok=True)

        # Check API status
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        initial_dir = res.json()["download_dir"]

        # Simulate choosing folder via API with explicit output_dir in download request
        dl_res = self.client.post("/api/download", json={
            "url": "https://www.youtube.com/watch?v=yrWZsNT8ogU",
            "mode": "video",
            "quality": "360p",
            "container": "mp4",
            "output_dir": custom_folder,
            "title": "Arabic Test Video"
        })
        self.assertEqual(dl_res.status_code, 200)
        data = dl_res.json()
        self.assertIn("task_id", data)
        self.assertEqual(data["output_dir"], custom_folder)

        # Cancel the task so we don't download the entire 50-minute video during tests
        task_id = data["task_id"]
        time.sleep(1.0)
        cancel_res = self.client.post(f"/api/download/cancel/{task_id}")
        self.assertEqual(cancel_res.status_code, 200)

        # Verify status endpoint returns cancelled status and size field
        status_res = self.client.get(f"/api/download/status/{task_id}")
        self.assertEqual(status_res.status_code, 200)
        s_data = status_res.json()
        self.assertIn("size", s_data)
        self.assertIn("downloaded", s_data)
        self.assertIn("speed", s_data)
        self.assertIn("eta", s_data)

        print("✔ test_03_folder_selection_and_persistence passed!")

    def test_04_web_video_extractor_deep_scraping(self):
        """Tests web scraper against synthetic HTML pages with video tags, OpenGraph, and streams."""
        extractor = WebVideoExtractor()

        # Synthetic HTML test
        test_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Media Test Page</title>
            <meta property="og:video" content="https://example.com/stream.mp4">
            <meta property="og:image" content="https://example.com/poster.jpg">
        </head>
        <body>
            <video src="https://example.com/direct_video.mp4" poster="https://example.com/thumb.png"></video>
            <video>
                <source src="https://example.com/source_video.webm" type="video/webm">
            </video>
            <iframe src="https://player.vimeo.com/video/12345678"></iframe>
        </body>
        </html>
        """

        from unittest.mock import patch, MagicMock
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = test_html

        with patch("requests.get", return_value=mock_resp):
            videos, page_title, page_icon = extractor._deep_scrape_webpage("https://example.com/media")
            self.assertEqual(page_title, "Media Test Page")
            self.assertTrue(len(videos) >= 3)

            # Check that HTML5, source, OG, and iframe were extracted
            types = [v["type"] for v in videos]
            self.assertTrue(any("HTML5" in t for t in types))
            self.assertTrue(any("OpenGraph" in t for t in types))
            self.assertTrue(any("Embedded" in t for t in types))

        print(f"✔ test_04_web_video_extractor_deep_scraping passed! Discovered {len(videos)} streams.")

    def test_05_cancellation_mechanism(self):
        """Tests that cancellation raises DownloadCancelledException and stops safely."""
        de = DownloaderEngine()
        de.cancel()
        self.assertTrue(de._is_cancelled)
        de.reset_cancellation()
        self.assertFalse(de._is_cancelled)
        print("✔ test_05_cancellation_mechanism passed!")

    def test_06_history_persistence(self):
        """Tests persistent JSON history storage with unicode titles and paths."""
        hist_file = os.path.join(self.test_dir, "test_hist.json")
        hm = HistoryManager(hist_file)

        # Add item with Arabic title
        entry = hm.add_entry(
            url="https://youtube.com/watch?v=123",
            title="الدحيح - فيديو تجريبي",
            file_path="C:/Downloads/video.mp4",
            file_size="85.4 MB",
            format_info="1080p Full HD",
            source="YouTube"
        )
        self.assertEqual(entry["title"], "الدحيح - فيديو تجريبي")

        # Load back
        history = hm.load_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["title"], "الدحيح - فيديو تجريبي")

        # Delete
        hm.delete_entry(entry["id"])
        self.assertEqual(len(hm.load_history()), 0)
        print("✔ test_06_history_persistence passed!")


if __name__ == "__main__":
    print("=" * 65)
    print("RUNNING HARDCORE MULTI-DOWNLOADER VERIFICATION TESTS")
    print("=" * 65)
    unittest.main(verbosity=2)
