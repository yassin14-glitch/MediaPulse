"""Core download engine powered by yt-dlp with thread-safe progress tracking, cancellation, and robust error handling."""
import json
import os
import re
import sys
import threading
import time
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import yt_dlp
from core.errors import map_error_to_human_message
from core.ffmpeg_manager import FFmpegManager
from core.logger import get_logger, log_exception

logger = get_logger()
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".multimedia_downloader", "config.json")


def normalize_video_url(url: str) -> str:
    """Normalizes video URLs (e.g. Instagram /reels/ -> /reel/, stripping tracking queries)."""
    if not url:
        return ""
    url = url.strip()
    # Normalize Instagram /reels/ -> /reel/
    url = re.sub(r'instagram\.com/reels/', 'instagram.com/reel/', url, flags=re.IGNORECASE)
    # Strip tracking query params for social sites that can break extractor routing
    if any(domain in url.lower() for domain in ["instagram.com", "tiktok.com", "twitter.com", "x.com"]):
        try:
            parsed = urlparse(url)
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if not clean.endswith("/") and ("instagram.com" in clean or "tiktok.com" in clean):
                clean += "/"
            return clean
        except Exception:
            pass
    return url


def check_playlist_url(url: str) -> Dict[str, Any]:
    """Analyzes a URL to see if it contains a YouTube playlist, single video with playlist, or pure video."""
    result = {
        "is_youtube": False,
        "has_playlist": False,
        "has_video": False,
        "is_single_and_playlist": False,
        "is_pure_playlist": False,
        "video_id": None,
        "playlist_id": None,
        "single_url": None,
        "playlist_url": None
    }
    if not url or not str(url).strip():
        return result

    raw_url = str(url).strip()
    try:
        parsed = urlparse(raw_url)
        netloc = parsed.netloc.lower()
        if not ("youtube.com" in netloc or "youtu.be" in netloc):
            return result

        result["is_youtube"] = True
        qs = parse_qs(parsed.query)

        playlist_id = None
        if "list" in qs and qs["list"]:
            playlist_id = qs["list"][0]

        video_id = None
        if "youtu.be" in netloc:
            path_parts = [p for p in parsed.path.split("/") if p]
            if path_parts:
                video_id = path_parts[0]
        elif "youtube.com" in netloc:
            if "v" in qs and qs["v"]:
                video_id = qs["v"][0]
            elif "/embed/" in parsed.path:
                path_parts = [p for p in parsed.path.split("/embed/") if p]
                if path_parts:
                    video_id = path_parts[0].split("/")[0]
            elif "/v/" in parsed.path:
                path_parts = [p for p in parsed.path.split("/v/") if p]
                if path_parts:
                    video_id = path_parts[0].split("/")[0]
            elif "/shorts/" in parsed.path:
                path_parts = [p for p in parsed.path.split("/shorts/") if p]
                if path_parts:
                    video_id = path_parts[0].split("/")[0]

        result["video_id"] = video_id
        result["playlist_id"] = playlist_id
        result["has_video"] = bool(video_id)
        result["has_playlist"] = bool(playlist_id)
        result["is_single_and_playlist"] = bool(video_id and playlist_id)
        result["is_pure_playlist"] = bool(playlist_id and not video_id)

        if video_id:
            result["single_url"] = f"https://www.youtube.com/watch?v={video_id}"
        if playlist_id:
            result["playlist_url"] = f"https://www.youtube.com/playlist?list={playlist_id}"

        return result
    except Exception as e:
        logger.debug(f"Error checking playlist URL {url}: {e}")
        return result


def parse_time_to_seconds(time_str: Optional[str]) -> Optional[int]:
    """Parses HH:MM:SS or MM:SS or seconds string to integer seconds."""
    if not time_str or not str(time_str).strip():
        return None
    s = str(time_str).strip()
    try:
        if ":" not in s:
            return int(float(s))
        parts = [int(p) for p in s.split(":")]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except Exception:
        pass
    return None


def get_installed_browsers() -> List[str]:

    """Detects available web browsers on the user's system."""
    browsers = []
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if os.path.isdir(os.path.join(appdata, "Mozilla", "Firefox", "Profiles")):
            browsers.append("firefox")
        if os.path.isdir(os.path.join(localappdata, "Google", "Chrome", "User Data")):
            browsers.append("chrome")
        if os.path.isdir(os.path.join(localappdata, "Microsoft", "Edge", "User Data")):
            browsers.append("edge")
        if os.path.isdir(os.path.join(localappdata, "BraveSoftware", "Brave-Browser", "User Data")):
            browsers.append("brave")
        if os.path.isdir(os.path.join(appdata, "Opera Software", "Opera Stable")):
            browsers.append("opera")
    else:
        browsers = ["firefox", "chrome", "edge"]
    return browsers if browsers else ["firefox", "chrome", "edge"]


def get_browser_cookies_setting() -> str:
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return cfg.get("browser_cookies", "auto")
    except Exception:
        pass
    return "auto"


class DownloadCancelledException(Exception):
    """Raised when the user cancels an ongoing download."""
    pass


class DownloaderEngine:
    """Thread-safe download manager with progress reporting and cancellation."""

    _cached_working_browser: Optional[str] = None

    def __init__(self):
        self._is_cancelled = False
        self._current_ydl: Optional[yt_dlp.YoutubeDL] = None
        self._lock = threading.Lock()
        self.last_downloaded_file: Optional[str] = None

    @classmethod
    def get_candidate_browsers(cls) -> List[str]:
        """Returns ordered list of browsers to try for cookie extraction."""
        setting = get_browser_cookies_setting()
        if setting == "none":
            return []
        if setting and setting != "auto":
            return [setting]

        # Auto mode: prioritize any previously confirmed working browser
        installed = get_installed_browsers()
        ordered = []
        if cls._cached_working_browser and cls._cached_working_browser in installed:
            ordered.append(cls._cached_working_browser)
        for b in ["firefox", "chrome", "edge", "brave", "opera"]:
            if b in installed and b not in ordered:
                ordered.append(b)
        return ordered if ordered else ["firefox", "chrome", "edge"]


    def cancel(self):
        """Signals current download to abort."""
        with self._lock:
            self._is_cancelled = True
        logger.info("Cancellation signal sent to DownloaderEngine.")

    def reset_cancellation(self):
        with self._lock:
            self._is_cancelled = False

    @staticmethod
    def format_bytes(num_bytes: Optional[float]) -> str:
        """Converts bytes to human readable string (KB, MB, GB)."""
        if not num_bytes or num_bytes <= 0:
            return "0 B"
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if abs(num_bytes) < 1024.0:
                return f"{num_bytes:.1f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.1f} PB"

    @staticmethod
    def format_eta(seconds: Optional[int]) -> str:
        """Converts seconds into MM:SS or HH:MM:SS format."""
        if seconds is None:
            return "--:--"
        try:
            seconds = int(seconds)
            if seconds < 0:
                return "--:--"
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            if h > 0:
                return f"{h:02d}:{m:02d}:{s:02d}"
            return f"{m:02d}:{s:02d}"
        except Exception:
            return "--:--"

    def _parse_extracted_info(self, info: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Parses raw yt-dlp info dictionary into clean application data structure."""
        # If playlist
        is_playlist = "entries" in info and info["entries"]
        if is_playlist:
            entries = [e for e in info["entries"] if e]
            first_entry = entries[0] if entries else {}
            return {
                "is_playlist": True,
                "title": info.get("title", "Playlist"),
                "count": len(entries),
                "uploader": info.get("uploader", first_entry.get("uploader", "Unknown")),
                "thumbnail": info.get("thumbnails", [{}])[-1].get("url", first_entry.get("thumbnail", "")),
                "duration": sum([e.get("duration", 0) or 0 for e in entries if e]),
                "original_info": info
            }

        # Single video
        formats = info.get("formats", [])
        resolutions = set()
        has_audio = False
        has_video = False

        for f in formats:
            h = f.get("height")
            if h and isinstance(h, int) and h > 0:
                resolutions.add(h)
            if f.get("vcodec") != "none":
                has_video = True
            if f.get("acodec") != "none":
                has_audio = True

        sorted_res = sorted(list(resolutions), reverse=True)
        res_labels = [f"{r}p" for r in sorted_res]

        # Best thumbnail
        thumbnails = info.get("thumbnails", [])
        thumb_url = info.get("thumbnail", "")
        if thumbnails:
            valid_thumbs = [t for t in thumbnails if t.get("url")]
            if valid_thumbs:
                thumb_url = valid_thumbs[-1].get("url", thumb_url)

        return {
            "is_playlist": False,
            "title": info.get("title", "Unknown Title"),
            "uploader": info.get("uploader") or info.get("channel") or "Unknown Channel",
            "duration": info.get("duration", 0),
            "view_count": info.get("view_count", 0),
            "thumbnail": thumb_url,
            "webpage_url": info.get("webpage_url", url),
            "extractor": info.get("extractor_key", "Generic"),
            "available_resolutions": res_labels,
            "has_video": has_video,
            "has_audio": has_audio,
            "original_info": info
        }

    def fetch_info(self, url: str) -> Dict[str, Any]:
        """Fetches metadata for a URL with auto-cookie fallback for Instagram, TikTok, and social sites."""
        if not url or not url.strip():
            raise RuntimeError("No URL provided. Please enter a video link.")

        url = normalize_video_url(url)
        ffmpeg_path = FFmpegManager.get_ffmpeg_path()
        base_ydl_opts: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
            },
        }
        if ffmpeg_path:
            base_ydl_opts["ffmpeg_location"] = ffmpeg_path

        # If a working browser is already known, apply it directly
        candidate_browsers = self.get_candidate_browsers()
        is_cookie_heavy_site = any(d in url.lower() for d in ["instagram.com", "facebook.com", "tiktok.com"])

        # Determine attempt sequence
        attempts = []
        if self._cached_working_browser:
            attempts.append(self._cached_working_browser)
        elif is_cookie_heavy_site and candidate_browsers:
            attempts.extend(candidate_browsers)

        # Also include anonymous attempt if not already tried
        if not is_cookie_heavy_site:
            attempts.insert(0, None)

        last_error = None
        for b in attempts:
            try:
                opts = dict(base_ydl_opts)
                if b:
                    opts["cookiesfrombrowser"] = (b,)
                    opts.pop("http_headers", None)
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info:
                        if b:
                            DownloaderEngine._cached_working_browser = b
                            logger.info(f"Successfully extracted media using {b} browser cookies.")
                        return self._parse_extracted_info(info, url)
            except Exception as e:
                last_error = e
                logger.debug(f"Extraction attempt with browser={b} failed: {e}")

        # If initial attempts failed, try remaining candidate browsers
        for b in candidate_browsers:
            if b in attempts:
                continue
            try:
                opts = dict(base_ydl_opts)
                opts["cookiesfrombrowser"] = (b,)
                opts.pop("http_headers", None)
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info:
                        DownloaderEngine._cached_working_browser = b
                        logger.info(f"Successfully extracted media using {b} browser cookies.")
                        return self._parse_extracted_info(info, url)
            except Exception as e:
                last_error = e

        human_msg = map_error_to_human_message(last_error) if last_error else "Could not retrieve media info."
        if "instagram.com" in url.lower() and ("login" in str(last_error).lower() or "empty media" in str(last_error).lower()):
            human_msg = (
                "Instagram requires login cookies to access this Reel or post. "
                "Please make sure you are logged into Instagram in your browser (Firefox / Edge / Chrome) "
                "or configure your browser under Settings."
            )
        log_exception(f"Error fetching info for URL '{url}'", last_error)
        raise RuntimeError(human_msg)

    def fetch_playlist_info(self, url: str) -> Dict[str, Any]:
        """Fetches flat playlist metadata quickly without downloading or deep video format resolution."""
        if not url or not url.strip():
            raise RuntimeError("No URL provided for playlist.")

        chk = check_playlist_url(url)
        playlist_url = chk["playlist_url"] if chk["has_playlist"] else url

        ffmpeg_path = FFmpegManager.get_ffmpeg_path()
        base_ydl_opts: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": "in_playlist",
            "ignoreerrors": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
            },
        }
        if ffmpeg_path:
            base_ydl_opts["ffmpeg_location"] = ffmpeg_path

        candidate_browsers = self.get_candidate_browsers()
        attempts = []
        if self._cached_working_browser:
            attempts.append(self._cached_working_browser)
        attempts.append(None)
        if candidate_browsers:
            for b in candidate_browsers:
                if b not in attempts:
                    attempts.append(b)

        last_error = None
        raw_info = None

        for b in attempts:
            try:
                opts = dict(base_ydl_opts)
                if b:
                    opts["cookiesfrombrowser"] = (b,)
                    opts.pop("http_headers", None)
                with yt_dlp.YoutubeDL(opts) as ydl:
                    raw_info = ydl.extract_info(playlist_url, download=False)
                    if raw_info:
                        if b:
                            DownloaderEngine._cached_working_browser = b
                        break
            except Exception as e:
                last_error = e

        if not raw_info:
            human_msg = map_error_to_human_message(last_error) if last_error else "Could not load playlist."
            raise RuntimeError(human_msg)

        playlist_title = raw_info.get("title") or "YouTube Playlist"
        playlist_id = raw_info.get("id") or chk.get("playlist_id") or ""
        uploader = raw_info.get("uploader") or raw_info.get("channel") or "Unknown Creator"

        raw_entries = raw_info.get("entries")
        if raw_entries is None:
            raw_entries = []
        elif hasattr(raw_entries, "__iter__") and not isinstance(raw_entries, list):
            try:
                raw_entries = list(raw_entries)
            except Exception:
                raw_entries = []

        formatted_entries: List[Dict[str, Any]] = []
        idx = 1
        for entry in raw_entries:
            if not entry:
                continue

            vid_id = entry.get("id") or ""
            title = entry.get("title") or f"Video {idx}"
            duration = entry.get("duration")

            # Check for unavailable, private or deleted video
            title_lower = title.lower()
            is_unavailable = (
                title in ["[Private video]", "[Deleted video]", "[Blocked video]"]
                or "private video" in title_lower
                or "deleted video" in title_lower
                or entry.get("availability") in ["private", "subscriber_only", "needs_auth"]
                or not vid_id
            )

            # Determine thumbnail
            thumb_url = ""
            if vid_id:
                thumb_url = f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg"
            elif entry.get("thumbnails"):
                thumb_url = entry["thumbnails"][-1].get("url", "")
            elif entry.get("thumbnail"):
                thumb_url = entry["thumbnail"]

            duration_str = self.format_eta(duration) if duration else "--:--"

            formatted_entries.append({
                "index": idx,
                "id": vid_id,
                "title": title,
                "duration": duration or 0,
                "duration_str": duration_str,
                "uploader": entry.get("uploader") or entry.get("channel") or uploader,
                "thumbnail": thumb_url,
                "url": f"https://www.youtube.com/watch?v={vid_id}" if vid_id else entry.get("url", ""),
                "is_available": not is_unavailable
            })
            idx += 1

        return {
            "is_playlist": True,
            "playlist_id": playlist_id,
            "title": playlist_title,
            "uploader": uploader,
            "count": len(formatted_entries),
            "is_empty": len(formatted_entries) == 0,
            "entries": formatted_entries
        }

    def download(
        self,
        url: str,
        output_dir: str,
        mode: str = "video",              # "video" or "audio"
        quality: str = "best",             # "best", "2160p", "1080p", "720p", "mp3", etc.
        container: str = "mp4",            # "mp4", "mkv", "mp3", "m4a", "wav", "flac", "opus", "webm"
        embed_subs: bool = False,
        embed_thumbnail: bool = False,
        embed_metadata: bool = True,
        sponsorblock: bool = False,
        filename_template: Optional[str] = None,
        speed_limit: Optional[str] = None,
        proxy: Optional[str] = None,
        trim_start: Optional[str] = None,
        trim_end: Optional[str] = None,
        playlist_items: Optional[str] = None,
        download_playlist: bool = False,
        playlist_index: Optional[int] = None,
        playlist_total: Optional[int] = None,
        prefix_index: bool = False,
        skip_if_exists: bool = True,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """Downloads the video/audio with progress feedback, cancellation support, and write safety."""
        self.reset_cancellation()
        self.last_downloaded_file = None

        if not url or not url.strip():
            return {
                "success": False,
                "title": "",
                "file_path": None,
                "file_size": "0 B",
                "format": "",
                "thumbnail": "",
                "url": url,
                "error": "No URL provided. Please enter a valid video link."
            }

        url = normalize_video_url(url.strip())

        # Check directory write permissions
        try:
            os.makedirs(output_dir, exist_ok=True)
            test_file = os.path.join(output_dir, f".write_test_{os.getpid()}_{int(time.time())}")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(test_file)
        except Exception as e:
            human_err = "Cannot write to the chosen download folder. Please select a folder with write permissions."
            log_exception(f"Folder write test failed for {output_dir}", e)
            if progress_callback:
                progress_callback({
                    "status": "error",
                    "percent": 0.0,
                    "message": human_err
                })
            return {
                "success": False,
                "title": "",
                "file_path": None,
                "file_size": "0 B",
                "format": "",
                "thumbnail": "",
                "url": url,
                "error": human_err
            }

        # Check if already downloaded (for resuming stopped playlists)
        if skip_if_exists and os.path.isdir(output_dir):
            try:
                extracted_id = None
                parsed_chk = check_playlist_url(url)
                if parsed_chk.get("video_id"):
                    extracted_id = parsed_chk["video_id"]
                elif "v=" in url:
                    extracted_id = url.split("v=")[1].split("&")[0]

                for fname in os.listdir(output_dir):
                    fpath = os.path.join(output_dir, fname)
                    if not os.path.isfile(fpath):
                        continue
                    if fpath.endswith(".part") or fpath.endswith(".ytdl"):
                        continue
                    if os.path.getsize(fpath) <= 1024:
                        continue

                    match = False
                    if prefix_index and playlist_index is not None:
                        prefix_pat = f"{playlist_index:02d} - "
                        if fname.startswith(prefix_pat):
                            match = True

                    if extracted_id and f"[{extracted_id}]" in fname:
                        match = True

                    if match:
                        fsize_str = self.format_bytes(os.path.getsize(fpath))
                        logger.info(f"Skipping already downloaded video: {fpath} ({fsize_str})")
                        if progress_callback:
                            progress_callback({
                                "status": "completed",
                                "percent": 100.0,
                                "file_path": fpath,
                                "size_str": fsize_str,
                                "message": "Already downloaded (skipped)"
                            })
                        return {
                            "success": True,
                            "skipped": True,
                            "title": fname,
                            "file_path": fpath,
                            "file_size": fsize_str,
                            "format": f"{quality} ({container})",
                            "thumbnail": "",
                            "url": url,
                            "error": None
                        }
            except Exception as e:
                logger.debug(f"Error checking existing file: {e}")

        ffmpeg_path = FFmpegManager.get_ffmpeg_path()
        last_hook_time = [0.0]

        def hook(d: Dict[str, Any]):
            with self._lock:
                if self._is_cancelled:
                    raise DownloadCancelledException("Download cancelled by user.")

            status = d.get("status", "downloading")
            if status == "downloading":
                now = time.time()
                # Throttle progress updates to at most 1 update per 120ms to avoid UI flooding
                if now - last_hook_time[0] < 0.12:
                    return
                last_hook_time[0] = now

                downloaded = d.get("downloaded_bytes", 0) or 0
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                speed = d.get("speed")
                eta = d.get("eta")
                percent = (downloaded / total * 100) if total > 0 else 0.0

                if percent <= 0.0 and d.get("_percent_str"):
                    try:
                        clean_p = d["_percent_str"].replace("%", "").strip()
                        percent = float(clean_p)
                    except Exception:
                        pass

                downloaded_str = self.format_bytes(downloaded)
                total_str = self.format_bytes(total) if total > 0 else "--"
                size_str = f"{downloaded_str} / {total_str}" if total > 0 else f"{downloaded_str} downloaded"

                info_dict = {
                    "status": "downloading",
                    "percent": min(percent, 100.0),
                    "downloaded_bytes": downloaded,
                    "total_bytes": total,
                    "downloaded_str": downloaded_str,
                    "total_str": total_str,
                    "size_str": size_str,
                    "speed_str": f"{self.format_bytes(speed)}/s" if speed else "--",
                    "eta_str": self.format_eta(eta),
                    "filename": os.path.basename(d.get("filename", "video")),
                }
                if progress_callback:
                    progress_callback(info_dict)

            elif status == "finished":
                filename = d.get("filename")
                if filename:
                    self.last_downloaded_file = filename
                if progress_callback:
                    progress_callback({
                        "status": "processing",
                        "percent": 100.0,
                        "filename": os.path.basename(filename) if filename else "",
                        "size_str": "Merging streams with FFmpeg...",
                        "speed_str": "Merging...",
                        "eta_str": "--:--",
                        "message": "Processing & merging media streams..."
                    })

        # Template formatting
        default_tmpl = "%(title).160B [%(id)s].%(ext)s"
        if prefix_index and playlist_index is not None:
            default_tmpl = f"{playlist_index:02d} - %(title).160B [%(id)s].%(ext)s"
        tmpl = filename_template if filename_template and filename_template.strip() else default_tmpl
        if "%(ext)s" not in tmpl:
            tmpl += ".%(ext)s"

        # Base YDL Options
        ydl_opts: Dict[str, Any] = {
            "outtmpl": os.path.join(output_dir, tmpl),
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
            "noplaylist": not download_playlist,
            "restrictfilenames": False,
            "windowsfilenames": True,
            "trim_file_name": 160,
            "continuedl": True,
            "retries": 10,
            "fragment_retries": 10,
            "skip_unavailable_fragments": True,
            "updatetime": False,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
            },
        }

        if ffmpeg_path:
            ydl_opts["ffmpeg_location"] = ffmpeg_path

        # Speed limit
        if speed_limit and speed_limit.lower() not in ["none", "unlimited", ""]:
            try:
                num = float(re.sub(r"[^\d.]", "", speed_limit))
                if "m" in speed_limit.lower():
                    ydl_opts["ratelimit"] = int(num * 1024 * 1024)
                elif "k" in speed_limit.lower():
                    ydl_opts["ratelimit"] = int(num * 1024)
                else:
                    ydl_opts["ratelimit"] = int(num)
            except Exception:
                pass

        # Network Proxy
        if proxy and proxy.strip():
            ydl_opts["proxy"] = proxy.strip()

        # Playlist Items Range
        if playlist_items and playlist_items.strip():
            ydl_opts["playlist_items"] = playlist_items.strip()
            ydl_opts["noplaylist"] = False

        # Video Trimmer Range (download_ranges)
        s_sec = parse_time_to_seconds(trim_start) if trim_start else None
        e_sec = parse_time_to_seconds(trim_end) if trim_end else None
        if s_sec is not None or e_sec is not None:
            try:
                from yt_dlp.utils import download_range_func
                ydl_opts["download_ranges"] = download_range_func([], [[s_sec or 0, e_sec]])
                ydl_opts["force_keyframes_at_cuts"] = True
            except Exception as e:
                logger.warning(f"Could not configure download_ranges: {e}")

        # Browser Cookies
        candidate_browsers = self.get_candidate_browsers()
        is_cookie_heavy_site = any(d in url.lower() for d in ["instagram.com", "facebook.com", "tiktok.com"])

        if self._cached_working_browser:
            ydl_opts["cookiesfrombrowser"] = (self._cached_working_browser,)
            ydl_opts.pop("http_headers", None)
        elif is_cookie_heavy_site and candidate_browsers:
            ydl_opts["cookiesfrombrowser"] = (candidate_browsers[0],)
            ydl_opts.pop("http_headers", None)

        # Mode & Formats
        if mode == "audio":
            ydl_opts["format"] = "bestaudio/best"
            target_codec = container if container in ["mp3", "m4a", "wav", "flac", "opus"] else "mp3"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": target_codec,
                "preferredquality": "320" if target_codec == "mp3" else "0",
            }]
        else:
            clean_res = re.sub(r"[^\d]", "", quality)
            if quality == "best" or not clean_res:
                ydl_opts["format"] = "bestvideo+bestaudio/best"
            else:
                h = int(clean_res)
                ydl_opts["format"] = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"

            target_container = container if container in ["mp4", "mkv", "webm"] else "mp4"
            ydl_opts["merge_output_format"] = target_container

        # Subtitles
        if embed_subs and ffmpeg_path:
            ydl_opts["writesubtitles"] = True
            ydl_opts["writeautomaticsub"] = True
            ydl_opts["subtitleslangs"] = ["all", "-live_chat"]
            if "postprocessors" not in ydl_opts:
                ydl_opts["postprocessors"] = []
            ydl_opts["postprocessors"].append({
                "key": "FFmpegEmbedSubtitle"
            })

        # Thumbnail embedding
        if embed_thumbnail and ffmpeg_path:
            ydl_opts["writethumbnail"] = True
            if "postprocessors" not in ydl_opts:
                ydl_opts["postprocessors"] = []
            ydl_opts["postprocessors"].append({
                "key": "EmbedThumbnail",
                "already_have_thumbnail": False
            })

        # Metadata embedding
        if embed_metadata and ffmpeg_path:
            if "postprocessors" not in ydl_opts:
                ydl_opts["postprocessors"] = []
            ydl_opts["postprocessors"].append({
                "key": "FFmpegMetadata",
                "add_metadata": True,
                "add_chapters": True
            })

        # SponsorBlock (Auto-skip sponsored segments)
        if sponsorblock:
            if "postprocessors" not in ydl_opts:
                ydl_opts["postprocessors"] = []
            ydl_opts["postprocessors"].append({
                "key": "SponsorBlock",
                "categories": ["sponsor", "intro", "outro", "selfpromo", "preview", "filler"]
            })
            ydl_opts["postprocessors"].append({
                "key": "ModifyChapters",
                "remove_sponsor_segments": ["sponsor", "intro", "outro", "selfpromo", "preview", "filler"]
            })


        # Execute Download
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self._current_ydl = ydl
                info = ydl.extract_info(url, download=True)

                final_filepath = None
                if info:
                    if "requested_downloads" in info and info["requested_downloads"]:
                        final_filepath = info["requested_downloads"][0].get("filepath")
                    if not final_filepath:
                        try:
                            final_filepath = ydl.prepare_filename(info)
                        except Exception:
                            pass

                if not final_filepath or not os.path.exists(final_filepath):
                    final_filepath = self.last_downloaded_file

                if final_filepath and not os.path.exists(final_filepath):
                    base, _ = os.path.splitext(final_filepath)
                    for ext in [f".{container}", ".mp4", ".mkv", ".mp3", ".m4a", ".webm"]:
                        if os.path.exists(base + ext):
                            final_filepath = base + ext
                            break

                file_size_str = "0 B"
                if final_filepath and os.path.exists(final_filepath):
                    file_size_str = self.format_bytes(os.path.getsize(final_filepath))

                title = info.get("title", "Video") if info else "Video"
                thumbnail = info.get("thumbnail", "") if info else ""

                if progress_callback:
                    progress_callback({
                        "status": "completed",
                        "percent": 100.0,
                        "file_path": final_filepath,
                        "size_str": file_size_str,
                        "message": "Download completed successfully!"
                    })

                logger.info(f"Download completed successfully: {final_filepath} ({file_size_str})")

                return {
                    "success": True,
                    "title": title,
                    "file_path": final_filepath,
                    "file_size": file_size_str,
                    "format": f"{quality} ({container})",
                    "thumbnail": thumbnail,
                    "url": url,
                    "error": None
                }

        except DownloadCancelledException:
            logger.info(f"Download cancelled for URL: {url}")
            if progress_callback:
                progress_callback({
                    "status": "cancelled",
                    "percent": 0.0,
                    "message": "Download was cancelled."
                })
            return {
                "success": False,
                "title": "",
                "file_path": None,
                "file_size": "0 B",
                "format": "",
                "thumbnail": "",
                "url": url,
                "error": "Download was cancelled."
            }
        except Exception as e:
            err_str = str(e).lower()
            is_unavailable = any(term in err_str for term in [
                "private video", "is private", "deleted video", "has been deleted",
                "video unavailable", "has been removed", "sign in to confirm your age",
                "not available in your country", "blocked", "terms of service", "in your region"
            ])
            human_msg = map_error_to_human_message(e)
            if is_unavailable:
                human_msg = "Skipped: Video is private, deleted, or unavailable."
                logger.warning(f"Skipping unavailable video in playlist: {url} - {human_msg}")
                if progress_callback:
                    progress_callback({
                        "status": "error",
                        "percent": 0.0,
                        "message": human_msg
                    })
                return {
                    "success": False,
                    "skipped": True,
                    "is_unavailable": True,
                    "title": "Unavailable Video",
                    "file_path": None,
                    "file_size": "0 B",
                    "format": "",
                    "thumbnail": "",
                    "url": url,
                    "error": human_msg
                }

            log_exception(f"Download error on URL: {url}", e)
            if progress_callback:
                progress_callback({
                    "status": "error",
                    "percent": 0.0,
                    "message": human_msg
                })
            return {
                "success": False,
                "skipped": False,
                "is_unavailable": False,
                "title": "",
                "file_path": None,
                "file_size": "0 B",
                "format": "",
                "thumbnail": "",
                "url": url,
                "error": human_msg
            }
