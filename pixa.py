#!/usr/bin/env python3
"""pixa - Convert images to dot-style wallpapers."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

__version__ = "0.0.1"

DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert ``#RRGGBB`` to ``(r, g, b)``."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------------------
# Background detection & removal
# ---------------------------------------------------------------------------

def detect_bg_color(arr: np.ndarray) -> tuple[int, int, int]:
    """Sample image edges and return the most common colour (the background)."""
    edges = np.concatenate([
        arr[0, :],
        arr[-1, :],
        arr[:, 0],
        arr[:, -1],
    ])
    edge_tuples = [tuple(p) for p in edges]
    return Counter(edge_tuples).most_common(1)[0][0]


def remove_background(arr: np.ndarray, threshold: int = 30) -> np.ndarray:
    """Return a boolean mask where ``True`` = background pixel.

    Uses euclidean distance from the most common edge colour.
    """
    bg = detect_bg_color(arr)

    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    dist = np.sqrt(
        (r.astype(float) - bg[0]) ** 2
        + (g.astype(float) - bg[1]) ** 2
        + (b.astype(float) - bg[2]) ** 2
    )
    return dist < threshold * 3


def find_character_bbox(
    mask: np.ndarray, pad: int = 30
) -> tuple[int, int, int, int]:
    """Return ``(x_min, y_min, x_max, y_max)`` bounding box of non-bg pixels."""
    rows = np.any(~mask, axis=1)
    cols = np.any(~mask, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    h, w = mask.shape
    return (
        max(0, cmin - pad),
        max(0, rmin - pad),
        min(w, cmax + pad),
        min(h, rmax + pad),
    )


def crop_to_character(img: Image.Image) -> tuple[Image.Image, tuple[float, float]]:
    """Remove background and crop to the character bounding box.

    Returns ``(cropped_image, (rel_x, rel_y))`` where the relative position
    is where the character's centre sits in the *original* image (0-1 range).
    """
    orig_w, orig_h = img.size
    arr = np.array(img)
    bg_mask = remove_background(arr)
    bbox = find_character_bbox(bg_mask)

    cropped = img.crop(bbox)
    crop_arr = np.array(cropped)
    local_mask = bg_mask[bbox[1] : bbox[3], bbox[0] : bbox[2]]
    crop_arr[local_mask] = [0, 0, 0]

    rel_x = (bbox[0] + bbox[2]) / 2 / orig_w
    rel_y = (bbox[1] + bbox[3]) / 2 / orig_h

    return Image.fromarray(crop_arr), (rel_x, rel_y)


# ---------------------------------------------------------------------------
# Output sizing
# ---------------------------------------------------------------------------

def resolve_output_size(
    img_w: int,
    img_h: int,
    explicit_w: int | None,
    explicit_h: int | None,
) -> tuple[int, int]:
    """Decide final output dimensions.

    Always keeps the original size unless the user specifies explicitly.
    """
    if explicit_w is not None or explicit_h is not None:
        return explicit_w or img_w, explicit_h or img_h
    return img_w, img_h


# ---------------------------------------------------------------------------
# Core rendering
# ---------------------------------------------------------------------------

def create_dots_wallpaper(
    source: Image.Image,
    out_w: int,
    out_h: int,
    *,
    dot_spacing: int = 7,
    max_radius: float = 3.2,
    threshold: int = 25,
    bg_color: tuple[int, int, int] = (0, 0, 0),
    dot_color: tuple[int, int, int] | None = None,
    colored: bool = False,
    rel_pos: tuple[float, float] | None = None,
) -> Image.Image:
    """Render *source* as a dot-style wallpaper of size ``out_w`` x ``out_h``."""
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

    if rel_pos:
        rx, ry = rel_pos
        offset_x = int(out_w * rx - art_w / 2)
        offset_y = int(out_h * ry - art_h / 2)
    else:
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pixa",
        description="Convert images to dot-style wallpapers",
    )
    p.add_argument("input", help="Input image path")
    p.add_argument(
        "-o", "--output", default=None,
        help="Output path (default: output.<input-ext>)",
    )
    p.add_argument(
        "-w", "--width", type=int, default=None,
        help="Output width (default: auto)",
    )
    p.add_argument(
        "-ht", "--height", type=int, default=None,
        help="Output height (default: auto)",
    )
    p.add_argument(
        "-d", "--dot-size", type=int, default=7,
        help="Dot spacing in px (default: 7)",
    )
    p.add_argument(
        "-r", "--radius", type=float, default=3.2,
        help="Max dot radius (default: 3.2)",
    )
    p.add_argument(
        "-th", "--threshold", type=int, default=25,
        help="Min brightness threshold (default: 25)",
    )
    p.add_argument(
        "--bg", default=None,
        help="Background hex color (default: auto)",
    )
    p.add_argument(
        "--text-color", default="#ffffff",
        help="Dot color in white mode (default: #ffffff)",
    )
    p.add_argument(
        "--mode",
        choices=["full", "color", "white"],
        default="white",
        help=(
            "full   = whole image + original bg | "
            "color  = character + colored dots | "
            "white  = character + white dots"
        ),
    )
    return p


def _resolve_output_path(input_path: Path, output: str | None) -> str:
    """Deduce output path, preserving the input file extension."""
    if output:
        return output
    return str(input_path.with_name(f"output{input_path.suffix}"))
    """Open *path* and ensure RGB mode."""
    return Image.open(path).convert("RGB")


def _prepare_mode(
    img: Image.Image, args: argparse.Namespace
) -> tuple[Image.Image, tuple[int, int], tuple[int, int, int], tuple[int, int, int] | None, bool, tuple[float, float] | None]:
    """Apply mode-specific preprocessing.

    Returns ``(processed_img, (out_w, out_h), bg_color, dot_color, colored, rel_pos)``.
    """
    out_w, out_h = resolve_output_size(
        img.width, img.height, args.width, args.height
    )
    bg_color = hex_to_rgb(args.bg) if args.bg else (0, 0, 0)
    dot_color = hex_to_rgb(args.text_color)

    if args.mode == "full":
        if not args.bg:
            bg_color = detect_bg_color(np.array(img))
        return img, (out_w, out_h), bg_color, dot_color, True, None

    img, rel_pos = crop_to_character(img)
    print(f"Cropped to character: {img.width}x{img.height}")
    return (
        img,
        (out_w, out_h),
        bg_color,
        dot_color,
        args.mode == "color",
        rel_pos,
    )


def main() -> None:
    args = build_parser().parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    img = Image.open(input_path).convert("RGB")
    print(f"Loaded: {input_path} ({img.width}x{img.height})")

    img, (out_w, out_h), bg_color, dot_color, colored, rel_pos = _prepare_mode(
        img, args
    )

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
        rel_pos=rel_pos,
    )

    out_path = _resolve_output_path(input_path, args.output)
    result.save(out_path)
    print(f"Saved: {out_path} ({out_w}x{out_h})")


if __name__ == "__main__":
    main()
