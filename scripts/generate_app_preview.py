"""Generates an aesthetic 1200x700 app showcase preview image in assets/preview.png
using Pillow for the GitHub README banner.
"""
import os
from PIL import Image, ImageDraw, ImageFont

def generate_preview():
    width = 1200
    height = 680
    im = Image.new("RGBA", (width, height), (9, 13, 22, 255))
    draw = ImageDraw.Draw(im)

    # Ambient glow gradients
    for r in range(350, 0, -5):
        alpha = int((350 - r) * 0.12)
        draw.ellipse([800 - r, 120 - r, 800 + r, 120 + r], fill=(59, 130, 246, alpha))
        draw.ellipse([300 - r, 450 - r, 300 + r, 450 + r], fill=(16, 185, 129, int(alpha * 0.8)))

    # Main Window Mockup Canvas
    win_x0, win_y0, win_x1, win_y1 = 60, 50, 1140, 630
    draw.rounded_rectangle([win_x0, win_y0, win_x1, win_y1], radius=16, fill=(19, 28, 46, 240), outline=(35, 51, 77, 255), width=2)

    # Titlebar
    draw.rounded_rectangle([win_x0, win_y0, win_x1, win_y0 + 44], radius=16, fill=(15, 23, 42, 255))
    draw.rectangle([win_x0, win_y0 + 20, win_x1, win_y0 + 44], fill=(15, 23, 42, 255))
    draw.line([win_x0, win_y0 + 44, win_x1, win_y0 + 44], fill=(35, 51, 77, 255), width=1)

    # Window Controls (Mac/Win style)
    draw.ellipse([win_x0 + 16, win_y0 + 16, win_x0 + 28, win_y0 + 28], fill=(239, 68, 68, 255))
    draw.ellipse([win_x0 + 36, win_y0 + 16, win_x0 + 48, win_y0 + 28], fill=(245, 158, 11, 255))
    draw.ellipse([win_x0 + 56, win_y0 + 16, win_x0 + 68, win_y0 + 28], fill=(16, 185, 129, 255))

    # Window Title
    draw.text((win_x0 + 80, win_y0 + 14), "MediaPulse Pro • Universal Multimedia Video & Audio Downloader", fill=(203, 213, 225, 255))

    # Sidebar Area
    sb_w = 210
    draw.rectangle([win_x0, win_y0 + 44, win_x0 + sb_w, win_y1], fill=(15, 23, 42, 220), outline=None)
    draw.line([win_x0 + sb_w, win_y0 + 44, win_x0 + sb_w, win_y1], fill=(35, 51, 77, 255), width=1)

    # Sidebar Brand
    draw.rounded_rectangle([win_x0 + 16, win_y0 + 60, win_x0 + 46, win_y0 + 90], radius=8, fill=(59, 130, 246, 255))
    draw.text((win_x0 + 25, win_y0 + 66), "⚡", fill=(255, 255, 255, 255))
    draw.text((win_x0 + 56, win_y0 + 66), "MediaPulse Pro", fill=(96, 165, 250, 255))

    # Sidebar Nav Items
    nav_items = [
        ("📺 YouTube Pro", True),
        ("🌐 Universal Web", False),
        ("📋 Batch Queue", False),
        ("📁 Library & History", False),
        ("⚙️ Settings", False)
    ]
    ny = win_y0 + 120
    for name, is_active in nav_items:
        if is_active:
            draw.rounded_rectangle([win_x0 + 12, ny, win_x0 + sb_w - 12, ny + 36], radius=8, fill=(59, 130, 246, 45), outline=(59, 130, 246, 100))
            draw.text((win_x0 + 24, ny + 10), name, fill=(96, 165, 250, 255))
        else:
            draw.text((win_x0 + 24, ny + 10), name, fill=(148, 163, 184, 255))
        ny += 46

    # Language pill in sidebar
    draw.rounded_rectangle([win_x0 + 16, win_y1 - 44, win_x0 + sb_w - 16, win_y1 - 16], radius=6, fill=(30, 41, 59, 255), outline=(35, 51, 77, 255))
    draw.text((win_x0 + 26, win_y1 - 36), "🌐 12 Languages (EN/AR)", fill=(203, 213, 225, 255))

    # Main Body Area
    main_x = win_x0 + sb_w + 30
    main_y = win_y0 + 64

    # Card Title
    draw.text((main_x, main_y), "YouTube Pro Video Downloader", fill=(248, 250, 252, 255))

    # URL Input Box
    input_w = 780
    draw.rounded_rectangle([main_x, main_y + 30, main_x + input_w, main_y + 80], radius=10, fill=(11, 17, 32, 255), outline=(59, 130, 246, 200), width=2)
    draw.text((main_x + 18, main_y + 45), "🔗 https://www.youtube.com/watch?v=dQw4w9WgXcQ", fill=(226, 232, 240, 255))
    draw.rounded_rectangle([main_x + input_w - 100, main_y + 38, main_x + input_w - 12, main_y + 72], radius=6, fill=(59, 130, 246, 255))
    draw.text((main_x + input_w - 82, main_y + 46), "Preview", fill=(255, 255, 255, 255))

    # Pre-Download Preview Card
    card_y = main_y + 100
    card_w = input_w
    draw.rounded_rectangle([main_x, card_y, main_x + card_w, card_y + 115], radius=10, fill=(11, 17, 32, 255), outline=(35, 51, 77, 255))
    # Thumbnail mock
    draw.rounded_rectangle([main_x + 16, card_y + 14, main_x + 160, card_y + 100], radius=8, fill=(30, 41, 59, 255), outline=(59, 130, 246, 120))
    draw.polygon([(main_x + 80, card_y + 45), (main_x + 80, card_y + 70), (main_x + 105, card_y + 57)], fill=(96, 165, 250, 255))

    draw.text((main_x + 175, card_y + 20), "Rick Astley - Never Gonna Give You Up (Official Music Video)", fill=(241, 245, 249, 255))
    draw.text((main_x + 175, card_y + 46), "Rick Astley • 3:32 • 1,540,291,048 views • High Bitrate Audio", fill=(148, 163, 184, 255))

    # Badges
    draw.rounded_rectangle([main_x + 175, card_y + 72, main_x + 280, card_y + 94], radius=6, fill=(16, 185, 129, 40), outline=(16, 185, 129, 100))
    draw.text((main_x + 185, card_y + 76), "✂️ Clip: 00:30-01:45", fill=(52, 211, 153, 255))

    draw.rounded_rectangle([main_x + 290, card_y + 72, main_x + 395, card_y + 94], radius=6, fill=(59, 130, 246, 40), outline=(59, 130, 246, 100))
    draw.text((main_x + 300, card_y + 76), "🛡️ SponsorBlock", fill=(96, 165, 250, 255))

    # Format Chips
    chips_y = card_y + 135
    chips = [
        ("Best Available", False),
        ("4K Ultra HD", True),
        ("2K QHD", False),
        ("1080p Full HD", False),
        ("720p HD", False),
        ("MP3 Studio 320k", False)
    ]
    cx = main_x
    for c_text, is_c_active in chips:
        c_w = len(c_text) * 8 + 24
        if is_c_active:
            draw.rounded_rectangle([cx, chips_y, cx + c_w, chips_y + 32], radius=6, fill=(59, 130, 246, 60), outline=(59, 130, 246, 255), width=2)
            draw.text((cx + 12, chips_y + 8), c_text, fill=(96, 165, 250, 255))
        else:
            draw.rounded_rectangle([cx, chips_y, cx + c_w, chips_y + 32], radius=6, fill=(11, 17, 32, 255), outline=(35, 51, 77, 255))
            draw.text((cx + 12, chips_y + 8), c_text, fill=(148, 163, 184, 255))
        cx += c_w + 10

    # Big Download Button
    draw.rounded_rectangle([main_x + card_w - 180, chips_y - 2, main_x + card_w, chips_y + 34], radius=8, fill=(37, 99, 235, 255))
    draw.text((main_x + card_w - 155, chips_y + 7), "⬇️ Download 4K", fill=(255, 255, 255, 255))

    # Live Progress Bar Card
    prog_y = chips_y + 54
    draw.rounded_rectangle([main_x, prog_y, main_x + card_w, prog_y + 90], radius=10, fill=(11, 17, 32, 255), outline=(35, 51, 77, 255))
    draw.text((main_x + 18, prog_y + 14), "Rick Astley - Never Gonna Give You Up [4K 60fps].mp4", fill=(241, 245, 249, 255))
    draw.text((main_x + card_w - 60, prog_y + 14), "78.4%", fill=(96, 165, 250, 255))

    # Progress Track
    draw.rounded_rectangle([main_x + 18, prog_y + 38, main_x + card_w - 18, prog_y + 48], radius=5, fill=(30, 41, 59, 255))
    draw.rounded_rectangle([main_x + 18, prog_y + 38, main_x + int((card_w - 36) * 0.784) + 18, prog_y + 48], radius=5, fill=(16, 185, 129, 255))

    # Progress Footer
    draw.text((main_x + 18, prog_y + 60), "12.4 MB/s • 86.2 MB / 110.0 MB", fill=(148, 163, 184, 255))
    draw.text((main_x + card_w - 120, prog_y + 60), "ETA: 00:02", fill=(148, 163, 184, 255))

    # Save to assets/preview.png
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "preview.png")
    im.save(out_path, format="PNG")
    print(f"[OK] Generated showcase banner at: {out_path}")

if __name__ == "__main__":
    generate_preview()
