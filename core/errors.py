"""Human-friendly error translation and classification for video downloads."""
import re
from core.logger import log_exception


def map_error_to_human_message(error: Exception or str) -> str:
    """Converts technical stack traces and yt-dlp errors into clean, helpful user messages."""
    err_str = str(error)

    # 1. Private video
    if re.search(r"private video|sign in if you've been granted access|this video is private", err_str, re.I):
        return "This video is private. You need permission from the owner to access it."

    # 2. Age-restricted video
    if re.search(r"sign in to confirm your age|age-restricted", err_str, re.I):
        return "This video is age-restricted and requires signing into YouTube."

    # 3. Region blocked / Geo restricted
    if re.search(r"available in your country|blocked in your (region|country)|geo-restricted|geographic", err_str, re.I):
        return "This video is not available in your geographical region."

    # 4. Deleted or not found (404)
    if re.search(r"video unavailable|does not exist|removed by the uploader|404|not found", err_str, re.I):
        return "This video is no longer available or was deleted by the uploader."

    # 5. Members-only content
    if re.search(r"join this channel to get access|members-only", err_str, re.I):
        return "This video is available to channel members only."

    # 6. Network / Connection drop / Timeout
    if re.search(r"timed? out|connection (refused|reset|aborted|lost)|network is unreachable|getaddrinfo failed|no internet", err_str, re.I):
        return "Network connection was lost or timed out. Please check your internet connection."

    # 7. Permission / Unwritable directory
    if re.search(r"permission denied|read-only file system|access is denied|errno 13", err_str, re.I):
        return "Cannot write to the chosen download folder. Please select a folder with write permissions."

    # 8. Disk full
    if re.search(r"no space left on device|disk full|not enough space|errno 28", err_str, re.I):
        return "Your hard drive is full. Free up disk space and try again."

    # 9. Unsupported / Malformed URL
    if re.search(r"unsupported url|is not a valid url|unknown url scheme", err_str, re.I):
        return "The provided link is not a valid or supported video URL."

    # 10. Cancellation
    if re.search(r"cancelled by user|download cancelled", err_str, re.I):
        return "Download was cancelled."

    # 11. Empty URL
    if not err_str.strip():
        return "No URL provided. Please enter a video link."

    # 12. Fallback: Clean up raw yt-dlp error prefix if present
    cleaned = re.sub(r"^(ERROR:\s*(\[.*?\])?\s*)", "", err_str).strip()
    # Limit length so it stays a human message
    if len(cleaned) > 120:
        cleaned = cleaned[:117] + "..."
    return cleaned
