"""FastAPI Web Server for the Universal Video Downloader with Queue, i18n, and Updater support."""
import json
import os
import re
import sys
import threading
from typing import Any, Dict, List, Optional

# Ensure standard output can handle unicode/Arabic text on Windows without crashing
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.downloader_engine import (
    DownloaderEngine,
    check_playlist_url,
    get_browser_cookies_setting,
    get_installed_browsers,
    normalize_video_url,
)
from core.ffmpeg_manager import FFmpegManager
from core.history_manager import HistoryManager
from core.i18n import (
    detect_system_language,
    get_available_languages,
    get_current_language,
    load_translations,
    set_current_language,
)
from core.logger import get_logger, log_exception
from core.queue_manager import QueueManager
from core.updater import (
    check_for_updates,
    get_current_version,
    get_update_status,
    perform_update,
    start_background_check,
)
from core.version import __app_name__, __version__
from core.web_extractor import WebVideoExtractor

logger = get_logger()
app = FastAPI(title=f"{__app_name__} API", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".multimedia_downloader", "config.json")


def load_config() -> Dict[str, Any]:
    defaults = {
        "download_dir": os.path.join(os.path.expanduser("~"), "Downloads", "VideoDownloads"),
        "language": "auto",
        "theme": "dark",
        "accent": "blue",
        "filename_template": "%(title).160B [%(id)s].%(ext)s",
        "video_format": "mp4",
        "video_quality": "best",
        "audio_format": "mp3",
        "audio_quality": "320k",
        "max_concurrent": 1,
        "speed_limit": "unlimited",
        "proxy": "",
        "browser_cookies": "auto",
        "subtitles_enabled": False,
        "subtitles_embed": False,
        "embed_thumbnail": False,
        "embed_metadata": True,
        "sponsorblock": False,
        "playlist_mode": "all",
        "clipboard_watcher": True,
        "notifications": True,
        "sound": True,
        "start_with_windows": False,
        "minimize_to_tray": False,
        "first_run_completed": False
    }
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                defaults.update(saved)
    except Exception:
        pass
    return defaults


def save_config(cfg: Dict[str, Any]):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving config: {e}")


config_state = load_config()
current_download_dir = config_state.get("download_dir", os.path.join(os.path.expanduser("~"), "Downloads", "VideoDownloads"))
set_current_language(config_state.get("language", "auto"))

history_mgr = HistoryManager()
extractor = WebVideoExtractor()
queue_mgr = QueueManager(history_mgr=history_mgr)
active_downloads: Dict[str, Dict[str, Any]] = {}

ffmpeg_download_state: Dict[str, Any] = {
    "is_downloading": False,
    "percent": 0.0,
    "status": "idle",
    "message": ""
}

# Start background yt-dlp update check on startup
start_background_check()


class FetchInfoRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    mode: str = "video"           # "video" or "audio"
    quality: str = "best"
    container: str = "mp4"
    output_dir: Optional[str] = None
    title: Optional[str] = None
    trim_start: Optional[str] = None
    trim_end: Optional[str] = None
    sponsorblock: bool = False
    embed_subs: bool = False
    embed_thumbnail: bool = False
    speed_limit: Optional[str] = None
    proxy: Optional[str] = None


class QueueAddRequest(BaseModel):
    url: str
    mode: str = "video"
    quality: str = "best"
    container: str = "mp4"
    output_dir: Optional[str] = None
    title: Optional[str] = None
    trim_start: Optional[str] = None
    trim_end: Optional[str] = None
    sponsorblock: bool = False
    embed_subs: bool = False
    speed_limit: Optional[str] = None


class BatchAddRequest(BaseModel):
    urls: List[str]
    mode: str = "video"
    quality: str = "best"
    container: str = "mp4"
    output_dir: Optional[str] = None


class PlaylistQueueItem(BaseModel):
    url: str
    title: str
    index: int


class PlaylistQueueAddRequest(BaseModel):
    playlist_id: Optional[str] = None
    playlist_title: str
    items: List[PlaylistQueueItem]
    mode: str = "video"
    quality: str = "best"
    container: str = "mp4"
    output_dir: Optional[str] = None
    create_subfolder: bool = True
    prefix_index: bool = True


class QueueReorderRequest(BaseModel):
    order: List[str]


class PathRequest(BaseModel):
    path: Optional[str] = None


class DeleteHistoryRequest(BaseModel):
    id: str


class CookieSettingRequest(BaseModel):
    browser: str


class LanguageSettingRequest(BaseModel):
    language: str


class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, Any]


@app.get("/api/status")
def get_status():
    global current_download_dir
    avail, ver, path = FFmpegManager.get_status()
    up_status = get_update_status()
    cfg = load_config()
    return {
        "app_name": __app_name__,
        "version": __version__,
        "ffmpeg_available": avail,
        "ffmpeg_version": ver,
        "ffmpeg_path": path,
        "download_dir": current_download_dir,
        "ytdlp_version": get_current_version(),
        "ytdlp_update": up_status,
        "browser_cookies": get_browser_cookies_setting(),
        "available_browsers": get_installed_browsers(),
        "config": cfg,
        "language": get_current_language(),
        "system_language": detect_system_language()
    }


# --- i18n Locales Endpoints ---

@app.get("/api/locales")
def get_locales():
    return {
        "languages": get_available_languages(),
        "current": get_current_language(),
        "system": detect_system_language()
    }


@app.get("/api/locales/{code}")
def get_locale_strings(code: str):
    return load_translations(code)


@app.post("/api/settings/language")
def set_language_endpoint(req: LanguageSettingRequest):
    set_current_language(req.language)
    cfg = load_config()
    cfg["language"] = req.language
    save_config(cfg)
    return {"success": True, "language": req.language}


# --- Settings Endpoints ---

@app.get("/api/settings/all")
def get_all_settings():
    return load_config()


@app.post("/api/settings/save")
def save_all_settings(req: SettingsUpdateRequest):
    global current_download_dir
    cfg = load_config()
    cfg.update(req.settings)
    if "download_dir" in req.settings and os.path.isdir(req.settings["download_dir"]):
        current_download_dir = req.settings["download_dir"]
    if "language" in req.settings:
        set_current_language(req.settings["language"])
    if "browser_cookies" in req.settings:
        DownloaderEngine._cached_working_browser = None
    save_config(cfg)
    return {"success": True, "settings": cfg}


@app.get("/api/settings/export")
def export_settings():
    return JSONResponse(content=load_config())


@app.post("/api/settings/import")
def import_settings(req: SettingsUpdateRequest):
    global current_download_dir
    cfg = req.settings
    if "download_dir" in cfg and os.path.isdir(cfg["download_dir"]):
        current_download_dir = cfg["download_dir"]
    save_config(cfg)
    return {"success": True, "settings": cfg}


@app.post("/api/settings/clear-cache")
def clear_cache():
    cleaned = 0
    try:
        tmp_dir = os.path.join(os.path.expanduser("~"), ".multimedia_downloader")
        if os.path.exists(tmp_dir):
            for f in os.listdir(tmp_dir):
                if f.startswith(".write_test") or f.endswith(".part") or f.endswith(".ytdl"):
                    try:
                        os.remove(os.path.join(tmp_dir, f))
                        cleaned += 1
                    except Exception:
                        pass
    except Exception:
        pass
    return {"success": True, "cleaned": cleaned}


@app.post("/api/settings/browser-cookies")
def set_browser_cookies(req: CookieSettingRequest):
    try:
        cfg = load_config()
        cfg["browser_cookies"] = req.browser
        save_config(cfg)
        DownloaderEngine._cached_working_browser = None
        return {"success": True, "browser_cookies": req.browser}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/choose-folder")
def choose_folder():
    """Opens native Windows folder chooser dialog and saves selection."""
    global current_download_dir
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askdirectory(
            initialdir=current_download_dir,
            title="Choose Where to Save Videos"
        )
        root.destroy()
        if selected and os.path.isdir(selected):
            current_download_dir = os.path.normpath(selected)
            cfg = load_config()
            cfg["download_dir"] = current_download_dir
            save_config(cfg)
            return {"success": True, "folder": current_download_dir}
        return {"success": False, "folder": current_download_dir}
    except Exception as e:
        logger.error(f"Folder chooser dialog error: {e}")
        return {"success": False, "error": str(e), "folder": current_download_dir}


@app.post("/api/open-folder")
def open_folder(req: PathRequest):
    folder = req.path or current_download_dir
    if not os.path.exists(folder):
        return {"success": False, "error": "Folder does not exist"}

    if sys.platform == "win32":
        import subprocess
        subprocess.run(["explorer", os.path.normpath(folder)])
    else:
        import subprocess
        subprocess.run(["xdg-open", folder])
    return {"success": True}


@app.post("/api/play-file")
def play_file(req: PathRequest):
    if not req.path or not os.path.exists(req.path):
        raise HTTPException(status_code=404, detail="File does not exist")

    try:
        if sys.platform == "win32":
            os.startfile(os.path.normpath(req.path))
        else:
            import subprocess
            subprocess.run(["xdg-open", req.path])
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not open file: {e}")


@app.get("/api/clipboard/check")
def check_clipboard():
    """Checks if system clipboard has a valid media URL."""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        if text and any(d in text.lower() for d in ["youtube.com", "youtu.be", "instagram.com", "tiktok.com", "twitter.com", "x.com", "vimeo.com", "reddit.com"]):
            return {"has_video_url": True, "url": text.strip()}
    except Exception:
        pass
    return {"has_video_url": False, "url": None}


# --- FFmpeg On-Demand Download Endpoints ---

@app.post("/api/ffmpeg/download")
def start_ffmpeg_download():
    global ffmpeg_download_state
    if ffmpeg_download_state["is_downloading"]:
        return {"success": False, "message": "Download already in progress"}

    ffmpeg_download_state["is_downloading"] = True
    ffmpeg_download_state["percent"] = 0.0
    ffmpeg_download_state["status"] = "starting"
    ffmpeg_download_state["message"] = "Connecting to download server..."

    def _worker():
        global ffmpeg_download_state
        def _cb(pct, msg):
            ffmpeg_download_state["percent"] = pct
            ffmpeg_download_state["message"] = msg
            ffmpeg_download_state["status"] = "downloading"
        success, msg = FFmpegManager.download_ffmpeg(progress_callback=_cb)
        ffmpeg_download_state["is_downloading"] = False
        ffmpeg_download_state["status"] = "completed" if success else "error"
        ffmpeg_download_state["percent"] = 100.0 if success else 0.0
        ffmpeg_download_state["message"] = msg

    threading.Thread(target=_worker, daemon=True, name="FFmpegDownloader").start()
    return {"success": True, "message": "FFmpeg download started"}


@app.get("/api/ffmpeg/download-status")
def get_ffmpeg_download_status():
    global ffmpeg_download_state
    return ffmpeg_download_state


# --- YouTube & Web Sniffer Endpoints ---

@app.post("/api/youtube/info")
def get_youtube_info(req: FetchInfoRequest):
    if not req.url:
        raise HTTPException(status_code=400, detail="No URL provided. Please enter a valid video link.")
    downloader = DownloaderEngine()
    try:
        info = downloader.fetch_info(req.url)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/youtube/check-url")
def check_url_endpoint(req: FetchInfoRequest):
    return check_playlist_url(req.url)


@app.post("/api/youtube/playlist-info")
def get_playlist_info_endpoint(req: FetchInfoRequest):
    if not req.url:
        raise HTTPException(status_code=400, detail="No URL provided for playlist.")
    downloader = DownloaderEngine()
    try:
        info = downloader.fetch_playlist_info(req.url)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@app.post("/api/web/extract")
def extract_web_streams(req: FetchInfoRequest):
    if not req.url:
        raise HTTPException(status_code=400, detail="Empty URL provided")
    res = extractor.extract_streams(req.url)
    return res


# --- Download Execution Endpoints ---

@app.post("/api/download")
def start_download(req: DownloadRequest):
    global current_download_dir
    downloader = DownloaderEngine()
    task_id = str(len(active_downloads) + 1)
    target_dir = req.output_dir or current_download_dir
    os.makedirs(target_dir, exist_ok=True)

    cfg = load_config()

    active_downloads[task_id] = {
        "status": "starting",
        "percent": 0.0,
        "speed": "--",
        "eta": "--",
        "filename": "",
        "size": "0 B / 0 B",
        "downloaded": "0 B",
        "total": "--",
        "file_path": None,
        "result": None,
        "downloader": downloader
    }

    def run_worker():
        def progress_cb(d: Dict[str, Any]):
            task = active_downloads[task_id]
            task["status"] = d.get("status", "downloading")
            task["percent"] = d.get("percent", 0.0)
            task["speed"] = d.get("speed_str", "--")
            task["eta"] = d.get("eta_str", "--")
            task["filename"] = d.get("filename", "")
            task["size"] = d.get("size_str", "0 B")
            task["downloaded"] = d.get("downloaded_str", "0 B")
            task["total"] = d.get("total_str", "--")
            if d.get("file_path"):
                task["file_path"] = d.get("file_path")

        res = downloader.download(
            url=req.url,
            output_dir=target_dir,
            mode=req.mode,
            quality=req.quality,
            container=req.container,
            embed_subs=req.embed_subs or cfg.get("subtitles_embed", False),
            embed_thumbnail=req.embed_thumbnail or cfg.get("embed_thumbnail", False),
            embed_metadata=cfg.get("embed_metadata", True),
            sponsorblock=req.sponsorblock or cfg.get("sponsorblock", False),
            filename_template=cfg.get("filename_template"),
            speed_limit=req.speed_limit or cfg.get("speed_limit"),
            proxy=req.proxy or cfg.get("proxy"),
            trim_start=req.trim_start,
            trim_end=req.trim_end,
            progress_callback=progress_cb
        )
        task = active_downloads[task_id]
        task["result"] = res
        task["status"] = "completed" if res.get("success") else ("cancelled" if res.get("error") == "Download was cancelled." else "error")
        if res.get("file_path"):
            task["file_path"] = res.get("file_path")

        if res.get("success"):
            history_mgr.add_entry(
                url=req.url,
                title=res.get("title") or req.title or "Video",
                file_path=res.get("file_path", ""),
                file_size=res.get("file_size", "0 B"),
                format_info=res.get("format", ""),
                source="Web UI"
            )

    threading.Thread(target=run_worker, daemon=True, name=f"DownloadTask-{task_id}").start()
    return {"task_id": task_id, "status": "started", "output_dir": target_dir}


@app.get("/api/download/status/{task_id}")
def check_download_status(task_id: str):
    task = active_downloads.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "status": task.get("status"),
        "percent": task.get("percent", 0.0),
        "speed": task.get("speed", "--"),
        "eta": task.get("eta", "--"),
        "filename": task.get("filename", ""),
        "size": task.get("size", "0 B / 0 B"),
        "downloaded": task.get("downloaded", "0 B"),
        "total": task.get("total", "--"),
        "file_path": task.get("file_path") or (task.get("result", {}) or {}).get("file_path"),
        "result": task.get("result")
    }


@app.post("/api/download/cancel/{task_id}")
def cancel_download(task_id: str):
    task = active_downloads.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    downloader: DownloaderEngine = task.get("downloader")
    if downloader:
        downloader.cancel()
        task["status"] = "cancelled"
        return {"success": True}
    return {"success": False, "detail": "Downloader not found"}


# --- Queue Management Endpoints ---

@app.get("/api/queue")
def get_queue_tasks():
    return {"tasks": queue_mgr.get_all_tasks()}


@app.post("/api/queue/add")
def add_to_queue(req: QueueAddRequest):
    global current_download_dir
    target_dir = req.output_dir or current_download_dir
    task = queue_mgr.add_task(
        url=req.url,
        mode=req.mode,
        quality=req.quality,
        container=req.container,
        output_dir=target_dir,
        title=req.title or "Video",
        trim_start=req.trim_start,
        trim_end=req.trim_end,
        sponsorblock=req.sponsorblock,
        embed_subs=req.embed_subs,
        speed_limit=req.speed_limit
    )
    return {"success": True, "task": task.to_dict()}


@app.post("/api/queue/batch-add")
def batch_add_to_queue(req: BatchAddRequest):
    global current_download_dir
    target_dir = req.output_dir or current_download_dir
    added = []
    for raw_url in req.urls:
        url = raw_url.strip()
        if not url:
            continue
        task = queue_mgr.add_task(
            url=url,
            mode=req.mode,
            quality=req.quality,
            container=req.container,
            output_dir=target_dir,
            title="Batch Item"
        )
        added.append(task.to_dict())
    return {"success": True, "count": len(added), "tasks": added}


@app.post("/api/queue/add-playlist")
def add_playlist_to_queue(req: PlaylistQueueAddRequest):
    global current_download_dir
    base_dir = req.output_dir or current_download_dir
    if req.create_subfolder:
        safe_name = re.sub(r'[\\/*?:"<>|]', "", req.playlist_title).strip() or "Playlist"
        target_dir = os.path.join(base_dir, safe_name)
    else:
        target_dir = base_dir

    os.makedirs(target_dir, exist_ok=True)
    total_items = len(req.items)
    added = []

    for item in req.items:
        task = queue_mgr.add_task(
            url=item.url,
            mode=req.mode,
            quality=req.quality,
            container=req.container,
            output_dir=target_dir,
            title=item.title,
            playlist_id=req.playlist_id,
            playlist_title=req.playlist_title,
            playlist_index=item.index,
            playlist_total=total_items,
            prefix_index=req.prefix_index,
            skip_if_exists=True
        )
        added.append(task.to_dict())

    return {
        "success": True,
        "count": len(added),
        "playlist_title": req.playlist_title,
        "output_dir": target_dir,
        "tasks": added
    }


@app.post("/api/queue/reorder")
def reorder_queue(req: QueueReorderRequest):
    success = queue_mgr.reorder_tasks(req.order)
    return {"success": success}


@app.post("/api/queue/pause/{task_id}")
def pause_queue_task(task_id: str):
    success = queue_mgr.pause_task(task_id)
    return {"success": success}


@app.post("/api/queue/resume/{task_id}")
def resume_queue_task(task_id: str):
    success = queue_mgr.resume_task(task_id)
    return {"success": success}


@app.post("/api/queue/cancel/{task_id}")
def cancel_queue_task(task_id: str):
    success = queue_mgr.cancel_task(task_id)
    return {"success": success}


@app.post("/api/queue/remove/{task_id}")
def remove_queue_task(task_id: str):
    success = queue_mgr.remove_task(task_id)
    return {"success": success}


@app.post("/api/queue/clear")
def clear_completed_queue():
    queue_mgr.clear_completed()
    return {"success": True}


# --- History Endpoints ---

@app.get("/api/history")
def get_history():
    return {"history": history_mgr.load_history()}


@app.post("/api/history/delete")
def delete_history_item(req: DeleteHistoryRequest):
    history_mgr.delete_entry(req.id)
    return {"success": True}


@app.post("/api/history/clear")
def clear_history():
    history_mgr.clear_history()
    return {"success": True}


# --- Updater Endpoints ---

@app.get("/api/update/status")
def get_update_info():
    return get_update_status()


@app.post("/api/update/check")
def trigger_update_check():
    has_update, curr, latest = check_for_updates()
    return {
        "has_update": has_update,
        "current_version": curr,
        "latest_version": latest
    }


@app.post("/api/update/perform")
def trigger_update_perform():
    success, msg = perform_update()
    return {"success": success, "message": msg}


# Serve Static UI
def get_static_dir() -> str:
    candidates = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            candidates.append(os.path.join(meipass, "web", "static"))
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, "_internal", "web", "static"))
        candidates.append(os.path.join(exe_dir, "_internal", "static"))
        candidates.append(os.path.join(exe_dir, "web", "static"))
        candidates.append(os.path.join(exe_dir, "static"))
    candidates.append(os.path.join(os.path.dirname(__file__), "static"))
    candidates.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "static"))

    for c in candidates:
        if os.path.isdir(c) and os.path.exists(os.path.join(c, "modern.html")):
            return c
    return os.path.join(os.path.dirname(__file__), "static")


static_dir = get_static_dir()
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def serve_index():
    index_file = os.path.join(static_dir, "modern.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse("<h3>Web UI modern.html not found</h3>")
