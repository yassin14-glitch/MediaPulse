"""Thread-safe download queue manager with sequential execution, pause, resume, and cancellation."""
import os
import threading
import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from core.downloader_engine import DownloaderEngine
from core.history_manager import HistoryManager
from core.logger import get_logger, log_exception

logger = get_logger()


class TaskState(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class DownloadTask:
    def __init__(
        self,
        url: str,
        mode: str = "video",
        quality: str = "best",
        container: str = "mp4",
        output_dir: str = "",
        title: str = "",
        trim_start: Optional[str] = None,
        trim_end: Optional[str] = None,
        sponsorblock: bool = False,
        embed_subs: bool = False,
        speed_limit: Optional[str] = None
    ):
        self.id = str(uuid.uuid4())[:8]
        self.url = url
        self.mode = mode
        self.quality = quality
        self.container = container
        self.output_dir = output_dir
        self.title = title or "Video"
        self.trim_start = trim_start
        self.trim_end = trim_end
        self.sponsorblock = sponsorblock
        self.embed_subs = embed_subs
        self.speed_limit = speed_limit
        self.state = TaskState.QUEUED
        self.percent = 0.0
        self.speed = "--"
        self.size = "0 B / 0 B"
        self.eta = "--"
        self.filename = ""
        self.file_path: Optional[str] = None
        self.error: Optional[str] = None
        self.engine: Optional[DownloaderEngine] = None
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "mode": self.mode,
            "quality": self.quality,
            "container": self.container,
            "output_dir": self.output_dir,
            "trim_start": self.trim_start,
            "trim_end": self.trim_end,
            "sponsorblock": self.sponsorblock,
            "state": self.state.value,
            "percent": self.percent,
            "speed": self.speed,
            "size": self.size,
            "eta": self.eta,
            "filename": self.filename,
            "file_path": self.file_path,
            "error": self.error
        }


class QueueManager:
    """Manages sequential queue execution, pause/resume, reordering, and cancellation."""

    def __init__(self, history_mgr: Optional[HistoryManager] = None):
        self.tasks: List[DownloadTask] = []
        self._lock = threading.Lock()
        self.history_mgr = history_mgr or HistoryManager()
        self._is_running = True
        self.current_task: Optional[DownloadTask] = None
        self._worker_thread = threading.Thread(target=self._queue_worker, daemon=True, name="QueueWorker")
        self._worker_thread.start()

    def add_task(
        self,
        url: str,
        mode: str = "video",
        quality: str = "best",
        container: str = "mp4",
        output_dir: str = "",
        title: str = "",
        trim_start: Optional[str] = None,
        trim_end: Optional[str] = None,
        sponsorblock: bool = False,
        embed_subs: bool = False,
        speed_limit: Optional[str] = None
    ) -> DownloadTask:
        task = DownloadTask(
            url, mode, quality, container, output_dir, title,
            trim_start=trim_start, trim_end=trim_end,
            sponsorblock=sponsorblock, embed_subs=embed_subs,
            speed_limit=speed_limit
        )
        with self._lock:
            self.tasks.append(task)
        logger.info(f"Task {task.id} added to queue for {url}")
        return task


    def pause_task(self, task_id: str) -> bool:
        """Pauses a downloading or queued task."""
        with self._lock:
            task = next((t for t in self.tasks if t.id == task_id), None)
            if not task:
                return False

            if task.state == TaskState.QUEUED:
                task.state = TaskState.PAUSED
                logger.info(f"Queued task {task.id} paused.")
                return True
            elif task.state == TaskState.DOWNLOADING and task.engine:
                task.state = TaskState.PAUSED
                task.engine.cancel()
                logger.info(f"Downloading task {task.id} signaled to pause.")
                return True
        return False

    def resume_task(self, task_id: str) -> bool:
        """Resumes a paused task, re-queueing it."""
        with self._lock:
            task = next((t for t in self.tasks if t.id == task_id), None)
            if not task or task.state != TaskState.PAUSED:
                return False

            task.state = TaskState.QUEUED
            task.error = None
            logger.info(f"Task {task.id} resumed and re-queued.")
            return True

    def cancel_task(self, task_id: str) -> bool:
        """Cancels a task permanently."""
        with self._lock:
            task = next((t for t in self.tasks if t.id == task_id), None)
            if not task:
                return False

            if task.state == TaskState.DOWNLOADING and task.engine:
                task.engine.cancel()

            task.state = TaskState.CANCELLED
            logger.info(f"Task {task.id} cancelled.")
            return True

    def remove_task(self, task_id: str) -> bool:
        """Removes a task from the queue."""
        with self._lock:
            task = next((t for t in self.tasks if t.id == task_id), None)
            if not task:
                return False
            if task.state == TaskState.DOWNLOADING and task.engine:
                task.engine.cancel()
            self.tasks = [t for t in self.tasks if t.id != task_id]
            logger.info(f"Task {task_id} removed from queue.")
            return True

    def clear_completed(self):
        """Clears all completed, error, or cancelled tasks."""
        with self._lock:
            self.tasks = [t for t in self.tasks if t.state in (TaskState.QUEUED, TaskState.DOWNLOADING, TaskState.PAUSED)]

    def reorder_tasks(self, ordered_ids: List[str]) -> bool:
        """Reorders queued tasks based on provided list of task IDs."""
        with self._lock:
            id_to_task = {t.id: t for t in self.tasks}
            reordered = []
            for tid in ordered_ids:
                if tid in id_to_task:
                    reordered.append(id_to_task.pop(tid))
            reordered.extend(id_to_task.values())
            self.tasks = reordered
            logger.info("Queue reordered successfully.")
            return True

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [t.to_dict() for t in self.tasks]

    def _queue_worker(self):
        """Sequential download worker."""
        while self._is_running:
            task_to_run = None
            with self._lock:
                for t in self.tasks:
                    if t.state == TaskState.QUEUED:
                        task_to_run = t
                        task_to_run.state = TaskState.DOWNLOADING
                        task_to_run.engine = DownloaderEngine()
                        self.current_task = task_to_run
                        break

            if not task_to_run:
                time.sleep(0.5)
                continue

            # Process the task
            logger.info(f"Queue worker starting task {task_to_run.id} ({task_to_run.url})")

            def progress_cb(d: Dict[str, Any]):
                task_to_run.percent = d.get("percent", task_to_run.percent)
                task_to_run.speed = d.get("speed_str", task_to_run.speed)
                task_to_run.size = d.get("size_str", task_to_run.size)
                task_to_run.eta = d.get("eta_str", task_to_run.eta)
                if d.get("filename"):
                    task_to_run.filename = d["filename"]

            try:
                res = task_to_run.engine.download(
                    url=task_to_run.url,
                    output_dir=task_to_run.output_dir,
                    mode=task_to_run.mode,
                    quality=task_to_run.quality,
                    container=task_to_run.container,
                    trim_start=task_to_run.trim_start,
                    trim_end=task_to_run.trim_end,
                    sponsorblock=task_to_run.sponsorblock,
                    embed_subs=task_to_run.embed_subs,
                    speed_limit=task_to_run.speed_limit,
                    progress_callback=progress_cb
                )


                with self._lock:
                    if task_to_run.state == TaskState.PAUSED:
                        # Left in paused state
                        pass
                    elif res.get("success"):
                        task_to_run.state = TaskState.COMPLETED
                        task_to_run.file_path = res.get("file_path")
                        task_to_run.title = res.get("title") or task_to_run.title
                        task_to_run.size = res.get("file_size") or task_to_run.size
                        task_to_run.percent = 100.0

                        # Save to history
                        self.history_mgr.add_entry(
                            url=task_to_run.url,
                            title=task_to_run.title,
                            file_path=task_to_run.file_path or "",
                            file_size=task_to_run.size,
                            format_info=res.get("format", ""),
                            source="Queue"
                        )
                    elif res.get("error") == "Download was cancelled.":
                        if task_to_run.state != TaskState.PAUSED:
                            task_to_run.state = TaskState.CANCELLED
                    else:
                        task_to_run.state = TaskState.ERROR
                        task_to_run.error = res.get("error", "Download failed.")

            except Exception as e:
                with self._lock:
                    task_to_run.state = TaskState.ERROR
                    task_to_run.error = str(e)
                log_exception(f"Unhandled exception in queue task {task_to_run.id}", e)

            finally:
                self.current_task = None
                time.sleep(0.5)

    def shutdown(self):
        """Gracefully aborts any running task and shuts down worker."""
        self._is_running = False
        with self._lock:
            for t in self.tasks:
                if t.state == TaskState.DOWNLOADING and t.engine:
                    t.engine.cancel()
