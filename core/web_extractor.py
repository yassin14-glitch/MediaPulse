"""Universal Web Video Extractor that discovers videos from any website URL."""
import json
import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from core.downloader_engine import DownloaderEngine, normalize_video_url


class WebVideoExtractor:
    """Extracts videos from any website URL using yt-dlp + HTML5/OG media fallback scraping."""

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(self):
        self.downloader = DownloaderEngine()

    def inspect_url(self, url: str) -> Dict[str, Any]:
        """Inspects any URL and extracts all discoverable videos."""
        url = normalize_video_url(url.strip())
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        discovered_videos: List[Dict[str, Any]] = []
        site_title = urlparse(url).netloc
        site_icon = ""
        last_ytdlp_error = None

        # Strategy 1: Try yt-dlp (covers 1800+ sites: YouTube, Instagram, TikTok, Twitter/X, Reddit, Vimeo, etc.)
        try:
            info = self.downloader.fetch_info(url)
            if info:
                site_title = info.get("title", site_title)
                # If it's a playlist
                if info.get("is_playlist"):
                    discovered_videos.append({
                        "id": "ytdlp_playlist",
                        "title": f"[Playlist] {info['title']} ({info['count']} videos)",
                        "url": url,
                        "type": "Playlist / Extractor",
                        "extractor": info.get("extractor", "yt-dlp"),
                        "thumbnail": info.get("thumbnail", ""),
                        "resolutions": ["Best Quality"],
                        "source": "yt-dlp",
                        "is_direct": False
                    })
                else:
                    discovered_videos.append({
                        "id": "ytdlp_main",
                        "title": info.get("title", "Video Stream"),
                        "url": url,
                        "type": f"Extractor ({info.get('extractor', 'Generic')})",
                        "extractor": info.get("extractor", "yt-dlp"),
                        "thumbnail": info.get("thumbnail", ""),
                        "duration": info.get("duration", 0),
                        "uploader": info.get("uploader", ""),
                        "resolutions": info.get("available_resolutions", ["Best Available"]),
                        "source": "yt-dlp",
                        "is_direct": False
                    })
        except Exception as e:
            last_ytdlp_error = str(e)

        # Strategy 2: Deep HTML5 / OpenGraph / Media tag web scraping
        try:
            html_videos, parsed_title, parsed_icon = self._deep_scrape_webpage(url)
            if parsed_title and site_title == urlparse(url).netloc:
                site_title = parsed_title
            if parsed_icon:
                site_icon = parsed_icon

            # Append HTML videos avoiding duplicates
            existing_urls = {v["url"] for v in discovered_videos}
            for vid in html_videos:
                if vid["url"] not in existing_urls:
                    discovered_videos.append(vid)
                    existing_urls.add(vid["url"])
        except Exception as e:
            print(f"Deep scraping error for {url}: {e}")

        return {
            "page_url": url,
            "title": site_title,
            "icon": site_icon,
            "count": len(discovered_videos),
            "videos": discovered_videos,
            "error_hint": last_ytdlp_error if not discovered_videos else None
        }

    def _deep_scrape_webpage(self, url: str) -> tuple[List[Dict[str, Any]], str, str]:
        """Scrapes web page HTML for HTML5 video tags, OpenGraph video, embedded players, and m3u8/mp4 URLs."""
        videos = []
        page_title = ""
        page_icon = ""

        try:
            response = requests.get(url, headers=self.DEFAULT_HEADERS, timeout=10)
            if response.status_code != 200:
                return videos, page_title, page_icon

            html = response.text
            soup = BeautifulSoup(html, "html.parser")

            if soup.title and soup.title.string:
                page_title = soup.title.string.strip()

            # Find favicon
            icon_tag = soup.find("link", rel=lambda x: x and "icon" in x.lower())
            if icon_tag and icon_tag.get("href"):
                page_icon = urljoin(url, icon_tag["href"])

            # 1. Look for <video> tags
            for idx, video_tag in enumerate(soup.find_all("video")):
                src = video_tag.get("src")
                poster = video_tag.get("poster", "")
                if poster:
                    poster = urljoin(url, poster)

                if src:
                    full_src = urljoin(url, src)
                    videos.append({
                        "id": f"html5_video_{idx}",
                        "title": f"{page_title or 'Video'} - HTML5 Source #{idx+1}",
                        "url": full_src,
                        "type": "Direct HTML5 Video",
                        "extractor": "HTML5 <video>",
                        "thumbnail": poster,
                        "resolutions": ["Direct Stream"],
                        "source": "html5",
                        "is_direct": True
                    })

                # Check inside <source> children
                for s_idx, source in enumerate(video_tag.find_all("source")):
                    s_src = source.get("src")
                    s_type = source.get("type", "video/mp4")
                    if s_src:
                        full_s_src = urljoin(url, s_src)
                        videos.append({
                            "id": f"html5_source_{idx}_{s_idx}",
                            "title": f"{page_title or 'Video'} - Stream #{s_idx+1} ({s_type})",
                            "url": full_s_src,
                            "type": f"HTML5 Source ({s_type})",
                            "extractor": "HTML5 <source>",
                            "thumbnail": poster,
                            "resolutions": ["Direct Stream"],
                            "source": "html5",
                            "is_direct": True
                        })

            # 2. Look for OpenGraph and Twitter video meta tags
            og_video = soup.find("meta", property=re.compile(r"og:video(:secure_url|:url)?$", re.I))
            if og_video and og_video.get("content"):
                og_url = urljoin(url, og_video["content"])
                og_image = soup.find("meta", property="og:image")
                thumb = urljoin(url, og_image["content"]) if og_image and og_image.get("content") else ""
                videos.append({
                    "id": "og_video",
                    "title": f"{page_title or 'Video'} (OpenGraph Stream)",
                    "url": og_url,
                    "type": "OpenGraph Video Meta",
                    "extractor": "Meta Tags",
                    "thumbnail": thumb,
                    "resolutions": ["Best Stream"],
                    "source": "opengraph",
                    "is_direct": True
                })

            # 3. Look for embedded iframes (e.g. YouTube, Vimeo, Dailymotion embeds)
            for f_idx, iframe in enumerate(soup.find_all("iframe")):
                f_src = iframe.get("src") or iframe.get("data-src")
                if not f_src:
                    continue
                full_f_src = urljoin(url, f_src)
                if any(x in full_f_src.lower() for x in ["youtube.com/embed", "player.vimeo.com", "dailymotion.com/embed", "tiktok.com", "stream"]):
                    videos.append({
                        "id": f"iframe_{f_idx}",
                        "title": f"Embedded Player #{f_idx+1} ({urlparse(full_f_src).netloc})",
                        "url": full_f_src,
                        "type": "Embedded Video Player",
                        "extractor": "IFrame Player",
                        "thumbnail": "",
                        "resolutions": ["Best Available"],
                        "source": "iframe",
                        "is_direct": False
                    })

            # 4. Regex scan for direct video stream links in scripts (.mp4, .m3u8)
            direct_stream_pattern = re.compile(
                r'https?://[^\s"\'<>]+\.(?:mp4|m3u8|webm)(?:\?[^\s"\'<>]*)?',
                re.IGNORECASE
            )
            found_urls = set(direct_stream_pattern.findall(html))
            # Filter out advertisements or tracking pixels
            for s_idx, stream_url in enumerate(list(found_urls)[:5]):
                # Skip if already discovered
                if any(v["url"] == stream_url for v in videos):
                    continue
                is_m3u8 = ".m3u8" in stream_url.lower()
                videos.append({
                    "id": f"script_stream_{s_idx}",
                    "title": f"Detected Stream #{s_idx+1} ({'HLS m3u8' if is_m3u8 else 'MP4'})",
                    "url": stream_url,
                    "type": "HLS Stream (m3u8)" if is_m3u8 else "Direct MP4 File",
                    "extractor": "Script/Text Scanner",
                    "thumbnail": "",
                    "resolutions": ["Original"],
                    "source": "stream_url",
                    "is_direct": not is_m3u8
                })

        except Exception as e:
            print(f"Error while deep scraping: {e}")

        return videos, page_title, page_icon
