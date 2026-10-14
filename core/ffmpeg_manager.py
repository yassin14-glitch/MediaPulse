"""FFmpeg discovery and configuration manager supporting frozen executables and source runs."""
import os
import shutil
import subprocess
import sys
from typing import Optional, Tuple
from core.logger import get_logger

logger = get_logger()


class FFmpegManager:
    """Manages discovery and validation of FFmpeg across source and frozen builds."""

    _cached_path: Optional[str] = None
    _cached_version: Optional[str] = None

    @classmethod
    def get_ffmpeg_path(cls) -> Optional[str]:
        """Finds the best available FFmpeg executable path."""
        if cls._cached_path and os.path.exists(cls._cached_path):
            return cls._cached_path

        exe_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        candidates = []

        # 1. PyInstaller _MEIPASS bundle directory
        if getattr(sys, "frozen", False):
            meipass = getattr(sys, "_MEIPASS", "")
            if meipass:
                candidates.append(os.path.join(meipass, exe_name))
                candidates.append(os.path.join(meipass, "bin", exe_name))

            # Exe directory
            exe_dir = os.path.dirname(sys.executable)
            candidates.append(os.path.join(exe_dir, "_internal", "bin", exe_name))
            candidates.append(os.path.join(exe_dir, "_internal", exe_name))
            candidates.append(os.path.join(exe_dir, "bin", exe_name))
            candidates.append(os.path.join(exe_dir, exe_name))

        # 2. Local application bin directory (from source)
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates.append(os.path.join(app_dir, "bin", exe_name))
        candidates.append(os.path.join(app_dir, exe_name))

        # 3. User app data bin directory (~/.multimedia_downloader/bin)
        appdata_bin = os.path.join(os.path.expanduser("~"), ".multimedia_downloader", "bin", exe_name)
        candidates.append(appdata_bin)

        # Check candidate files
        for p in candidates:
            if p and os.path.isfile(p) and os.path.exists(p):
                cls._cached_path = os.path.normpath(p)
                logger.info(f"Found bundled/local FFmpeg at: {cls._cached_path}")
                return cls._cached_path

        # 4. Check system PATH
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg and os.path.exists(system_ffmpeg):
            cls._cached_path = os.path.normpath(system_ffmpeg)
            logger.info(f"Found system PATH FFmpeg at: {cls._cached_path}")
            return cls._cached_path

        logger.warning("FFmpeg executable could not be located in any known candidate paths.")
        return None

    @classmethod
    def download_ffmpeg(cls, progress_callback=None) -> Tuple[bool, str]:
        """Downloads static ffmpeg.exe on demand into ~/.multimedia_downloader/bin/."""
        import urllib.request
        import zipfile

        target_dir = os.path.join(os.path.expanduser("~"), ".multimedia_downloader", "bin")
        os.makedirs(target_dir, exist_ok=True)
        target_exe = os.path.join(target_dir, "ffmpeg.exe")

        # Official static release zip
        url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        zip_path = os.path.join(target_dir, "ffmpeg_download.zip")

        try:
            if progress_callback:
                progress_callback(5.0, "Connecting to download server...")

            def _reporthook(blocknum, blocksize, totalsize):
                if totalsize > 0 and progress_callback:
                    pct = min(90.0, (blocknum * blocksize / totalsize) * 85.0 + 5.0)
                    progress_callback(pct, f"Downloading FFmpeg ({pct:.1f}%)...")

            urllib.request.urlretrieve(url, zip_path, reporthook=_reporthook)

            if progress_callback:
                progress_callback(92.0, "Extracting ffmpeg.exe...")

            with zipfile.ZipFile(zip_path, "r") as zf:
                # Find ffmpeg.exe within zip
                found = False
                for member in zf.namelist():
                    if member.endswith("ffmpeg.exe"):
                        with zf.open(member) as source, open(target_exe, "wb") as target:
                            shutil.copyfileobj(source, target)
                        found = True
                        break

            if os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except Exception:
                    pass

            if not found or not os.path.exists(target_exe):
                return False, "ffmpeg.exe was not found inside the downloaded archive."

            cls._cached_path = target_exe
            cls._cached_version = None
            avail, ver, _ = cls.get_status()
            if avail:
                if progress_callback:
                    progress_callback(100.0, "FFmpeg ready!")
                return True, f"FFmpeg installed successfully: {ver}"
            return False, "Downloaded FFmpeg executable failed validation."

        except Exception as e:
            logger.error(f"Failed to download FFmpeg: {e}")
            if os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except Exception:
                    pass
            return False, f"Download failed: {e}"


    @classmethod
    def get_status(cls) -> Tuple[bool, str, Optional[str]]:
        """Returns (is_available, description_or_version, path)."""
        ffmpeg_path = cls.get_ffmpeg_path()
        if not ffmpeg_path:
            return (
                False,
                "FFmpeg is missing. 1080p/4K audio-video merging requires FFmpeg. Please install FFmpeg or place ffmpeg.exe in the application folder.",
                None
            )

        if cls._cached_version:
            return True, cls._cached_version, ffmpeg_path

        try:
            result = subprocess.run(
                [ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            first_line = result.stdout.splitlines()[0] if result.stdout else "FFmpeg Available"
            cls._cached_version = first_line
            return True, first_line, ffmpeg_path
        except Exception as e:
            logger.warning(f"Error testing ffmpeg version: {e}")
            return True, f"FFmpeg located: {os.path.basename(ffmpeg_path)}", ffmpeg_path


if __name__ == "__main__":
    avail, ver, path = FFmpegManager.get_status()
    print(f"Available: {avail}")
    print(f"Version: {ver}")
    print(f"Path: {path}")
