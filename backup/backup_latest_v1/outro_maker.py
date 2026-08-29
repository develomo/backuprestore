import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import ImageClip, CompositeVideoClip

# ==========================================================
# PROFESSIONAL OUTRO MAKER v2.0
# ==========================================================
# WHAT'S NEW vs OLD VERSION:
#
# Old code: Hardcoded 1920x1080 (horizontal only — breaks
#           on vertical Shorts), generic "SUBSCRIBE MY
#           CHANNEL" text, TextClip requires ImageMagick
#           (often broken on Windows), no niche awareness.
#
# New code:
#   - Works for BOTH vertical (Shorts 1080x1920) and
#     horizontal (Long 1280x720) — auto-detects from size
#   - Pure PIL rendering — no ImageMagick dependency
#   - Niche-specific CTA text + colors (reuses the same
#     NICHE_TEXT_CONFIG style as safe_long_video_polished.py)
#   - Two distinct functions:
#       make_long_outro()  → full outro clip for Long videos
#                            (2 seconds, end of video, matches
#                            the intro/outro structure you built)
#       make_shorts_end_cta() → lightweight CTA overlay for
#                            last 3-5 seconds of a Short
#                            (NOT a separate clip — overlays
#                            on existing final clip since
#                            Shorts don't have outro clips)
# ==========================================================

BASE_DIR             = Path(__file__).parent
SETTINGS_DIR         = BASE_DIR / "config"
NICHE_SETTINGS_FILE  = SETTINGS_DIR / "niche_settings.txt"

DEFAULT_NICHE = "quantum_future"

# ==========================================================
# NICHE CTA TEXT — SHORT FORM (for Shorts end overlay)
# Short, punchy commands — appear in last 3-5 seconds
# ==========================================================
NICHE_SHORTS_CTA = {
    "quantum_future":     "Follow for more AI breakthroughs",
    "stoic_wisdom":       "Follow for daily wisdom",
    "luxury_lifestyle":   "Follow for the luxury mindset",
    "mystery":            "Follow — next secret drops soon",
    "interior_design":    "Follow for more design transformations",
    "finance_simulation": "Follow — build wealth the right way",
}

# ==========================================================
# NICHE CTA TEXT — LONG FORM (for Long video outro clip)
# Two lines: command + teaser
# ==========================================================
NICHE_LONG_OUTRO = {
    "quantum_future": {
        "line1": "Follow NOW.",
        "line2": "Next video will change how you see AI forever.",
    },
    "stoic_wisdom": {
        "line1": "Follow for daily wisdom.",
        "line2": "Your mindset shifts start here.",
    },
    "luxury_lifestyle": {
        "line1": "Follow NOW.",
        "line2": "Next video reveals the luxury mindset.",
    },
    "mystery": {
        "line1": "Follow — next secret drops soon.",
        "line2": "You are not ready for what comes next.",
    },
    "interior_design": {
        "line1": "Follow for more design secrets.",
        "line2": "Your dream space is closer than you think.",
    },
    "finance_simulation": {
        "line1": "Follow NOW — money moves fast.",
        "line2": "Next video reveals the wealth formula.",
    },
}

# ==========================================================
# NICHE VISUAL COLORS — matches color_grading.py identity
# ==========================================================
NICHE_VISUAL_CONFIG = {
    "quantum_future":     {"bg": (5, 8, 24),   "text": (0, 220, 255),  "accent": (0, 180, 255)},
    "stoic_wisdom":       {"bg": (18, 14, 8),  "text": (255, 215, 140),"accent": (200, 160, 80)},
    "luxury_lifestyle":   {"bg": (10, 8, 4),   "text": (255, 215, 0),  "accent": (200, 160, 0)},
    "mystery":            {"bg": (8, 4, 18),   "text": (200, 180, 255),"accent": (160, 130, 255)},
    "interior_design":    {"bg": (20, 18, 14), "text": (255, 240, 210),"accent": (220, 200, 160)},
    "finance_simulation": {"bg": (4, 14, 8),   "text": (0, 220, 120),  "accent": (0, 180, 100)},
}


# ==========================================================
# HELPERS
# ==========================================================
def _load_active_niche():
    """Reads niche from config/niche_settings.txt."""
    if NICHE_SETTINGS_FILE.exists():
        key = NICHE_SETTINGS_FILE.read_text(encoding="utf-8").strip()
        if key in NICHE_VISUAL_CONFIG:
            return key
    return DEFAULT_NICHE


def _get_font(size, bold=True):
    """Loads Windows Arial font. No ImageMagick needed."""
    try:
        path = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _text_size(draw, text, font, stroke=0):
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


# ==========================================================
# LONG VIDEO OUTRO
# Full standalone clip — used in safe_long_video_polished.py
# This is functionally identical to build_outro_clip() already
# added there, kept here as a reusable standalone module so
# other scripts can call it without duplicating code.
# ==========================================================
def make_long_outro(niche=None, size=(1280, 720), duration=2.0):
    """
    Builds a niche-aware outro clip for Long videos.

    Design:
    - Background slightly lighter than the niche's base color
    - Line 1: bold CTA command (large font)
    - Line 2: teaser for next video (smaller font)
    - No ImageMagick dependency — pure PIL

    Args:
        niche:    Optional niche override. If None, reads from
                  config/niche_settings.txt
        size:     (W, H) tuple — should match EDIT_W/EDIT_H of
                  the long video pipeline
        duration: float seconds (default 2.0)

    Returns:
        MoviePy ImageClip set to duration

    Usage:
        from outro_maker import make_long_outro
        outro_clip = make_long_outro(niche=active_niche, size=(1280,720))
    """
    active_niche = niche if (niche and niche in NICHE_LONG_OUTRO) else _load_active_niche()

    vis_cfg  = NICHE_VISUAL_CONFIG.get(active_niche, NICHE_VISUAL_CONFIG[DEFAULT_NICHE])
    txt_cfg  = NICHE_LONG_OUTRO.get(active_niche, NICHE_LONG_OUTRO[DEFAULT_NICHE])

    W, H      = size
    bg_color  = tuple(min(255, c + 12) for c in vis_cfg["bg"])
    txt_color = vis_cfg["text"]

    img  = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    font_cta = _get_font(max(40, int(H * 0.086)), bold=True)
    font_sub = _get_font(max(26, int(H * 0.055)), bold=False)

    line1 = txt_cfg["line1"]
    line2 = txt_cfg["line2"]

    try:
        bbox1 = draw.textbbox((0, 0), line1, font=font_cta)
        tw1   = bbox1[2] - bbox1[0]
        x1    = (W - tw1) // 2
        y1    = int(H * 0.32)
        draw.text((x1 + 3, y1 + 3), line1, font=font_cta, fill=(0, 0, 0))
        draw.text((x1, y1), line1, font=font_cta, fill=txt_color)
    except Exception:
        pass

    try:
        bbox2 = draw.textbbox((0, 0), line2, font=font_sub)
        tw2   = bbox2[2] - bbox2[0]
        x2    = (W - tw2) // 2
        y2    = int(H * 0.55)
        draw.text((x2 + 2, y2 + 2), line2, font=font_sub, fill=(0, 0, 0))
        draw.text((x2, y2), line2, font=font_sub, fill=txt_color)
    except Exception:
        pass

    return ImageClip(np.array(img)).set_duration(duration)


# ==========================================================
# SHORTS END CTA OVERLAY
# NOT a separate clip — overlays text on the LAST portion
# of the existing final video. Shorts don't get outro clips
# (per your instruction), only a brief CTA text overlay.
# ==========================================================
def make_shorts_end_cta(video, niche=None, cta_duration=3.5):
    """
    Overlays a niche-aware CTA text on the last few seconds
    of a Shorts video. Does NOT extend video duration —
    text appears over existing final frames.

    Design:
    - Positioned in lower-third, above where captions sit
      (captions are at 72% height, CTA sits at 85% height)
    - Fades in over last cta_duration seconds, fades out
      right at video end
    - Small pill-style background so text stays readable
      over any clip content

    Args:
        video:        MoviePy VideoClip (the fully edited Short)
        niche:        Optional niche override. If None, reads
                      from config/niche_settings.txt
        cta_duration: float seconds before video end to show CTA

    Returns:
        CompositeVideoClip — same duration as input video

    Usage:
        from outro_maker import make_shorts_end_cta
        video = make_shorts_end_cta(video, niche=active_niche)
    """
    active_niche = niche if (niche and niche in NICHE_SHORTS_CTA) else _load_active_niche()

    vis_cfg  = NICHE_VISUAL_CONFIG.get(active_niche, NICHE_VISUAL_CONFIG[DEFAULT_NICHE])
    cta_text = NICHE_SHORTS_CTA.get(active_niche, NICHE_SHORTS_CTA[DEFAULT_NICHE])

    W, H = video.size
    total_dur = float(video.duration)
    cta_dur   = min(cta_duration, total_dur * 0.4)
    start_t   = max(0, total_dur - cta_dur)

    txt_color = vis_cfg["text"]

    font = _get_font(max(28, int(H * 0.026)), bold=True)

    img  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    tw, th = _text_size(draw, cta_text, font, stroke=3)

    pad_x = 28
    pad_y = 14
    y_pos = int(H * 0.85)

    x1 = (W - tw) // 2 - pad_x
    y1 = y_pos - pad_y
    x2 = (W + tw) // 2 + pad_x
    y2 = y_pos + th + pad_y

    try:
        draw.rounded_rectangle((x1, y1, x2, y2), radius=20, fill=(0, 0, 0, 165))
    except Exception:
        draw.rectangle((x1, y1, x2, y2), fill=(0, 0, 0, 165))

    draw.text(
        ((W - tw) // 2, y_pos),
        cta_text,
        font=font,
        fill=(255, 255, 255, 255),
        stroke_width=3,
        stroke_fill=(*txt_color, 255)
    )

    cta_clip = (
        ImageClip(np.array(img))
        .set_start(start_t)
        .set_duration(cta_dur)
    )

    # Simple fade-in for the CTA overlay
    fade_dur = min(0.5, cta_dur * 0.3)
    cta_clip = cta_clip.crossfadein(fade_dur)

    print(
        f"[OutroMaker] Shorts CTA: niche={active_niche} | "
        f"text=\"{cta_text}\" | shown from {start_t:.1f}s",
        flush=True
    )

    composite = CompositeVideoClip([video, cta_clip], size=video.size)
    return composite.set_duration(total_dur)


# ==========================================================
# BACKWARD COMPATIBILITY
# Old code calling make_outro() still works
# ==========================================================
def make_outro(duration=4):
    """
    Kept for backward compatibility.
    Now calls make_long_outro() with auto niche detection
    instead of generic hardcoded "SUBSCRIBE MY CHANNEL" text.
    """
    return make_long_outro(duration=duration)