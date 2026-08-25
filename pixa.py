#!/usr/bin/env python3
"""pixa - Convert images to dot-style wallpapers."""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from collections import Counter


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def detect_bg_color(arr: np.ndarray) -> tuple[int, int, int]:
    """Find the most common edge color (background)."""
    edges = np.concatenate([
        arr[0, :],
        arr[-1, :],
        arr[:, 0],
        arr[:, -1],
    ])
    edge_tuples = [tuple(p) for p in edges]
    return Counter(edge_tuples).most_common(1)[0][0]


def remove_background(arr: np.ndarray, threshold: int = 30) -> np.ndarray:
    """Detect and remove solid-color backgrounds by finding the most common edge color."""
    most_common = detect_bg_color(arr)

    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    dist = np.sqrt(
        (r.astype(float) - most_common[0])**2 +
        (g.astype(float) - most_common[1])**2 +
        (b.astype(float) - most_common[2])**2
    )

    bg_mask = dist < threshold * 3
    return bg_mask


def find_character_bbox(mask: np.ndarray, pad: int = 30) -> tuple[int, int, int, int]:
    """Find bounding box of non-background pixels."""
    rows = np.any(~mask, axis=1)
    cols = np.any(~mask, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    h, w = mask.shape
    rmin = max(0, rmin - pad)
    rmax = min(h, rmax + pad)
    cmin = max(0, cmin - pad)
    cmax = min(w, cmax + pad)

    return cmin, rmin, cmax, rmax


def create_dots_wallpaper(
    source: Image.Image,
    out_w: int,
    out_h: int,
    dot_spacing: int = 7,
    max_radius: float = 3.2,
    threshold: int = 25,
    bg_color: tuple[int, int, int] = (0, 0, 0),
    dot_color: tuple[int, int, int] | None = None,
    colored: bool = False,
) -> Image.Image:
    """Create a dot-style wallpaper from an image."""
    src_ratio = source.width / source.height
    out_ratio = out_w / out_h

    if src_ratio > out_ratio:
        cols_count = (out_w - dot_spacing) // dot_spacing
        rows_count = int(cols_count / src_ratio)
    else:
        rows_count = (out_h - dot_spacing) // dot_spacing
        cols_count = int(rows_count * src_ratio)

    resized = source.resize((cols_count, rows_count), Image.LANCZOS)
    gray = resized.convert("L")
    color_arr = np.array(resized)

    output = Image.new("RGB", (out_w, out_h), bg_color)
    draw = ImageDraw.Draw(output)

    gray_pixels = list(gray.getdata())

    art_w = cols_count * dot_spacing
    art_h = rows_count * dot_spacing
    offset_x = (out_w - art_w) // 2
    offset_y = (out_h - art_h) // 2

    for i, p in enumerate(gray_pixels):
        if p < threshold:
            continue

        col = i % cols_count
        row = i // cols_count

        x = offset_x + col * dot_spacing + dot_spacing // 2
        y = offset_y + row * dot_spacing + dot_spacing // 2

        radius = (p / 255) * max_radius
        if radius < 0.3:
            continue

        if colored:
            cr, cg, cb = color_arr[row, col]
            factor = 0.85
            color = (int(cr * factor), int(cg * factor), int(cb * factor))
        else:
            color = dot_color or (255, 255, 255)

        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=color,
        )

    return output


def main():
    parser = argparse.ArgumentParser(
        prog="pixa",
        description="Convert images to dot-style wallpapers",
    )
    parser.add_argument("input", help="Input image path")
    parser.add_argument("-o", "--output", default="output.png", help="Output file (default: output.png)")
    parser.add_argument("-w", "--width", type=int, default=None, help="Output width (default: input width)")
    parser.add_argument("-ht", "--height", type=int, default=None, help="Output height (default: input height)")
    parser.add_argument("-d", "--dot-size", type=int, default=7, help="Dot spacing in px (default: 7)")
    parser.add_argument("-r", "--radius", type=float, default=3.2, help="Max dot radius (default: 3.2)")
    parser.add_argument("-th", "--threshold", type=int, default=25, help="Min brightness threshold (default: 25)")
    parser.add_argument("--bg", default=None, help="Background color hex (default: auto)")
    parser.add_argument("--text-color", default="#ffffff", help="Dot color for white mode (default: #ffffff)")
    parser.add_argument(
        "--mode",
        choices=["full", "color", "white"],
        default="white",
        help="full=image+original bg, color=character+colored dots, white=character+white dots (default: white)",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    img = Image.open(input_path)
    print(f"Loaded: {input_path} ({img.width}x{img.height})")

    out_w = args.width or img.width
    out_h = args.height or img.height
    dot_color = hex_to_rgb(args.text_color)

    if args.mode == "full":
        arr = np.array(img)
        bg_rgb = detect_bg_color(arr)
        bg_color = hex_to_rgb(args.bg) if args.bg else bg_rgb
        colored = True
        print(f"Mode: full (bg auto-detected: {bg_rgb})")
    elif args.mode == "color":
        arr = np.array(img)
        bg_mask = remove_background(arr)
        bbox = find_character_bbox(bg_mask)
        img = img.crop(bbox)

        crop_arr = np.array(img)
        local_mask = bg_mask[bbox[1]:bbox[3], bbox[0]:bbox[2]]
        crop_arr[local_mask] = [0, 0, 0]
        img = Image.fromarray(crop_arr)

        bg_color = hex_to_rgb(args.bg) if args.bg else (0, 0, 0)
        colored = True
        print(f"Mode: color (cropped: {img.width}x{img.height})")
    else:  # white
        arr = np.array(img)
        bg_mask = remove_background(arr)
        bbox = find_character_bbox(bg_mask)
        img = img.crop(bbox)

        crop_arr = np.array(img)
        local_mask = bg_mask[bbox[1]:bbox[3], bbox[0]:bbox[2]]
        crop_arr[local_mask] = [0, 0, 0]
        img = Image.fromarray(crop_arr)

        bg_color = hex_to_rgb(args.bg) if args.bg else (0, 0, 0)
        colored = False
        print(f"Mode: white (cropped: {img.width}x{img.height})")

    result = create_dots_wallpaper(
        source=img,
        out_w=out_w,
        out_h=out_h,
        dot_spacing=args.dot_size,
        max_radius=args.radius,
        threshold=args.threshold,
        bg_color=bg_color,
        dot_color=dot_color,
        colored=colored,
    )

    result.save(args.output)
    print(f"Saved: {args.output} ({out_w}x{out_h})")


if __name__ == "__main__":
    main()
