"""Unit tests for the sequential download queue, pause, resume, and cancellation."""
import time
import pytest
from core.queue_manager import QueueManager, TaskState


def test_queue_add_and_get():
    qm = QueueManager()
    try:
        t1 = qm.add_task(url="https://example.com/1", title="Video 1")
        t2 = qm.add_task(url="https://example.com/2", title="Video 2")

        tasks = qm.get_all_tasks()
        assert len(tasks) >= 2
        ids = [t["id"] for t in tasks]
        assert t1.id in ids
        assert t2.id in ids
    finally:
        qm.shutdown()


def test_queue_pause_and_resume():
    qm = QueueManager()
    try:
        t = qm.add_task(url="https://example.com/pause_test", title="Pause Test")
        # Manually set to paused or pause while queued
        success = qm.pause_task(t.id)
        assert success is True
        
        # Check task state
        tasks = {task["id"]: task for task in qm.get_all_tasks()}
        assert tasks[t.id]["state"] == TaskState.PAUSED.value

        # Resume task
        res_success = qm.resume_task(t.id)
        assert res_success is True
        tasks_after = {task["id"]: task for task in qm.get_all_tasks()}
        assert tasks_after[t.id]["state"] == TaskState.QUEUED.value
    finally:
        qm.shutdown()


def test_queue_cancel_and_remove():
    qm = QueueManager()
    try:
        t = qm.add_task(url="https://example.com/cancel_test", title="Cancel Test")
        cancel_success = qm.cancel_task(t.id)
        assert cancel_success is True

        tasks = {task["id"]: task for task in qm.get_all_tasks()}
        assert tasks[t.id]["state"] == TaskState.CANCELLED.value

        # Remove task
        remove_success = qm.remove_task(t.id)
        assert remove_success is True
        ids = [task["id"] for task in qm.get_all_tasks()]
        assert t.id not in ids
    finally:
        qm.shutdown()


def test_queue_clear_completed():
    qm = QueueManager()
    try:
        t1 = qm.add_task(url="https://example.com/c1", title="C1")
        t2 = qm.add_task(url="https://example.com/c2", title="C2")
        qm.cancel_task(t1.id)
        
        # t1 is cancelled, t2 is queued
        qm.clear_completed()
        ids = [task["id"] for task in qm.get_all_tasks()]
        assert t1.id not in ids
        assert t2.id in ids
    finally:
        qm.shutdown()
