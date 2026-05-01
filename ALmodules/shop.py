"""
shop.py — Fortnite Item Shop image generation + shop-hash watcher.

Card style matches the original AutoLeak format:
  - 512×512 per entry
  - Gradient background from entry 'colors' field (color1 → color3)
  - Item image (bundle art / track album / featured / icon) centered on gradient
  - assets/overlay.png dark-bottom gradient for text readability
  - Name · Last-seen · Price text using BurbankBigRegular-BlackItalic

Because modern shops have 200+ entries, the output is split into one image
per section (grouped by layout.name).  Each file is saved to merged/.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import io
import json
import math
import os
import shutil
import time
from collections import defaultdict
from datetime import datetime
from typing import Optional

import requests
from colorama import Fore
from PIL import Image, ImageDraw

from ALmodules.image_gen import load_font, RESAMPLE
from ALmodules.compressor import compress_image
from ALmodules.setup import resolve_font

FORTNITE_API = "https://fortnite-api.com"

CARD_SZ      = 512
SHOP_COLS    = 6
HEADER_H     = 200   # section header bar height
# Font to always use for shop (regardless of settings sideFont)
_SHOP_FONT   = os.path.join("fonts", "BurbankBigRegular-BlackItalic.otf")
_HISTORY_FILE = os.path.join("json", "shop_history.json")

_VBUCKS_URL         = "https://fortnite-api.com/images/vbuck.png"
_vbucks_icon_cache: dict[int, "Image.Image"] = {}


def _get_vbucks_icon(size: int) -> "Optional[Image.Image]":
    """Return a square RGBA V-Bucks icon resized to `size`, downloading once per run."""
    if size in _vbucks_icon_cache:
        return _vbucks_icon_cache[size]
    local = os.path.join("assets", "vbuck.png")
    try:
        if os.path.exists(local):
            raw = Image.open(local).convert("RGBA")
        else:
            r = requests.get(_VBUCKS_URL, timeout=8)
            r.raise_for_status()
            raw = Image.open(io.BytesIO(r.content)).convert("RGBA")
            os.makedirs("assets", exist_ok=True)
            raw.save(local)
        img = raw.resize((size, size), RESAMPLE)
        _vbucks_icon_cache[size] = img
        return img
    except Exception:
        return None


def _draw_price_with_icon(
    card: "Image.Image",
    draw: "ImageDraw.Draw",
    cx: int,
    baseline_y: int,
    price: int,
    font,
    icon_size: int = 30,
    gap: int = 5,
):
    """Draw [vbucks-icon] [price-number] centered on cx, baseline at baseline_y."""
    price_str = str(price)
    try:
        bbox  = font.getbbox(price_str)
        txt_w = bbox[2] - bbox[0]
    except Exception:
        txt_w = int(font.getlength(price_str))

    icon = _get_vbucks_icon(icon_size)
    if icon:
        total_w  = icon_size + gap + txt_w
        left_x   = cx - total_w // 2
        icon_top = baseline_y - icon_size   # bottom of icon sits at baseline
        card.paste(icon.convert("RGB"), (int(left_x), int(icon_top)), icon)
        draw = ImageDraw.Draw(card)          # refresh after paste
        txt_x = left_x + icon_size + gap
        draw.text((int(txt_x), baseline_y), price_str, font=font,
                  fill="white", anchor="ls")
    else:
        draw.text((cx, baseline_y), price_str, font=font, fill="white", anchor="ms")

    return draw


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_json(url: str, params: dict | None = None, timeout: int = 15) -> dict | None:
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(Fore.RED + f"  API error: {e}")
        return None


def _parse_color(hex_str: str) -> tuple[int, int, int]:
    """Parse RRGGBBAA or RRGGBB hex into (R, G, B)."""
    h = (hex_str or "888888ff").lstrip("#")[:6]
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _gradient_bg(colors: dict) -> Image.Image:
    """Build a 512×512 gradient background from an entry's 'colors' dict."""
    top = _parse_color(colors.get("color1", "888888ff"))
    bot = _parse_color(colors.get("color3", "222222ff"))
    img  = Image.new("RGB", (CARD_SZ, CARD_SZ))
    draw = ImageDraw.Draw(img)
    for y in range(CARD_SZ):
        t = y / (CARD_SZ - 1)
        r = int(top[0] + (bot[0] - top[0]) * t)
        g = int(top[1] + (bot[1] - top[1]) * t)
        b = int(top[2] + (bot[2] - top[2]) * t)
        draw.line([(0, y), (CARD_SZ - 1, y)], fill=(r, g, b))
    return img


def _best_image_url(entry: dict) -> Optional[str]:
    """Return the best available image URL for a shop entry."""
    # 1. Bundle artwork
    bundle = entry.get("bundle") or {}
    if bundle.get("image"):
        return bundle["image"]

    # 2. Track album art
    for t in (entry.get("tracks") or []):
        if t.get("albumArt"):
            return t["albumArt"]

    # 3. BR item — featured > icon > smallIcon
    for item in (entry.get("brItems") or []):
        imgs = item.get("images") or {}
        url = imgs.get("featured") or imgs.get("icon") or imgs.get("smallIcon")
        if url:
            return url

    # 4. newDisplayAsset material instance (still present on some entries)
    nda = entry.get("newDisplayAsset") or {}
    for inst in (nda.get("materialInstances") or []):
        imgs = inst.get("images") or {}
        url = imgs.get("Background") or imgs.get("OfferImage")
        if url:
            return url

    return None


def _entry_name(entry: dict) -> str:
    """Return a display name for a shop entry."""
    bundle = entry.get("bundle") or {}
    if bundle.get("name"):
        return bundle["name"]
    for t in (entry.get("tracks") or []):
        title = t.get("title", "")
        if title:
            return title
    for item in (entry.get("brItems") or []):
        name = item.get("name", "")
        if name:
            return name
    # Last resort: clean up devName
    dev = entry.get("devName", "")
    return dev.split("[")[0].split(":")[0].strip() or "Unknown"


def _load_history() -> dict:
    """Load local shop-history map: { item_id: [date_str, ...] }"""
    try:
        with open(_HISTORY_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_history(history: dict, entries: list, today_str: str) -> None:
    """Record every brItem from today's shop into the history file."""
    for entry in entries:
        for item in (entry.get("brItems") or []):
            iid = item.get("id")
            if not iid:
                continue
            dates = history.setdefault(iid, [])
            if not dates or dates[-1] != today_str:
                dates.append(today_str)
    try:
        with open(_HISTORY_FILE, "w") as f:
            json.dump(history, f)
    except Exception:
        pass


def _days_ago(entry: dict, today_str: str, history: dict) -> str:
    """Return 'LAST SEEN: N days ago', 'NEW!', or '' using local history."""
    items = entry.get("brItems") or []
    if not items:
        return ""
    iid = items[0].get("id", "")
    if not iid:
        return ""
    dates = history.get(iid, [])
    # All dates before today
    past = [d for d in dates if d < today_str]
    if not past:
        return "NEW!"
    last = past[-1]
    try:
        d1 = datetime.strptime(last, "%Y-%m-%d")
        d2 = datetime.strptime(today_str, "%Y-%m-%d")
        n  = (d2 - d1).days
        if n <= 0:
            return "NEW!"
        return f"LAST SEEN: {n} day{'s' if n != 1 else ''} ago"
    except Exception:
        return "NEW!"


def _extract_inline_history(entries: list, history: dict) -> int:
    """
    Pass 1: read shopHistory already embedded inside brItems from the
    shop response itself.  No extra HTTP calls needed.
    Returns the number of items whose history was populated this way.
    """
    count = 0
    for entry in entries:
        for item in (entry.get("brItems") or []):
            iid = item.get("id")
            if not iid:
                continue
            raw = item.get("shopHistory") or []
            if not raw:
                continue
            new_dates = sorted({s[:10] for s in raw if s and len(s) >= 10})
            if new_dates:
                existing  = set(history.get(iid, []))
                history[iid] = sorted(existing | set(new_dates))
                count += 1
    return count


def _prefetch_shop_history(item_ids: list, history: dict, language: str) -> None:
    """
    Pass 2: for items STILL missing history after inline extraction, hit the
    individual cosmetics endpoint (which still carries shopHistory).
    Runs up to 12 parallel requests.
    """
    missing = [iid for iid in item_ids if iid not in history]
    if not missing:
        return

    print(Fore.CYAN + f"  Fetching shopHistory for {len(missing)} items via cosmetics API…")

    def _fetch_one(iid: str) -> None:
        try:
            r = requests.get(
                f"{FORTNITE_API}/v2/cosmetics/br/{iid}",
                params={"language": language},
                timeout=8,
            )
            if r.status_code == 200:
                data      = r.json().get("data") or {}
                raw_dates = data.get("shopHistory") or []
                dates     = sorted({s[:10] for s in raw_dates if s and len(s) >= 10})
                if dates:
                    existing = set(history.get(iid, []))
                    history[iid] = sorted(existing | set(dates))
        except Exception:
            pass

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        pool.map(_fetch_one, missing)

    fetched = sum(1 for iid in missing if iid in history)
    print(Fore.GREEN + f"  Got history for {fetched}/{len(missing)} items\n")


def _download_image(url: str, cache_path: str, timeout: int = 12) -> Optional[Image.Image]:
    """Download an image, cache it, return PIL Image or None."""
    if os.path.exists(cache_path):
        try:
            return Image.open(cache_path).convert("RGBA")
        except Exception:
            pass
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        with open(cache_path, "wb") as f:
            f.write(r.content)
        return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception:
        return None


# ── jam track card builder ────────────────────────────────────────────────────

def _is_jam_entry(entry: dict) -> bool:
    """True if this shop entry is purely a Jam Track (no BR items)."""
    return bool(entry.get("tracks")) and not entry.get("brItems")


def _build_jam_card(entry: dict, font_path: Optional[str]) -> Image.Image:
    """
    512×512 card styled for Jam Tracks:
    - Very dark gradient background (deep purple → near-black)
    - Album art centered in the upper ~60 % of the card
    - Equalizer bar decoration above the text block
    - Song title + artist name + price
    """
    track     = (entry.get("tracks") or [{}])[0]
    title     = track.get("title") or _entry_name(entry)
    artist    = track.get("artist") or ""
    album_url = track.get("albumArt") or ""
    price     = entry.get("finalPrice", 0)

    # ── Background: deep purple → near-black gradient ─────────────────────────
    top_col = (26, 5, 46)    # deep purple
    bot_col = (5,  5, 16)    # near-black
    card = Image.new("RGB", (CARD_SZ, CARD_SZ))
    draw = ImageDraw.Draw(card)
    for y in range(CARD_SZ):
        t = y / (CARD_SZ - 1)
        r = int(top_col[0] + (bot_col[0] - top_col[0]) * t)
        g = int(top_col[1] + (bot_col[1] - top_col[1]) * t)
        b = int(top_col[2] + (bot_col[2] - top_col[2]) * t)
        draw.line([(0, y), (CARD_SZ - 1, y)], fill=(r, g, b))

    # ── Album art ─────────────────────────────────────────────────────────────
    ART_SZ = 300
    art_x  = (CARD_SZ - ART_SZ) // 2
    art_y  = 24
    if album_url:
        url_hash   = hashlib.md5(album_url.encode()).hexdigest()[:16]
        cache_path = os.path.join("cache", f"shop_{url_hash}.png")
        art_img    = _download_image(album_url, cache_path)
        if art_img:
            art_img = art_img.convert("RGBA").resize((ART_SZ, ART_SZ), RESAMPLE)
            # Subtle drop-shadow (offset darkened copy pasted first)
            shadow = Image.new("RGBA", (ART_SZ, ART_SZ), (0, 0, 0, 140))
            card.paste(shadow.convert("RGB"), (art_x + 6, art_y + 6))
            card.paste(art_img.convert("RGB"), (art_x, art_y), art_img)

    # ── Equalizer bars (decorative) ───────────────────────────────────────────
    BAR_HEIGHTS = [14, 24, 38, 28, 18, 32, 44, 30, 20, 34, 16, 26]
    BAR_W, BAR_GAP = 10, 5
    total_bar_w = len(BAR_HEIGHTS) * (BAR_W + BAR_GAP) - BAR_GAP
    bx  = (CARD_SZ - total_bar_w) // 2
    by  = art_y + ART_SZ + 10   # just below album art
    bar_color = (160, 80, 255)   # vibrant purple
    for i, h in enumerate(BAR_HEIGHTS):
        x = bx + i * (BAR_W + BAR_GAP)
        draw.rectangle([(x, by - h), (x + BAR_W - 1, by)], fill=bar_color)

    # ── Text ──────────────────────────────────────────────────────────────────
    cx = CARD_SZ // 2
    title_font  = load_font(font_path, 26)
    artist_font = load_font(font_path, 18)
    price_font  = load_font(font_path, 34)

    text_top = by + 14
    # Title — truncate if too long
    if len(title) > 28:
        title = title[:26] + "…"
    draw.text((cx, text_top),      title,  font=title_font,  fill="white",           anchor="ms")
    draw.text((cx, text_top + 30), artist, font=artist_font, fill=(180, 140, 255),   anchor="ms")

    # Price row
    if price:
        price_y = CARD_SZ - 18
        draw = _draw_price_with_icon(card, draw, cx, price_y, price, price_font,
                                     icon_size=28, gap=5)

    return card


# ── single card builder ───────────────────────────────────────────────────────

def _build_card(
    entry: dict,
    today_str: str,
    overlay: Optional[Image.Image],
    font_path: Optional[str],
    history: Optional[dict] = None,
) -> Image.Image:
    """Build a single 512×512 shop card."""

    # ── Background gradient ───────────────────────────────────────────────────
    card = _gradient_bg(entry.get("colors") or {})

    # ── Item image ────────────────────────────────────────────────────────────
    img_url = _best_image_url(entry)
    if img_url:
        url_hash   = hashlib.md5(img_url.encode()).hexdigest()[:16]
        cache_path = os.path.join("cache", f"shop_{url_hash}.png")
        item_img = _download_image(img_url, cache_path)
        if item_img:
            # Scale to fill card width or height (whichever is limiting),
            # preserve aspect ratio, center horizontally, bias toward top
            iw, ih = item_img.size
            scale  = min(CARD_SZ / iw, CARD_SZ / ih)
            new_w  = int(iw * scale)
            new_h  = int(ih * scale)
            item_img = item_img.resize((new_w, new_h), RESAMPLE)
            px = (CARD_SZ - new_w) // 2
            py = max(0, (CARD_SZ - new_h) // 2 - 20)   # slightly top-biased
            card.paste(item_img.convert("RGB"), (px, py), item_img)

    # ── Bottom fade overlay — covers only name + price text area ────────────
    # Programmatic gradient: fully transparent at top of strip → dark at bottom.
    # overlay.png is intentionally ignored; it covers too much of the artwork.
    _OV_START = CARD_SZ - 120   # gradient begins 120px from bottom (y=392)
    ov   = Image.new("RGBA", (CARD_SZ, CARD_SZ), (0, 0, 0, 0))
    ov_d = ImageDraw.Draw(ov)
    for _y in range(_OV_START, CARD_SZ):
        _t     = (_y - _OV_START) / (CARD_SZ - _OV_START)
        _alpha = int(210 * _t)
        ov_d.line([(0, _y), (CARD_SZ - 1, _y)], fill=(0, 0, 0, _alpha))
    card = card.convert("RGBA")
    card.alpha_composite(ov)
    card = card.convert("RGB")

    # ── Text ──────────────────────────────────────────────────────────────────
    draw = ImageDraw.Draw(card)
    cx   = CARD_SZ // 2

    # Price (bottom row)
    price      = entry.get("finalPrice", 0)
    price_font = load_font(font_path, 38)
    price_y    = CARD_SZ - 17
    if price:
        draw = _draw_price_with_icon(card, draw, cx, price_y, price, price_font,
                                     icon_size=32, gap=6)

    # Name (directly above price — section header carries NEW/LEAVING info)
    name      = _entry_name(entry)
    name_font = load_font(font_path, 30)
    name_y    = price_y - 44
    draw.text((cx, name_y), name, font=name_font, fill="white", anchor="ms")

    return card


# ── section image builder ─────────────────────────────────────────────────────

def _section_dates(section_entries: list, today_str: str) -> tuple[bool, str, str]:
    """
    Returns (is_new, leaving_str, raw_out_date).
    is_new:        all entries entered today.
    leaving_str:   human-readable string like "LEAVING IN 3 DAYS".
    raw_out_date:  the latest raw outDate ISO string (for exact time display).
    """
    in_dates:  list[str] = []
    out_dates: list[str] = []
    out_raw:   list[str] = []   # full ISO strings for exact time

    for entry in section_entries:
        in_d      = (entry.get("inDate")  or "")[:10]
        out_full  = (entry.get("outDate") or "")
        out_d     = out_full[:10]
        if in_d  and len(in_d)  == 10:
            in_dates.append(in_d)
        if out_d and len(out_d) == 10:
            out_dates.append(out_d)
            out_raw.append(out_full)

    is_new = bool(in_dates) and all(d == today_str for d in in_dates)

    leaving_str  = ""
    raw_out_date = ""
    if out_dates:
        latest_idx = out_dates.index(max(out_dates))
        latest_out = out_dates[latest_idx]
        raw_out_date = out_raw[latest_idx] if out_raw else ""
        if latest_out >= today_str:
            try:
                out_dt   = datetime.strptime(latest_out, "%Y-%m-%d")
                today_dt = datetime.strptime(today_str,  "%Y-%m-%d")
                days     = (out_dt - today_dt).days
                if days <= 0:
                    leaving_str = "LEAVING TODAY"
                elif days == 1:
                    leaving_str = "LEAVING TOMORROW"
                else:
                    leaving_str = f"LEAVING IN {days} DAYS"
            except Exception:
                pass

    return is_new, leaving_str, raw_out_date


def _section_label(
    section_name: str,
    date_str: str,
    font_path: Optional[str],
    is_new: bool = False,
    leaving_str: str = "",
) -> Image.Image:
    """Build a narrow header bar labelling a section."""
    w    = SHOP_COLS * CARD_SZ
    bar  = Image.new("RGB", (w, HEADER_H), (0, 0, 0))
    draw = ImageDraw.Draw(bar)

    title_font  = load_font(font_path, 86)
    sub_font    = load_font(font_path, 34)
    status_font = load_font(font_path, 24)

    # Line 1: "FORTNITE ITEM SHOP"
    draw.text((w / 2, 104), "FORTNITE ITEM SHOP",
              font=title_font, fill="white", anchor="ms")

    # Line 2: section name + date
    sub = f"{section_name.upper()}  •  {date_str}"
    draw.text((w / 2, 150), sub, font=sub_font, fill=(180, 180, 180), anchor="ms")

    # Line 3: status tags (only if we have something to show)
    status_parts = []
    if is_new:
        status_parts.append("✦ NEW")
    if leaving_str:
        status_parts.append(leaving_str)
    if status_parts:
        status_text = "  ·  ".join(status_parts)
        draw.text((w / 2, 185), status_text,
                  font=status_font, fill=(55, 220, 195), anchor="ms")

    return bar


def _assemble_section(
    section_name: str,
    cards: list[Image.Image],
    date_str: str,
    font_path: Optional[str],
    is_new: bool = False,
    leaving_str: str = "",
) -> Image.Image:
    """Stack a section header + card grid into one image."""
    cols   = SHOP_COLS
    rows   = math.ceil(len(cards) / cols)
    grid_w = cols * CARD_SZ
    grid_h = rows * CARD_SZ

    label = _section_label(section_name, date_str, font_path, is_new, leaving_str)

    full = Image.new("RGB", (grid_w, HEADER_H + grid_h), (0, 0, 0))
    full.paste(label, (0, 0))

    for idx, card in enumerate(cards):
        r = idx // cols
        c = idx % cols
        full.paste(card, (c * CARD_SZ, HEADER_H + r * CARD_SZ))

    return full


# ── public: generate shop ─────────────────────────────────────────────────────

def generate_shop(cfg: dict, tw, progress_cb=None) -> None:
    """
    Generate item shop images split by section.

    progress_cb: optional callable(float 0.0–1.0) called after each card is
                 attempted, so the GUI can update a progress bar in real time.
    iconType from settings is intentionally ignored — shop always uses
    its own fixed card style (gradient bg + overlay + Burbank text).
    """
    language = cfg["language"]
    name_lbl = cfg["name"]
    auto_tw  = cfg["AutoTweetMerged"]

    # Shop always uses BurbankBigRegular-BlackItalic regardless of sideFont setting
    font_path = _SHOP_FONT if os.path.exists(_SHOP_FONT) else None

    # ── Clear icons + cache + stale shop images ──────────────────────────────
    for d in ("icons", "cache"):
        try:
            shutil.rmtree(d)
        except FileNotFoundError:
            pass
        os.makedirs(d, exist_ok=True)
    os.makedirs("merged", exist_ok=True)
    # Remove old section images so re-runs don't show stale duplicates
    import glob as _glob
    for old_f in _glob.glob("merged/shop_*.jpg"):
        try:
            os.remove(old_f)
        except Exception:
            pass
    try:
        os.remove("merged/shop.jpg")
    except FileNotFoundError:
        pass

    # ── Fetch shop ────────────────────────────────────────────────────────────
    print(Fore.CYAN + "\nFetching Item Shop…")
    data = _get_json(f"{FORTNITE_API}/v2/shop", params={"language": language})
    if not data:
        print(Fore.RED + "Failed to fetch shop.")
        return

    today_str = (data.get("data") or {}).get("date", "")[:10] or \
                datetime.utcnow().strftime("%Y-%m-%d")
    entries   = (data.get("data") or {}).get("entries", [])

    if not entries:
        print(Fore.RED + "No shop entries found.")
        return

    print(Fore.GREEN + f"Found {len(entries)} entries in {today_str} shop\n")

    # ── Load local shop history (for "last seen" dates) ───────────────────────
    history = _load_history()

    # Pass 1: extract shopHistory already embedded in the shop response itself
    inline = _extract_inline_history(entries, history)
    print(Fore.CYAN + f"  Inline shopHistory: {inline} items populated from shop data")

    # Pass 2: for any items still missing, hit individual cosmetics endpoint
    all_item_ids = [
        item["id"]
        for entry in entries
        for item in (entry.get("brItems") or [])
        if item.get("id")
    ]
    _prefetch_shop_history(all_item_ids, history, language)

    # ── Load overlay ──────────────────────────────────────────────────────────
    overlay = None
    ov_path = os.path.join("assets", "overlay.png")
    if os.path.exists(ov_path):
        try:
            overlay = Image.open(ov_path).convert("RGBA").resize(
                (CARD_SZ, CARD_SZ), RESAMPLE
            )
        except Exception:
            pass

    # ── Deduplicate entries by offerId to prevent double-rendering ───────────
    seen_offer_ids: set = set()
    deduped: list = []
    for entry in entries:
        oid = entry.get("offerId") or entry.get("id") or None
        if oid:
            if oid in seen_offer_ids:
                continue
            seen_offer_ids.add(oid)
        deduped.append(entry)
    entries = deduped

    # ── Group entries by section (case-insensitive dedup) ────────────────────
    _STW_NAMES  = {"save the world"}
    _MUSIC_KEYS = {"jam track", "jam tracks", "music"}

    def _canonical_section(raw: str) -> str:
        """Normalise variant layout names → single canonical key."""
        cleaned = raw.strip()
        lower   = cleaned.lower()
        if any(k in lower for k in _MUSIC_KEYS):
            return "Jam Tracks"
        if lower in _STW_NAMES:
            return "Save the World"
        return cleaned

    # Use lowercase key for dedup; keep first-seen display name
    sections:      dict[str, list] = {}   # lower_key → [entries]
    section_names: dict[str, str]  = {}   # lower_key → display name
    section_order: list[str]       = []   # ordered lower_keys

    for entry in entries:
        layout    = entry.get("layout") or {}
        raw_name  = layout.get("name") or "Other"
        canonical = _canonical_section(raw_name)
        key       = canonical.lower()
        if key not in sections:
            sections[key]      = []
            section_names[key] = canonical
            section_order.append(key)
        sections[key].append(entry)

    # Sort: 0 = BR cosmetics, 1 = STW, 2 = Jam Tracks, 3 = other
    def section_priority(key: str) -> int:
        if key in _STW_NAMES:
            return 1
        if any(k in key for k in _MUSIC_KEYS):
            return 2
        has_br = any(e.get("brItems") for e in sections[key])
        return 0 if has_br else 3

    original_order = {k: i for i, k in enumerate(section_order)}
    section_order.sort(key=lambda k: (section_priority(k), original_order[k]))

    print(Fore.CYAN + f"Sections: {', '.join(section_names[k] for k in section_order)}\n")

    # ── Pre-count buildable entries for progress bar ──────────────────────────
    _total_buildable = sum(
        1 for k in section_order
        for e in sections[k]
        if not _is_jam_entry(e)
    )
    _done = 0

    def _tick():
        nonlocal _done
        _done += 1
        if progress_cb and _total_buildable:
            progress_cb(_done / _total_buildable)

    # ── Generate each section ─────────────────────────────────────────────────
    first_output    = None
    total_generated = 0
    shop_meta: dict = {}   # filename → {label, is_new, leaving, out_date} for GUI

    for sec_key in section_order:
        sec_entries = sections[sec_key]
        sec_name    = section_names[sec_key]
        cards: list[Image.Image] = []

        print(Fore.CYAN + f"  [{sec_name}] — {len(sec_entries)} entries")

        for idx, entry in enumerate(sec_entries, 1):
            # Jam tracks live on their own page — skip them here
            if _is_jam_entry(entry):
                continue

            e_name = _entry_name(entry)
            e_img  = _best_image_url(entry)

            # Skip empty/unknown entries (no name AND no image)
            if e_name == "Unknown" and e_img is None:
                print(Fore.YELLOW + f"\n    Skipping empty entry (no name/image)")
                _tick()
                continue

            try:
                card = _build_card(entry, today_str, overlay, font_path, history)
                cards.append(card)
                print(Fore.CYAN + f"    {idx}/{len(sec_entries)}", end="\r")
            except Exception as e:
                print(Fore.YELLOW + f"\n    Skipped '{e_name}': {e}")
            _tick()

        print()  # newline after \r progress

        if not cards:
            continue

        is_new, leaving_str, raw_out_date = _section_dates(sec_entries, today_str)

        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in sec_name).strip()
        out_fname = f"shop_{safe_name}_{today_str}.jpg"
        out_path  = f"merged/{out_fname}"
        img = _assemble_section(sec_name, cards, today_str, font_path, is_new, leaving_str)
        img.save(out_path, "JPEG", quality=92, optimize=True)
        print(Fore.GREEN + f"  → {out_path}")

        shop_meta[out_fname] = {
            "label":    sec_name,
            "is_new":   is_new,
            "leaving":  leaving_str,
            "out_date": raw_out_date,
        }

        total_generated += len(cards)

        if first_output is None:
            first_output = out_path
            img.save("merged/shop.jpg", "JPEG", quality=92, optimize=True)

    # ── Save section metadata for GUI display ─────────────────────────────────
    try:
        with open("merged/shop_meta.json", "w") as _f:
            json.dump(shop_meta, _f)
    except Exception:
        pass

    # ── Save history for future runs ──────────────────────────────────────────
    _save_history(history, entries, today_str)

    print(Fore.GREEN + f"\nDone — {total_generated} cards across {len(section_order)} sections.")

    # ── Optionally tweet first section ────────────────────────────────────────
    if auto_tw and tw and tw.ready and first_output:
        text = f"[{name_lbl}] Today's Fortnite Item Shop — {total_generated} items."
        try:
            tw.tweet_with_media(first_output, text)
            print(Fore.GREEN + "Tweeted shop!")
        except Exception as e:
            print(Fore.YELLOW + f"  Compressing: {e}")
            compress_image(first_output)
            try:
                tw.tweet_with_media(first_output, text)
            except Exception as e2:
                print(Fore.RED + f"  Tweet failed: {e2}")


# ── public: jam tracks fetch (used by JamTracksPage) ─────────────────────────

def fetch_jam_tracks(language: str = "en") -> list[dict]:
    """
    Fetch today's shop and return a list of jam track metadata dicts, each with:
      title, artist, albumArt, price, spotify, appleMusic
    Returns [] on error.
    """
    from urllib.parse import quote as _url_quote

    data = _get_json(f"{FORTNITE_API}/v2/shop", params={"language": language})
    if not data:
        return []

    entries = (data.get("data") or {}).get("entries", [])
    tracks_out = []

    for entry in entries:
        if not _is_jam_entry(entry):
            continue
        track  = (entry.get("tracks") or [{}])[0]
        title  = track.get("title", "")
        artist = track.get("artist", "")
        art    = track.get("albumArt", "")
        price  = entry.get("finalPrice", 500)

        if not title and not art:
            continue  # skip empty

        q = _url_quote(f"{title} {artist}".strip())
        tracks_out.append({
            "title":      title,
            "artist":     artist,
            "albumArt":   art,
            "price":      price,
            "spotify":    f"https://open.spotify.com/search/{q}",
            "appleMusic": f"https://music.apple.com/search?term={q}",
        })

    return tracks_out


# ── public: shop-hash watcher ─────────────────────────────────────────────────

def watch_shop_sections(cfg: dict, tw) -> None:
    """Poll for shop hash changes and tweet when it updates."""
    delay    = cfg["BotDelay"]
    language = cfg["language"]
    name_lbl = cfg["name"]

    print(Fore.CYAN + f"\n-- Shop Watcher --  (delay={delay}s)")
    print(Fore.YELLOW + "Press Ctrl-C to stop.\n")

    old_hash = None
    count    = 0

    try:
        while True:
            data = _get_json(f"{FORTNITE_API}/v2/shop", params={"language": language})
            if data:
                shop_hash = (data.get("data") or {}).get("hash", "")
                if old_hash is None:
                    old_hash = shop_hash
                    print(Fore.GREEN + "  Watching shop hash…")
                elif shop_hash != old_hash:
                    print(Fore.CYAN + "\n  [!] Shop updated!")
                    tweet_text = f"[{name_lbl}] Fortnite Item Shop has updated!"
                    if tw and tw.ready:
                        try:
                            tw.tweet(tweet_text)
                            print(Fore.GREEN + "  Tweeted shop update!")
                        except Exception as e:
                            print(Fore.RED + f"  Tweet failed: {e}")
                    else:
                        print(Fore.YELLOW + f"  (Twitter not configured)\n{tweet_text}")
                    old_hash = shop_hash
                else:
                    count += 1
                    print(Fore.GREEN + f"  Watching… ({count})", end="\r")
            time.sleep(delay)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nShop watcher stopped.")
