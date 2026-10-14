"""Tests running MediaPulse Pro from a completely clean external directory."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

SRC_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist", "MediaPulsePro")
CLEAN_DIR = os.path.join(tempfile.gettempdir(), "MediaPulse_CleanRun")

def run_clean_test():
    print(f"[*] Source distribution: {SRC_DIST}")
    print(f"[*] Target clean directory: {CLEAN_DIR}")

    if not os.path.exists(SRC_DIST):
        print(f"[FAIL] Source distribution does not exist: {SRC_DIST}")
        sys.exit(1)

    if os.path.exists(CLEAN_DIR):
        print("[*] Removing previous clean test folder...")
        shutil.rmtree(CLEAN_DIR, ignore_errors=True)

    print("[*] Copying distribution to clean test location...")
    shutil.copytree(SRC_DIST, CLEAN_DIR)
    
    clean_exe = os.path.join(CLEAN_DIR, "MediaPulsePro.exe")
    assert os.path.exists(clean_exe), f"Clean exe not found at {clean_exe}"
    print(f"[PASS] Successfully copied standalone bundle to clean location.")

    print(f"[*] Launching executable from clean directory (cwd={CLEAN_DIR})...")
    proc = subprocess.Popen([clean_exe], cwd=CLEAN_DIR)

    server_healthy = False
    status_data = None
    target_port = 8000

    try:
        for attempt in range(15):
            time.sleep(1)
            for port in [8000, 8001, 8002]:
                try:
                    url = f"http://127.0.0.1:{port}/api/status"
                    with urllib.request.urlopen(url, timeout=2) as resp:
                        if resp.status == 200:
                            status_data = json.loads(resp.read().decode("utf-8"))
                            target_port = port
                            server_healthy = True
                            break
                except Exception:
                    pass
            if server_healthy:
                break
            print(f"    Waiting for clean app initialization (attempt {attempt+1}/15)...")

        if not server_healthy:
            print("[FAIL] Clean app failed to respond on API.")
            sys.exit(1)

        print(f"[PASS] Clean app running and responding on port {target_port}!")
        print(f"       FFmpeg Available: {status_data.get('ffmpeg_available')}")
        print(f"       FFmpeg Version:   {status_data.get('ffmpeg_version')[:60]}...")
        assert status_data.get("ffmpeg_available") is True

        # Test UI asset delivery
        ui_url = f"http://127.0.0.1:{target_port}/static/modern.html"
        with urllib.request.urlopen(ui_url, timeout=3) as resp:
            content = resp.read().decode("utf-8")
            assert "MediaPulse Pro" in content
            print("[PASS] Clean app static web UI served successfully.")

        # Test real download
        dl_url = f"http://127.0.0.1:{target_port}/api/download"
        clean_dl_dir = os.path.join(CLEAN_DIR, "downloads")
        payload = json.dumps({
            "url": "https://www.w3schools.com/html/mov_bbb.mp4",
            "output_dir": clean_dl_dir,
            "mode": "video",
            "quality": "best",
            "container": "mp4"
        }).encode("utf-8")

        req = urllib.request.Request(dl_url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            dl_res = json.loads(resp.read().decode("utf-8"))
            task_id = dl_res.get("task_id")
            print(f"    Clean download task started: {task_id}")

        completed = False
        for _ in range(20):
            time.sleep(1)
            status_url = f"http://127.0.0.1:{target_port}/api/download/status/{task_id}"
            with urllib.request.urlopen(status_url, timeout=2) as resp:
                poll = json.loads(resp.read().decode("utf-8"))
                st = poll.get("status")
                print(f"    Clean Task {task_id}: {st} ({poll.get('percent', 0):.1f}%)")
                if st in ["finished", "completed"]:
                    completed = True
                    break
                elif st == "error":
                    print(f"[FAIL] Download error: {poll.get('message')}")
                    break

        assert completed is True, "Clean download should complete successfully"
        print("[PASS] Download executed and completed in clean directory environment!")

        print("\n=======================================================")
        print("CLEAN DIRECTORY EXECUTION VERIFIED 100% OPERATIONAL!")
        print("=======================================================")

    finally:
        print("[*] Terminating clean test process...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        print("[*] Clean test process terminated.")

if __name__ == "__main__":
    run_clean_test()
