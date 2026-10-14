"""Generates professional multi-size Windows icon and master PNG using Pillow."""
import os
import math
from PIL import Image, ImageDraw


def create_app_icon():
    os.makedirs("assets", exist_ok=True)
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Outer Dark Rounded Square Base with subtle border
    pad = 24
    corner = 110
    # Subtle drop glow
    for g in range(12, 0, -2):
        alpha = int(14 * (1 - g / 12))
        glow_box = [pad - g, pad - g, size - pad + g, size - pad + g]
        draw.rounded_rectangle(glow_box, radius=corner + g, fill=(59, 130, 246, alpha))

    # Dark background tile
    draw.rounded_rectangle([pad, pad, size - pad, size - pad], radius=corner, fill=(15, 23, 42, 255), outline=(51, 65, 85, 255), width=4)

    # Inner subtle glass shine
    draw.rounded_rectangle([pad + 6, pad + 6, size - pad - 6, pad + 180], radius=corner - 6, fill=(255, 255, 255, 12))

    # 2. Glowing Gradient Arrow / Media Downloader Symbol
    # Gradient coordinates
    center_x = size // 2
    center_y = size // 2 - 10

    # Draw vibrant lightning / downward download arrow with play slant
    # Arrow head points
    arrow_width = 120
    stem_width = 54
    arrow_top = 110
    arrow_mid = 290
    arrow_bottom = 390

    # Glow under arrow
    for ag in range(16, 0, -2):
        alpha = int(22 * (1 - ag / 16))
        # Head
        head_poly = [
            (center_x, arrow_bottom + ag),
            (center_x - arrow_width - ag, arrow_mid + ag // 2),
            (center_x + arrow_width + ag, arrow_mid + ag // 2)
        ]
        draw.polygon(head_poly, fill=(16, 185, 129, alpha))
        # Stem
        stem_box = [center_x - stem_width - ag, arrow_top - ag // 2, center_x + stem_width + ag, arrow_mid + ag]
        draw.rounded_rectangle(stem_box, radius=12, fill=(59, 130, 246, alpha))

    # Stem: Blue to Cyan
    for y in range(arrow_top, arrow_mid):
        ratio = (y - arrow_top) / (arrow_mid - arrow_top)
        r = int(59 * (1 - ratio) + 16 * ratio)
        g = int(130 * (1 - ratio) + 185 * ratio)
        b = int(246 * (1 - ratio) + 129 * ratio)
        draw.rectangle([center_x - stem_width, y, center_x + stem_width, y + 1], fill=(r, g, b, 255))

    # Arrow Head: Cyan to Emerald Green
    for y in range(arrow_mid, arrow_bottom):
        ratio = (y - arrow_mid) / (arrow_bottom - arrow_mid)
        # width shrinks linearly
        w = int(arrow_width * (1 - ratio))
        r = int(16 * (1 - ratio) + 5 * ratio)
        g = int(185 * (1 - ratio) + 150 * ratio)
        b = int(129 * (1 - ratio) + 105 * ratio)
        draw.line([(center_x - w, y), (center_x + w, y)], fill=(r, g, b, 255), width=2)

    # Bottom glowing pulse bar
    bar_y = 430
    bar_w = 140
    draw.rounded_rectangle(
        [center_x - bar_w, bar_y, center_x + bar_w, bar_y + 18],
        radius=9,
        fill=(16, 185, 129, 255)
    )

    # Save 512x512 Master PNG
    png_path = os.path.join("assets", "icon.png")
    img.save(png_path, "PNG")
    print(f"Saved master PNG icon to {png_path}")

    # Generate multi-size Windows .ico
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_path = os.path.join("assets", "icon.ico")
    img.save(ico_path, format="ICO", sizes=ico_sizes)
    print(f"Saved multi-resolution Windows ICO ({ico_sizes}) to {ico_path}")


if __name__ == "__main__":
    create_app_icon()
