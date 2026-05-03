"""
image_gen.py — Pillow 10+ compatible cosmetic card generator.

Key fixes vs the original AutoLeak:
  - PIL.Image.ANTIALIAS removed in Pillow 10 → use PIL.Image.LANCZOS
  - font.getsize() removed → use font.getbbox()
  - draw.textsize() removed → use draw.textbbox()
  - Consolidated all icon-type branches into one function instead of
    copy-pasted newcnew_fnbrapi / generate_cosmetics / newiconsfnapi etc.
"""

from __future__ import annotations

import io
import os
import textwrap
from enum import Enum
from typing import Optional

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── constants ─────────────────────────────────────────────────────────────────
SIZE        = 512
RESAMPLE    = Image.LANCZOS        # Was PIL.Image.ANTIALIAS (removed in Pillow 10)
FALLBACK_BG = (50, 50, 80, 255)   # Dark blue-grey RGBA

LARGE_W = 1793
LARGE_H = 1080

# Rarity → (button_fill_rgb, button_text_rgb)
_RARITY_COLORS: dict[str, tuple[tuple[int,int,int], tuple[int,int,int]]] = {
    "common":       ((184, 184, 184), (92,  92,  92 )),
    "uncommon":     ((101, 197, 0  ), (2,   80,  2  )),
    "rare":         ((0,   180, 255), (0,   69,  138)),
    "epic":         ((209, 90,  255), (76,  25,  123)),
    "legendary":    ((255, 139, 25 ), (138, 60,  30 )),
    "mythic":       ((245, 228, 106), (120, 100, 20 )),
    "exotic":       ((125, 232, 245), (0,   100, 120)),
    "icon":         ((92,  242, 243), (0,   73,  74 )),
    "slurp":        ((64,  217, 232), (0,   100, 110)),
    "marvel":       ((229, 33,  43 ), (89,  7,   12 )),
    "dc":           ((106, 159, 217), (40,  90,  150)),
    "starwars":     ((255, 245, 127), (110, 90,  20 )),
    "dark":         ((96,  64,  168), (45,  27,  105)),
    "frozen":       ((200, 232, 245), (80,  130, 180)),
    "lava":         ((255, 144, 96 ), (150, 60,  20 )),
    "shadow":       ((150, 150, 165), (60,  60,  75 )),
    "gaminglegends":((128, 120, 255), (40,  8,   95 )),
    "lambskin":     ((224, 196, 148), (120, 90,  50 )),
    "shadowfoil":   ((122, 122, 170), (50,  50,  90 )),
}


def _rarity_colors(rarity: str) -> tuple[tuple[int,int,int], tuple[int,int,int]]:
    return _RARITY_COLORS.get(rarity.lower(), ((184, 184, 184), (92, 92, 92)))


def _wm_xy(pos: str, img_w: int, img_h: int,
           text_w: int, text_h: int, margin: int = 12) -> tuple[int, int]:
    """Convert a position label to (x, y) pixel coordinates for watermark."""
    p = (pos or "top-left").lower().replace(" ", "-")
    if p == "top-right":
        return (img_w - text_w - margin, margin)
    if p == "top-center":
        return ((img_w - text_w) // 2, margin)
    if p == "bottom-left":
        return (margin, img_h - text_h - margin)
    if p == "bottom-right":
        return (img_w - text_w - margin, img_h - text_h - margin)
    if p == "bottom-center":
        return ((img_w - text_w) // 2, img_h - text_h - margin)
    return (margin, margin)   # default: top-left


class CardStyle(str, Enum):
    STANDARD = "standard"
    CLEAN    = "clean"
    NEW      = "new"
    CATABA   = "cataba"
    LARGE    = "large"


# ── Pillow-compat helpers ─────────────────────────────────────────────────────

def text_size(font: ImageFont.FreeTypeFont, text: str) -> tuple[int, int]:
    """Return (width, height) of rendered text — Pillow 10+ compatible."""
    bbox = font.getbbox(text)          # (left, top, right, bottom)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    """Return (width, height) via draw.textbbox — Pillow 10+ compatible."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def centered_x(img_width: int, text: str, font: ImageFont.FreeTypeFont) -> int:
    w, _ = text_size(font, text)
    return (img_width - w) // 2


# ── font loader ───────────────────────────────────────────────────────────────

def load_font(path: Optional[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a TrueType/OpenType font, falling back to PIL's built-in default."""
    if path and os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            pass
    # Pillow 10+ default font is bitmap but always available
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        # Pillow < 10 doesn't accept size kwarg on load_default
        return ImageFont.load_default()


# ── icon downloader ───────────────────────────────────────────────────────────

def fetch_icon(url: str) -> Image.Image:
    """Download and return a 512×512 RGBA icon image."""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        return img.resize((SIZE, SIZE), RESAMPLE)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch icon from {url}: {e}") from e


# ── rarity background loader ──────────────────────────────────────────────────

def load_rarity_bg(icon_type: str, rarity: str) -> Image.Image:
    """
    Load a rarity background PNG from rarities/<icon_type>/<rarity>.png.
    Falls back to 'common' if the specific rarity file is missing.
    Falls back to a generated solid-colour image if even common is missing.
    """
    base = os.path.join("rarities", icon_type)
    for name in (rarity, "common"):
        path = os.path.join(base, f"{name}.png")
        if os.path.exists(path):
            try:
                return Image.open(path).convert("RGBA").resize((SIZE, SIZE), RESAMPLE)
            except Exception:
                pass
    # Last resort: solid colour
    return Image.new("RGBA", (SIZE, SIZE), FALLBACK_BG)


def load_rarity_layer(icon_type: str, prefix: str, rarity: str) -> Optional[Image.Image]:
    """Load an optional overlay/border layer (e.g. border{rarity}.png)."""
    base = os.path.join("rarities", icon_type)
    for name in (rarity, "common"):
        path = os.path.join(base, f"{prefix}{name}.png")
        if os.path.exists(path):
            try:
                return Image.open(path).convert("RGBA").resize((SIZE, SIZE), RESAMPLE)
            except Exception:
                pass
    return None


# ── source tag helper ─────────────────────────────────────────────────────────

def get_source_tag(item: dict, build: str = "") -> str:
    """Extract a human-readable source tag from gameplay tags."""
    tags = item.get("gameplayTags") or []
    for tag in tags:
        if "Cosmetics.Source.ItemShop" in tag:
            return "Cosmetics.Source.ItemShop"
        if "BattlePass.Paid" in tag:
            return f"Cosmetics.Source.Season{build}.BattlePass.Paid"
        if "Cosmetics.Set." in tag:
            set_val = (item.get("set") or {}).get("value", "")
            return f"Cosmetics.Set.{set_val.replace(' ', '')}"
    return ""


# ── per-style renderers ───────────────────────────────────────────────────────

def _render_standard(img: Image.Image, item: dict,
                      font_main: str, font_side: str,
                      watermark: str, show_source: bool, build: str,
                      watermark_pos: str = "top-left") -> Image.Image:
    """Standard style: centred name + description + type text."""
    draw  = ImageDraw.Draw(img)
    name  = (item.get("name") or "TBD").upper()
    desc  = item.get("description") or ""
    cos_t = (item.get("type") or {}).get("displayValue", "")
    item_id = item.get("id", "")

    name_len = len(name)
    fs = 40 if name_len <= 20 else (30 if name_len <= 30 else 20)

    font  = load_font(font_main, fs)
    fw, _ = draw_text_size(draw, name, font)
    draw.text(((SIZE - fw) / 2, 390), name, font=font, fill="white")

    font_sm = load_font(font_main, 20)
    fw, _ = draw_text_size(draw, cos_t, font_sm)
    draw.text(((SIZE - fw) / 2, 430), cos_t, font=font_sm, fill="white")

    font_xs = load_font(font_side, 15)
    fw, _ = draw_text_size(draw, desc, font_xs)
    draw.text(((SIZE - fw) / 2, 455), desc, font=font_xs, fill="white")

    fw, _ = draw_text_size(draw, item_id, font_xs)
    draw.text(((SIZE - fw) / 2, 475), item_id, font=font_xs, fill="white")

    if watermark:
        wm_font = load_font(font_main, 25)
        tw, th  = draw_text_size(draw, watermark, wm_font)
        draw.text(_wm_xy(watermark_pos, img.width, img.height, tw, th),
                  watermark, font=wm_font, fill="white")

    return img


def _render_clean(img: Image.Image, item: dict,
                  font_main: str, font_side: str,
                  watermark: str, show_source: bool, build: str,
                  watermark_pos: str = "top-left") -> Image.Image:
    """Clean style: left-aligned name + type."""
    draw  = ImageDraw.Draw(img)
    name  = item.get("name") or "TBD"
    cos_t = (item.get("type") or {}).get("displayValue", "")

    name_len = len(name)
    fs = 40 if name_len <= 20 else (30 if name_len <= 30 else 20)

    font = load_font(font_main, fs)
    draw.text((25, 440), name, font=font, fill="white")

    font_type = load_font(font_main, 30)
    draw.text((25, 402), cos_t, font=font_type, fill="white")

    if watermark:
        wm_font = load_font(font_main, 25)
        tw, th  = draw_text_size(draw, watermark, wm_font)
        draw.text(_wm_xy(watermark_pos, img.width, img.height, tw, th),
                  watermark, font=wm_font, fill="white")

    return img


def _render_new(img: Image.Image, item: dict,
                font_main: str, font_side: str,
                watermark: str, show_source: bool, build: str,
                watermark_pos: str = "top-left") -> Image.Image:
    """
    'New' style: large centred name + description + set text.
    Mirrors the newcnew_fnbrapi / newiconsfnapi logic from the original.
    """
    draw = ImageDraw.Draw(img)
    cx   = SIZE // 2   # horizontal centre

    name = (item.get("name") or "TBD").upper()
    desc = item.get("description") or "TBD"
    set_text = (item.get("set") or {}).get("text")

    # --- Name ---
    if len(name) > 17:
        name_font = load_font(font_main, 45)
        name_y    = 440
        desc_nudge = True
    else:
        name_font = load_font(font_main, 60)
        name_y    = 450
        desc_nudge = False

    draw.text((cx, name_y), name, font=name_font, fill="white", anchor="ms")

    # --- Description ---
    desc_len = len(desc)
    if desc_len > 95:
        d_font = load_font(font_side, 10)
        d_y    = 470
    elif desc_len > 45:
        d_font = load_font(font_side, 14)
        d_y    = (474 if set_text else 480) - (8 if desc_nudge else 0)
    else:
        d_font = load_font(font_side, 16)
        d_y    = (475 if set_text else 480) - (2 if desc_nudge else 0)

    draw.text((cx, d_y), desc, font=d_font, fill="white", anchor="ms")

    # --- Set text ---
    if set_text:
        s_font = load_font(font_side, 15)
        draw.text((cx, 500), set_text, font=s_font, fill="white", anchor="ms")

    # --- Watermark ---
    if watermark:
        wm_font = load_font(font_main, 25)
        tw, th  = draw_text_size(draw, watermark, wm_font)
        draw.text(_wm_xy(watermark_pos, img.width, img.height, tw, th),
                  watermark, font=wm_font, fill="white")
        wm_y = 30
    else:
        wm_y = 10

    # --- Source tag ---
    if show_source:
        tag = get_source_tag(item, build)
        if tag:
            tag_font = load_font(font_main, 15)
            draw.text((10, wm_y), tag, font=tag_font, fill="white")

    return img


def _render_cataba(img: Image.Image, item: dict,
                   font_main: str, font_side: str,
                   watermark: str, show_source: bool, build: str,
                   watermark_pos: str = "top-left") -> Image.Image:
    """
    'Cataba' style: centred name + description (upper-cased) + backend type badge.
    Matches the catabaicons / catabasearch logic.
    """
    draw        = ImageDraw.Draw(img)
    name        = (item.get("name") or "TBD").upper()
    description = (item.get("description") or "").upper()
    backend_t   = (item.get("type") or {}).get("value", "").upper()

    # Use BurbankBigRegular-BlackItalic if available, else fall back to font_main
    cataba_font_path = os.path.join("fonts", "BurbankBigRegular-BlackItalic.otf")
    if not os.path.exists(cataba_font_path):
        cataba_font_path = font_main

    name_font = load_font(cataba_font_path, 31)
    desc_font = load_font(cataba_font_path, 10)
    type_font = load_font(cataba_font_path, 14)

    draw.text((256, 472), name,        font=name_font, fill="white", anchor="ms")
    draw.text((256, 501), description, font=desc_font, fill="white", anchor="ms")
    draw.text((6,   495), backend_t,   font=type_font, fill="white")

    return img


# ── cataba layer compositor ───────────────────────────────────────────────────

def _composite_cataba(rarity: str, icon_img: Image.Image, has_variants: bool) -> Image.Image:
    """Build the cataba layered composite (background → overlay → icon → foreground → rarity badge)."""
    base = os.path.join("rarities", "cataba")

    def try_open(name: str) -> Optional[Image.Image]:
        path = os.path.join(base, name)
        if os.path.exists(path):
            try:
                return Image.open(path).resize((SIZE, SIZE), RESAMPLE).convert("RGBA")
            except Exception:
                pass
        return None

    canvas = Image.new("RGB", (SIZE, SIZE))

    # Layer 1: rarity background
    layer = try_open(f"{rarity}.png") or try_open("common.png") or Image.new("RGBA", (SIZE, SIZE), FALLBACK_BG)
    canvas.paste(layer)

    # Layer 2: overlay
    overlay = try_open(f"{rarity}_overlay.png") or try_open("common_overlay.png")
    if overlay:
        canvas.paste(overlay, (0, 0), overlay)

    # Layer 3: icon
    canvas.paste(icon_img, (0, 0), icon_img)

    # Layer 4: foreground
    fg = try_open(f"{rarity}_background.png") or try_open("common_background.png")
    if fg:
        canvas.paste(fg, (0, 0), fg)

    # Layer 5: rarity badge
    badge = try_open(f"{rarity}_rarity.png") or try_open("placeholder_rarity.png")
    if badge:
        canvas.paste(badge, (0, 0), badge)

    # Layer 6: variants plus-sign
    if has_variants:
        plus = try_open("PlusSign.png")
        if plus:
            canvas.paste(plus, (0, 0), plus)

    return canvas


# ── large-style full card generator ──────────────────────────────────────────

def _generate_large_card(
    item: dict,
    icon_url: str,
    font_main: Optional[str],
    font_side: Optional[str],
    watermark: str,
    show_source: bool,
    build: str,
    watermark_pos: str = "top-left",
) -> Image.Image:
    """
    Build a 1793×1080 large-style cosmetic card matching the original AutoLeak design.

    Layout:
      Right side  — cosmetic icon (1083×1083) on cataba rarity background, at x=710
      Left side   — dark diagonal panel overlay (card.png)
      Text layer  — name, rarity button, backend type, description, set/ID/season
      Variants    — up to 6 variant preview images in a 3×2 grid (if item has styles)
    """
    ICON_SZ   = 1083
    DIAG_TOP  = 620   # must match setup.py _make_large_card()
    DIAG_BOT  = 740

    rarity   = (item.get("rarity") or {}).get("value", "common").lower()
    name     = (item.get("name") or "TBD").upper()
    desc     = (item.get("description") or "").upper()
    rarity_v = (item.get("rarity") or {}).get("value", "common")
    backend  = (item.get("type") or {}).get("value", "").upper()
    set_val  = ((item.get("set") or {}).get("value") or "N/A")
    item_id  = item.get("id", "")

    try:
        season = f"C{item['introduction']['chapter']} S{item['introduction']['season']}"
    except Exception:
        season = "N/A"
    season_line = season
    for tag in (item.get("gameplayTags") or []):
        if "ItemShop" in tag:
            season_line = f"{season} | ITEMSHOP"
            break

    # ── 1. Download icon — always prefer featured for full-body shots ─────────
    # For skins/backpacks the featured image shows the full character;
    # fall back to icon_url if featured isn't available.
    images     = item.get("images") or {}
    best_url   = images.get("featured") or images.get("icon") or icon_url
    try:
        resp = requests.get(best_url, timeout=15)
        resp.raise_for_status()
        icon_img = Image.open(io.BytesIO(resp.content)).convert("RGBA").resize((ICON_SZ, ICON_SZ), RESAMPLE)
    except Exception:
        icon_img = Image.new("RGBA", (ICON_SZ, ICON_SZ), FALLBACK_BG)

    # ── 2. Cataba rarity background at 1083×1083 ─────────────────────────────
    def _try_open_cataba(name_: str) -> Optional[Image.Image]:
        p = os.path.join("rarities", "cataba", f"{name_}.png")
        if os.path.exists(p):
            try:
                return Image.open(p).resize((ICON_SZ, ICON_SZ), RESAMPLE).convert("RGBA")
            except Exception:
                pass
        return None

    rarity_bg = _try_open_cataba(rarity) or _try_open_cataba("common") \
                or Image.new("RGBA", (ICON_SZ, ICON_SZ), FALLBACK_BG)

    icon_composite = Image.new("RGB", (ICON_SZ, ICON_SZ))
    icon_composite.paste(rarity_bg.convert("RGB"))
    icon_composite.paste(icon_img, (0, 0), icon_img)

    # ── 3. Main canvas ────────────────────────────────────────────────────────
    canvas = Image.new("RGB", (LARGE_W, LARGE_H), (0, 0, 0))
    canvas.paste(icon_composite, (710, 0))

    # ── 4. Dark panel overlay (card.png) ─────────────────────────────────────
    card_path = os.path.join("rarities", "large", "card.png")
    if os.path.exists(card_path):
        try:
            card_ov = Image.open(card_path).convert("RGBA")
            canvas.paste(card_ov, (0, 0), card_ov)
        except Exception:
            pass
    else:
        # Inline fallback so we never fail silently
        fallback = Image.new("RGBA", (LARGE_W, LARGE_H), (0, 0, 0, 0))
        ImageDraw.Draw(fallback).polygon(
            [(0, 0), (DIAG_TOP, 0), (DIAG_BOT, LARGE_H), (0, LARGE_H)],
            fill=(12, 10, 18, 252)
        )
        canvas.paste(fallback, (0, 0), fallback)

    # ── 5. Font selection ─────────────────────────────────────────────────────
    # Original used BurbankBigRegular-Black for the name and BlackItalic for
    # everything else.  Fall back to font_main if those aren't in fonts/.
    burbank_black  = os.path.join("fonts", "BurbankBigRegular-Black.ttf")
    burbank_italic = os.path.join("fonts", "BurbankBigRegular-BlackItalic.otf")
    if not os.path.exists(burbank_black):
        burbank_black = font_main
    if not os.path.exists(burbank_italic):
        burbank_italic = font_main

    draw = ImageDraw.Draw(canvas)

    # Define rarity button position up-front so it can constrain name layout
    BOX_X, BOX_Y = 28, 118

    # ── 6. Name — dynamic size + wrapping, must stay above rarity button ────────
    # Available area: x=30..590, y=30..BOX_Y-10 (=108)
    NAME_X      = 30
    NAME_Y_TOP  = 30
    NAME_MAX_W  = 580   # panel width before diagonal
    NAME_MAX_H  = BOX_Y - NAME_Y_TOP - 10   # pixels available

    name_drawn = False
    for fs in (60, 52, 44, 38, 32):
        name_font = load_font(burbank_black, fs)

        # ── Try single line ──
        bb = name_font.getbbox(name)
        tw_, th_ = bb[2] - bb[0], bb[3] - bb[1]
        if tw_ <= NAME_MAX_W and th_ <= NAME_MAX_H:
            draw.text((NAME_X, NAME_Y_TOP - bb[1]), name, font=name_font, fill="white")
            name_drawn = True
            break

        # ── Try 2-line split ──
        words = name.split()
        for split_at in range(1, len(words)):
            l1 = " ".join(words[:split_at])
            l2 = " ".join(words[split_at:])
            b1, b2 = name_font.getbbox(l1), name_font.getbbox(l2)
            lh = max(b1[3] - b1[1], b2[3] - b2[1])
            if (b1[2]-b1[0] <= NAME_MAX_W and b2[2]-b2[0] <= NAME_MAX_W
                    and lh * 2 + 6 <= NAME_MAX_H):
                draw.text((NAME_X, NAME_Y_TOP - b1[1]), l1,
                          font=name_font, fill="white")
                draw.text((NAME_X, NAME_Y_TOP + lh + 4 - b2[1]), l2,
                          font=name_font, fill="white")
                name_drawn = True
                break
        if name_drawn:
            break

    if not name_drawn:
        # Last resort: draw at smallest size, may still be long
        nf = load_font(burbank_black, 30)
        draw.text((NAME_X, NAME_Y_TOP), name, font=nf, fill="white")

    # ── 7. Rarity colored button + backend type ───────────────────────────────
    body_font = load_font(burbank_italic, 39)
    btn_color, txt_color = _rarity_colors(rarity_v)

    rarity_upper = rarity_v.upper()

    # Measure actual rendered glyph bounds (accounts for font bearing / italic slant)
    rb = body_font.getbbox(rarity_upper)
    text_w = rb[2] - rb[0]   # visual width
    text_h = rb[3] - rb[1]   # visual height

    PAD_X, PAD_Y = 18, 8
    tag_w = text_w + PAD_X * 2
    tag_h = text_h + PAD_Y * 2

    btn_img = Image.new("RGBA", (tag_w, tag_h), btn_color + (255,))
    canvas.paste(btn_img, (BOX_X, BOX_Y), btn_img)
    draw = ImageDraw.Draw(canvas)

    # Position draw origin so the visual glyph is centred in the box
    draw.text((BOX_X + PAD_X - rb[0], BOX_Y + PAD_Y - rb[1]),
              rarity_upper, font=body_font, fill=txt_color)

    # Backend type — vertically aligned with the rarity button centre
    backend_x = BOX_X + tag_w + 20
    bb = body_font.getbbox(backend) if backend else (0, 0, 0, 0)
    backend_draw_y = BOX_Y + (tag_h - (bb[3] - bb[1])) // 2 - bb[1]
    draw.text((backend_x, backend_draw_y), backend, font=body_font, fill="white")

    # ── 8. Description (wrapped, y=210) ──────────────────────────────────────
    wrapped = textwrap.fill(desc, 30)
    draw.text((34, 210), wrapped, font=body_font, fill="white")

    # ── 9. Bottom metadata ────────────────────────────────────────────────────
    meta_font = load_font(burbank_italic, 35)
    id_font   = load_font(burbank_italic, 25)
    meta_col  = (200, 197, 196)

    draw.text((20, 935),  f"Set: {set_val}",  font=meta_font, fill=meta_col)
    draw.text((20, 995),  f"ID:  {item_id}",  font=id_font,   fill=meta_col)
    draw.text((20, 1035), season_line,         font=meta_font, fill=meta_col)

    # ── 10. Watermark ─────────────────────────────────────────────────────────
    if watermark:
        wm_font = load_font(burbank_black, 30)
        tw, th  = draw_text_size(draw, watermark, wm_font)
        draw.text(_wm_xy(watermark_pos, canvas.width, canvas.height, tw, th),
                  watermark, font=wm_font, fill=(255, 255, 255, 180))

    # ── 11. Variants section (up to 6 style previews) ─────────────────────────
    variants_list = item.get("variants") or []
    if variants_list:
        opts = [
            o for o in (variants_list[0].get("options") or [])
            if o.get("name") not in ("DEFAULT", "Stage1")
        ]
        if opts:
            # Dark semi-transparent background for the whole variants area
            var_bg = Image.new("RGBA", (LARGE_W, LARGE_H), (0, 0, 0, 0))
            ImageDraw.Draw(var_bg).rectangle(
                [0, 330, 575, 758], fill=(18, 16, 26, 215)
            )
            canvas.paste(var_bg, (0, 0), var_bg)
            draw = ImageDraw.Draw(canvas)

            # "STYLES" header
            styles_font = load_font(burbank_italic, 28)
            draw.text((35, 354), "STYLES", font=styles_font, fill=(200, 200, 200))

            # Variant count + "+" circle
            count_font = load_font(burbank_italic, 35)
            draw.text((240, 342), str(len(opts)), font=count_font, fill=(153, 153, 153))
            cx, cy, r = 207, 360, 20
            draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                         fill=(45, 43, 55), outline=(170, 170, 170), width=2)
            try:
                plus_f = ImageFont.load_default(size=26)
            except TypeError:
                plus_f = ImageFont.load_default()
            draw.text((cx, cy), "+", font=plus_f, fill=(190, 190, 190), anchor="mm")

            # 3-column × 2-row grid of variant preview images
            GRID = [
                (24, 390), (204, 390), (384, 390),
                (24, 570), (204, 570), (384, 570),
            ]
            for opt, (gx, gy) in zip(opts[:6], GRID):
                v_url = opt.get("image")
                if not v_url:
                    continue
                try:
                    vr   = requests.get(v_url, timeout=10)
                    vimg = Image.open(io.BytesIO(vr.content)) \
                               .resize((157, 157), RESAMPLE).convert("RGBA")
                    vbox = Image.new("RGB", (157, 157), (33, 31, 32))
                    vbox.paste(vimg, (0, 0), vimg)
                    canvas.paste(vbox, (gx, gy))
                except Exception:
                    pass

    return canvas


# ── main public function ──────────────────────────────────────────────────────

def generate_card(
    item: dict,
    icon_url: str,
    out_path: str,
    icon_type: str,
    font_main: Optional[str],
    font_side: Optional[str],
    watermark: str = "",
    show_source: bool = True,
    build: str = "",
    watermark_pos: str = "top-left",
) -> None:
    """
    Generate a styled cosmetic card image and write it to out_path.

    Parameters
    ----------
    item          : Fortnite-API cosmetic item dict
    icon_url      : URL of the cosmetic's icon/featured image
    out_path      : Where to save the finished PNG
    icon_type     : One of 'standard', 'clean', 'new', 'cataba', 'large'
    font_main     : Path to primary font (None → PIL default)
    font_side     : Path to secondary font (None → PIL default)
    watermark     : Text watermark string
    show_source   : Whether to draw the gameplay source tag
    build         : Fortnite version label (used in source tag)
    watermark_pos : One of 'top-left', 'top-right', 'top-center',
                    'bottom-left', 'bottom-right', 'bottom-center'
    """
    # ── Large style: completely different canvas size — handle separately ────────
    if icon_type == CardStyle.LARGE:
        img = _generate_large_card(item, icon_url, font_main, font_side,
                                   watermark, show_source, build, watermark_pos)
        os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)
        img.save(out_path)
        return

    rarity = (item.get("rarity") or {}).get("value", "common").lower()

    # ── 1. Download icon ──────────────────────────────────────────────────────
    icon_img = fetch_icon(icon_url)   # 512×512 RGBA

    # ── 2. Build base composite ───────────────────────────────────────────────
    if icon_type == CardStyle.CATABA:
        has_variants = bool(item.get("variants"))
        img = _composite_cataba(rarity, icon_img, has_variants)
        img = img.convert("RGB")      # cataba canvas is RGB
    else:
        bg     = load_rarity_bg(icon_type, rarity)
        border = load_rarity_layer(icon_type, "border", rarity)

        canvas = bg.copy()
        canvas.paste(icon_img, (0, 0), icon_img)

        if border:
            canvas.paste(border, (0, 0), border)

        img = canvas.convert("RGB")

    # ── 3. Draw text overlay ──────────────────────────────────────────────────
    style_renderers = {
        CardStyle.STANDARD: _render_standard,
        CardStyle.CLEAN:    _render_clean,
        CardStyle.NEW:      _render_new,
        CardStyle.CATABA:   _render_cataba,
    }
    renderer = style_renderers.get(icon_type, _render_new)
    img = renderer(img, item, font_main, font_side, watermark, show_source, build,
                   watermark_pos)

    # ── 4. Save ───────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)
    img.save(out_path)
