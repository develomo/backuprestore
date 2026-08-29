import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import ImageClip, CompositeVideoClip

from hooks_engine import generate_hook

# ==========================================================
# PROFESSIONAL HOOK OVERLAY ENGINE v2.0
# ==========================================================
# WHAT'S NEW vs OLD VERSION:
#
# Old code: FFmpeg drawtext subprocess, disconnected from
#           MoviePy pipeline, generic "WAIT!" / "Watch till
#           end" text, no niche awareness, no styling.
#
# New code:
#   - Pure MoviePy/PIL — integrates directly into pipeline,
#     no separate FFmpeg subprocess or temp file needed
#   - Pulls niche-specific hook text from hooks_engine.py
#   - Bold, styled text with glow + shadow (matches caption
#     engine visual quality, not plain white drawtext)
#   - SHORTS: overlays on the hook clip (first 8 seconds),
#     positioned in upper-third (doesn't clash with bottom
#     captions), fades out by 3-4 seconds in
#   - LONG: overlays on the hook clip after intro, larger
#     text, stays longer (matches 8 sec hook duration)
#   - Niche-specific color matches color_grading.py palette
#     so hook text doesn't visually clash with the grade
# ==========================================================

# ==========================================================
# NICHE → HOOK TEXT COLOR
# Matches the niche color identity used in color_grading.py
# and viral_pacing_engine.py for visual consistency
# ==========================================================
NICHE_HOOK_COLOR = {
    "quantum_future":     (0, 220, 255),
    "stoic_wisdom":        (255, 215, 140),
    "luxury_lifestyle":    (255, 215, 0),
    "mystery":             (200, 180, 255),
    "interior_design":     (255, 240, 210),
    "finance_simulation":  (0, 220, 120),
}

DEFAULT_COLOR = (255, 255, 255)

# Hook overlay timing
SHORT_HOOK_FADE_IN  = 0.15
SHORT_HOOK_DISPLAY  = 3.2      # how long text stays fully visible
SHORT_HOOK_FADE_OUT = 0.35

LONG_HOOK_FADE_IN   = 0.3
LONG_HOOK_DISPLAY   = 5.5
LONG_HOOK_FADE_OUT  = 0.6


# ==========================================================
# FONT HELPER
# ==========================================================
def _get_font(size, bold=True):
    """Loads Windows Arial font. Falls back to PIL default."""
    try:
        path = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _text_size(draw, text, font, stroke=0):
    """Returns (width, height) of rendered text."""
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_text(text, max_chars_per_line=24):
    """
    Wraps hook text into 1-2 lines for better readability.
    Long hook sentences need wrapping; short hooks usually fit on 1 line.

    Args:
        text:                full hook string
        max_chars_per_line:  soft character limit per line

    Returns:
        list of line strings (1 or 2 lines)
    """
    if len(text) <= max_chars_per_line:
        return [text]

    words = text.split()
    mid   = len(words) // 2

    # Try to find a natural break point near the middle
    line1 = " ".join(words[:mid])
    line2 = " ".join(words[mid:])

    return [line1, line2]


# ==========================================================
# RENDER HOOK TEXT IMAGE
# ==========================================================
def _render_hook_image(text, video_size, color, font_size, position="upper"):
    """
    Renders styled hook text as a transparent RGBA image.

    Visual style:
    - Bold text with niche color
    - Black stroke outline for readability on any background
    - Soft glow behind text (matches caption_engine aesthetic)
    - Drop shadow for depth

    Args:
        text:        hook text string (already wrapped if needed)
        video_size:  (W, H) tuple
        color:       (R, G, B) tuple for text color
        font_size:   int font size in pixels
        position:    "upper" (Shorts, avoids bottom captions)
                     or "center" (Long videos)

    Returns:
        PIL RGBA Image
    """
    W, H = video_size
    lines = _wrap_text(text)
    font  = _get_font(font_size, bold=True)

    img  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Measure total text block height
    line_heights = []
    line_widths  = []
    for line in lines:
        lw, lh = _text_size(draw, line, font, stroke=5)
        line_widths.append(lw)
        line_heights.append(lh)

    line_gap     = int(max(line_heights) * 0.25)
    total_height = sum(line_heights) + line_gap * (len(lines) - 1)

    if position == "upper":
        start_y = int(H * 0.10)
    else:
        start_y = (H - total_height) // 2

    # Glow layer
    glow_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd       = ImageDraw.Draw(glow_img)

    y_cursor = start_y
    for i, line in enumerate(lines):
        lw = line_widths[i]
        x  = (W - lw) // 2
        gd.text(
            (x, y_cursor),
            line,
            font=font,
            fill=(*color, 160),
            stroke_width=8,
            stroke_fill=(*color, 100)
        )
        y_cursor += line_heights[i] + line_gap

    glow_img = glow_img.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(glow_img)

    # Main text with shadow
    draw = ImageDraw.Draw(img)
    y_cursor = start_y
    for i, line in enumerate(lines):
        lw = line_widths[i]
        x  = (W - lw) // 2

        # Drop shadow
        draw.text(
            (x + 4, y_cursor + 4),
            line,
            font=font,
            fill=(0, 0, 0, 220),
            stroke_width=6,
            stroke_fill=(0, 0, 0, 230)
        )

        # Main text
        draw.text(
            (x, y_cursor),
            line,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=5,
            stroke_fill=(*color, 255)
        )

        y_cursor += line_heights[i] + line_gap

    return img


# ==========================================================
# FADE HELPER
# Applies alpha fade-in/display/fade-out to a clip
# ==========================================================
def _apply_hook_fade(clip, fade_in, display_dur, fade_out):
    """
    Applies fade-in, hold, fade-out alpha envelope to hook text clip.

    Timeline:
    0 → fade_in:                    0% to 100% opacity
    fade_in → fade_in+display:      100% opacity (held)
    fade_in+display → end:          100% to 0% opacity

    Args:
        clip:        ImageClip (hook text)
        fade_in:     float seconds
        display_dur: float seconds to hold at full opacity
        fade_out:    float seconds

    Returns:
        ImageClip with alpha envelope applied
    """
    total_dur = clip.duration

    def make_frame_alpha(get_frame, t):
        frame = get_frame(t)
        alpha = 1.0

        if t < fade_in:
            alpha = t / fade_in
        elif t > (fade_in + display_dur):
            remaining = total_dur - t
            alpha = max(0.0, remaining / fade_out) if fade_out > 0 else 0.0

        alpha = max(0.0, min(1.0, alpha))

        if frame.shape[2] == 4:
            result = frame.copy().astype(np.float32)
            result[:, :, 3] = result[:, :, 3] * alpha
            return result.astype(np.uint8)
        else:
            rgba = np.dstack([frame, np.full(frame.shape[:2], int(255 * alpha), dtype=np.uint8)])
            return rgba

    return clip.fl(make_frame_alpha, apply_to=["mask"])


# ==========================================================
# PUBLIC API
# ==========================================================
def apply_hook(video, niche=None, mode="short", render_count=None):
    """
    Main function. Overlays niche-specific hook text on the
    given video clip (typically the first 8-second hook clip).

    Drop-in usage in pipeline:
        from hook_overlay import apply_hook
        hook_clip = apply_hook(hook_clip, niche=active_niche, mode="short")

    Args:
        video:        MoviePy VideoClip (the hook clip to overlay text on)
        niche:        Optional niche override. If None, reads from
                      config/niche_settings.txt automatically.
        mode:         "short" for Shorts (upper position, punchy text)
                      "long"  for Long videos (center position, full sentence)
        render_count: Optional render index for hook rotation.
                      If None, auto-reads from niche render counter.

    Returns:
        CompositeVideoClip: original video + hook text overlay,
        same duration as input video.
    """
    video_size = video.size
    color      = NICHE_HOOK_COLOR.get(niche, DEFAULT_COLOR) if niche else DEFAULT_COLOR

    # Resolve niche for color lookup if not explicitly passed
    if niche is None:
        from hooks_engine import _load_active_niche
        niche = _load_active_niche()
        color = NICHE_HOOK_COLOR.get(niche, DEFAULT_COLOR)

    # Get hook text from hooks_engine
    hook_text = generate_hook(niche=niche, mode=mode, render_count=render_count)

    if mode == "long":
        font_size   = max(48, int(video_size[1] * 0.045))
        position    = "center"
        fade_in     = LONG_HOOK_FADE_IN
        display_dur = min(LONG_HOOK_DISPLAY, video.duration - LONG_HOOK_FADE_IN - LONG_HOOK_FADE_OUT)
        fade_out    = LONG_HOOK_FADE_OUT
    else:
        font_size   = max(40, int(video_size[1] * 0.038))
        position    = "upper"
        fade_in     = SHORT_HOOK_FADE_IN
        display_dur = min(SHORT_HOOK_DISPLAY, video.duration - SHORT_HOOK_FADE_IN - SHORT_HOOK_FADE_OUT)
        fade_out    = SHORT_HOOK_FADE_OUT

    display_dur = max(0.5, display_dur)

    # Render the hook text image
    hook_img = _render_hook_image(
        hook_text,
        video_size,
        color,
        font_size,
        position=position
    )

    hook_clip = (
        ImageClip(np.array(hook_img))
        .set_duration(video.duration)
        .set_start(0)
    )

    # Apply fade envelope so text doesn't just hard-cut away
    total_visible = fade_in + display_dur + fade_out
    hook_clip = hook_clip.set_duration(min(total_visible, video.duration))
    hook_clip = _apply_hook_fade(hook_clip, fade_in, display_dur, fade_out)

    print(
        f"[HookOverlay] Applied: niche={niche} | mode={mode} | "
        f"text=\"{hook_text}\" | visible={total_visible:.1f}s",
        flush=True
    )

    composite = CompositeVideoClip([video, hook_clip], size=video_size)
    return composite.set_duration(video.duration)