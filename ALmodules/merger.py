"""
merger.py — Grid-merge all PNG files in a folder into a single image.

Handles both standard 512×512 cards and large 1793×1080 landscape cards:
  - Square cards  → fixed 6-column grid (same feel as original)
  - Landscape cards → sqrt-based square-ish grid (matches original AutoLeak large merger)

Card dimensions are auto-detected from the first PNG found — no hardcoded resize.
"""

from __future__ import annotations

import io
import math
import os
from typing import Optional

import requests
from PIL import Image

RESAMPLE     = Image.LANCZOS
DEFAULT_COLS = 6     # columns for square / portrait cards


def _load_watermark(source: str, card_w: int, card_h: int) -> Optional[Image.Image]:
    """Load a watermark, scaled to match the card cell size. Returns None on failure."""
    if not source:
        return None

    img = None

    if source.startswith("image/"):
        path = os.path.join("assets", source[len("image/"):])
        if os.path.exists(path):
            try:
                img = Image.open(path).convert("RGBA")
            except Exception:
                pass
    elif os.path.exists(source):
        try:
            img = Image.open(source).convert("RGBA")
        except Exception:
            pass
    else:
        try:
            resp = requests.get(source, timeout=10)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        except Exception:
            pass

    if img is None:
        return None

    return img.resize((card_w, card_h), RESAMPLE)


def merge_icons(
    icons_dir: str,
    out_path: str,
    cols: int = DEFAULT_COLS,
    watermark_url: str = "",
    bg_color: tuple[int, int, int] = (30, 30, 30),
) -> str:
    """
    Merge all PNG files in icons_dir into a grid image saved at out_path.

    Card size is auto-detected from the first PNG — no forced resize.
    Large landscape cards (e.g. 1793×1080) automatically switch to a
    sqrt-based grid so the output stays roughly square.

    Parameters
    ----------
    icons_dir     : Directory containing <id>.png icon files
    out_path      : Output file path (.jpg or .png)
    cols          : Columns per row for square/portrait cards (ignored for landscape)
    watermark_url : URL or local path of a watermark appended as the last cell
    bg_color      : RGB background fill colour

    Returns
    -------
    str : The resolved out_path
    """
    if not os.path.isdir(icons_dir):
        raise ValueError(f"Directory not found: {icons_dir}")

    icon_files = sorted([
        os.path.join(icons_dir, f)
        for f in os.listdir(icons_dir)
        if f.lower().endswith(".png")
    ])

    if not icon_files:
        raise ValueError(f"No PNG files found in {icons_dir}")

    # ── Detect card dimensions from the first valid image ─────────────────────
    card_w, card_h = 512, 512
    for path in icon_files:
        try:
            with Image.open(path) as probe:
                card_w, card_h = probe.size
            break
        except Exception:
            continue

    # ── Append watermark cell if requested ────────────────────────────────────
    wm_path = None
    wm_img  = _load_watermark(watermark_url, card_w, card_h)
    if wm_img:
        wm_path = os.path.join(icons_dir, "zzz_watermark.png")
        wm_img.save(wm_path)
        icon_files.append(wm_path)

    total = len(icon_files)

    # ── Grid layout ───────────────────────────────────────────────────────────
    if card_w > card_h:
        # Landscape cards (large style): sqrt-based grid, same as original AutoLeak
        n_cols = math.ceil(math.sqrt(total))
        n_rows = math.ceil(total / n_cols)
    else:
        # Square / portrait cards: fixed column count
        n_cols = cols
        n_rows = math.ceil(total / n_cols)

    grid_w = n_cols * card_w
    grid_h = n_rows * card_h
    canvas = Image.new("RGB", (grid_w, grid_h), bg_color)

    # ── Place each card ───────────────────────────────────────────────────────
    for idx, path in enumerate(icon_files):
        try:
            icon = Image.open(path).convert("RGB")
            # Resize only if this particular file differs from the detected size
            if icon.size != (card_w, card_h):
                icon = icon.resize((card_w, card_h), RESAMPLE)
        except Exception:
            icon = Image.new("RGB", (card_w, card_h), (80, 80, 80))

        row = idx // n_cols
        col = idx % n_cols
        canvas.paste(icon, (col * card_w, row * card_h))

    # ── Save ──────────────────────────────────────────────────────────────────
    os.makedirs(
        os.path.dirname(out_path) if os.path.dirname(out_path) else ".",
        exist_ok=True,
    )
    fmt = "JPEG" if out_path.lower().endswith((".jpg", ".jpeg")) else "PNG"
    save_kwargs = {"quality": 92, "optimize": True} if fmt == "JPEG" else {}
    canvas.save(out_path, fmt, **save_kwargs)

    # Clean up temporary watermark file
    if wm_path:
        try:
            os.remove(wm_path)
        except OSError:
            pass

    return out_path


def merge_files(
    file_list: list[str],
    out_path: str,
    cols: int = DEFAULT_COLS,
    bg_color: tuple[int, int, int] = (30, 30, 30),
    card_scale: float = 1.0,
    watermark_path: str = "",
) -> str:
    """
    Merge an explicit list of image files into a grid image saved at out_path.

    Unlike merge_icons(), this takes a specific file list rather than scanning
    an entire directory — use this when the caller has already selected which
    images to include.

    Parameters
    ----------
    file_list      : Ordered list of image file paths to merge
    out_path       : Output file path (.jpg or .png)
    cols           : Columns per row for square/portrait cards (ignored for landscape)
    bg_color       : RGB background fill colour
    watermark_path : Optional local path to an image appended as the last cell
    card_scale : Size multiplier applied to the auto-detected card dimensions
                 (0.25 = quarter size, 1.0 = original, 2.0 = double)

    Returns
    -------
    str : The resolved out_path
    """
    if not file_list:
        raise ValueError("No files provided.")

    # ── Detect card dimensions from the first valid image ─────────────────────
    card_w, card_h = 512, 512
    for path in file_list:
        try:
            with Image.open(path) as probe:
                card_w, card_h = probe.size
            break
        except Exception:
            continue

    # Apply scale
    card_w = max(1, int(card_w * card_scale))
    card_h = max(1, int(card_h * card_scale))

    # ── Append watermark as last cell ─────────────────────────────────────────
    files = list(file_list)
    if watermark_path and os.path.isfile(watermark_path):
        files.append(watermark_path)

    total = len(files)

    # ── Grid layout ───────────────────────────────────────────────────────────
    if card_w > card_h:
        # Landscape cards: sqrt-based grid
        n_cols = math.ceil(math.sqrt(total))
        n_rows = math.ceil(total / n_cols)
    else:
        # Square / portrait cards: fixed column count
        n_cols = cols
        n_rows = math.ceil(total / n_cols)

    canvas = Image.new("RGB", (n_cols * card_w, n_rows * card_h), bg_color)

    # ── Place each card ───────────────────────────────────────────────────────
    for idx, path in enumerate(files):
        try:
            icon = Image.open(path).convert("RGB")
            if icon.size != (card_w, card_h):
                icon = icon.resize((card_w, card_h), RESAMPLE)
        except Exception:
            icon = Image.new("RGB", (card_w, card_h), (80, 80, 80))

        row_idx = idx // n_cols
        col_idx = idx % n_cols
        canvas.paste(icon, (col_idx * card_w, row_idx * card_h))

    # ── Save ──────────────────────────────────────────────────────────────────
    os.makedirs(
        os.path.dirname(out_path) if os.path.dirname(out_path) else ".",
        exist_ok=True,
    )
    fmt = "JPEG" if out_path.lower().endswith((".jpg", ".jpeg")) else "PNG"
    save_kwargs = {"quality": 92, "optimize": True} if fmt == "JPEG" else {}
    canvas.save(out_path, fmt, **save_kwargs)

    return out_path
