import requests
import re
import json

url = "https://www.instagram.com/reel/DecR0l8BSWP/embed/captioned/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

r = requests.get(url, headers=headers, timeout=10)
print("Status code:", r.status_code)
# Search for video_url in the embed json/html
matches = re.findall(r'"video_url"\s*:\s*"([^"]+)"', r.text)
print("video_url matches:", len(matches))
if matches:
    clean_url = matches[0].replace(r"\u0026", "&").replace(r"\/", "/")
    print("Found video URL:", clean_url[:120])
else:
    # Also search for mp4
    mp4s = re.findall(r'https://[^"\'\s<>]+\.mp4[^"\'\s<>]*', r.text)
    print("mp4 matches:", len(mp4s))
    if mp4s:
        print("First mp4:", mp4s[0][:120])
