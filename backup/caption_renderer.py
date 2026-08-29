from pathlib import Path
import json
import math
import hashlib
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

try:
    from moviepy.editor import ImageClip, CompositeVideoClip
except Exception:
    ImageClip = None
    CompositeVideoClip = None

try:
    from caption_engine import (
        RenderConfig,
        CaptionToken,
        CaptionSegment,
        normalize_words,
        build_segments,
        render_text_image,
        save_caption_png,
        make_moviepy_caption_clip,
        add_captions_to_video,
        create_caption_clips,
        render_caption_preview,
        group_words_for_phrase_captions,
        caption_engine_report,
        clean_text,
        clean_word,
        find_font_path,
        load_font,
        hex_to_rgb,
        rgba,
        clamp,
    )
    BASE_ENGINE_AVAILABLE = True
except Exception as e:
    print(f"[CaptionRenderer] caption_engine unavailable: {e}", flush=True)
    BASE_ENGINE_AVAILABLE = False

try:
    from caption_style_registry import (
        get_caption_style,
        choose_default_style_for_niche,
        normalize_caption_mode,
        list_style_ids,
        get_preview_cards,
        validate_registry,
    )
    STYLE_REGISTRY_AVAILABLE = True
except Exception:
    STYLE_REGISTRY_AVAILABLE = False
    def normalize_caption_mode(mode):
        return "phrase" if str(mode).lower() in ("phrase", "group", "story", "line") else "word_by_word"
    def choose_default_style_for_niche(niche, mode="word_by_word"):
        return "phrase_crystal_line" if normalize_caption_mode(mode) == "phrase" else "wbw_crystal_cyan"
    def get_caption_style(style_id, fallback_mode="word_by_word"):
        return {"id": style_id or choose_default_style_for_niche("default", fallback_mode), "mode": normalize_caption_mode(fallback_mode), "primary": "#FFFFFF", "stroke_color": "#000000", "stroke_width": 3}
    def list_style_ids(mode=None):
        return []
    def get_preview_cards():
        return []
    def validate_registry():
        return {"ok": True}

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs" / "caption_renderer"
FRAME_DIR = OUTPUT_DIR / "frames"
PNG_DIR = OUTPUT_DIR / "png"
PREVIEW_DIR = OUTPUT_DIR / "preview"
DATA_DIR = OUTPUT_DIR / "data"
for folder in (OUTPUT_DIR, FRAME_DIR, PNG_DIR, PREVIEW_DIR, DATA_DIR):
    folder.mkdir(parents=True, exist_ok=True)


def safe_print(message):
    try:
        print(str(message).replace("→", "->").replace("—", "-"), flush=True)
    except Exception:
        pass


def _hash_payload(payload):
    try:
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    except Exception:
        raw = str(payload)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]


def _safe_tuple_size(size):
    try:
        return int(size[0]), int(size[1])
    except Exception:
        return (1080, 1920)


def _style(style_id=None, mode="word_by_word", niche="default"):
    mode = normalize_caption_mode(mode)
    sid = style_id or choose_default_style_for_niche(niche, mode)
    return get_caption_style(sid, fallback_mode=mode)


def _make_config(size=(1080, 1920), style_id=None, mode="word_by_word", niche="default", **kwargs):
    if BASE_ENGINE_AVAILABLE:
        return RenderConfig(
            size=_safe_tuple_size(size),
            niche=niche,
            caption_mode=normalize_caption_mode(mode),
            style_id=style_id or choose_default_style_for_niche(niche, mode),
            font_path=kwargs.get("font_path"),
            base_font_size=kwargs.get("base_font_size"),
            render_scale=int(kwargs.get("render_scale", 1)),
            cache_enabled=bool(kwargs.get("cache_enabled", True)),
            max_phrase_words=int(kwargs.get("max_phrase_words", 4)),
            min_caption_duration=float(kwargs.get("min_caption_duration", 0.10)),
            max_caption_duration=float(kwargs.get("max_caption_duration", 3.50)),
            word_delay_fix=float(kwargs.get("word_delay_fix", 0.0)),
            end_padding=float(kwargs.get("end_padding", 0.04)),
            y_offset=int(kwargs.get("y_offset", 0)),
            uppercase=bool(kwargs.get("uppercase", True)),
            debug=bool(kwargs.get("debug", False)),
        )
    return {
        "size": _safe_tuple_size(size),
        "niche": niche,
        "mode": normalize_caption_mode(mode),
        "style_id": style_id or choose_default_style_for_niche(niche, mode),
    }


def renderer_normalize_words(words):
    if BASE_ENGINE_AVAILABLE:
        return normalize_words(words)
    out = []
    if isinstance(words, dict):
        words = words.get("words", [])
    for i, item in enumerate(words or []):
        if isinstance(item, dict):
            w = str(item.get("word", item.get("text", ""))).strip()
            s = float(item.get("start", i * 0.35) or 0)
            e = float(item.get("end", s + 0.30) or (s + 0.30))
        else:
            w = str(item).strip()
            s = i * 0.35
            e = s + 0.30
        if w:
            out.append({"word": w, "start": s, "end": max(e, s + 0.05)})
    return out


def renderer_build_segments(words, size=(1080, 1920), style_id=None, mode="word_by_word", niche="default", **kwargs):
    if BASE_ENGINE_AVAILABLE:
        config = _make_config(size=size, style_id=style_id, mode=mode, niche=niche, **kwargs)
        return build_segments(words, config)
    tokens = renderer_normalize_words(words)
    mode = normalize_caption_mode(mode)
    segs = []
    if mode == "phrase":
        chunk = []
        for item in tokens:
            chunk.append(item)
            if len(chunk) >= int(kwargs.get("max_phrase_words", 4)):
                segs.append({"text": " ".join(x["word"] for x in chunk), "start": chunk[0]["start"], "end": chunk[-1]["end"], "words": chunk})
                chunk = []
        if chunk:
            segs.append({"text": " ".join(x["word"] for x in chunk), "start": chunk[0]["start"], "end": chunk[-1]["end"], "words": chunk})
    else:
        for item in tokens:
            segs.append({"text": item["word"], "start": item["start"], "end": item["end"], "words": [item]})
    return segs


def render_segment_png(segment, size=(1080, 1920), style_id=None, mode="word_by_word", niche="default", output_path=None, **kwargs):
    if not BASE_ENGINE_AVAILABLE:
        img = Image.new("RGBA", _safe_tuple_size(size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        text = segment.get("text", "") if isinstance(segment, dict) else str(segment)
        try:
            font = ImageFont.truetype(find_font_path(), int(size[1] * 0.055))
        except Exception:
            font = ImageFont.load_default()
        draw.text((80, int(size[1] * 0.75)), text, fill=(255, 255, 255, 255), font=font, stroke_width=3, stroke_fill=(0, 0, 0, 255))
        path = Path(output_path or PNG_DIR / f"{_hash_payload({'text': text, 'size': size})}.png")
        img.save(path)
        return str(path)
    config = _make_config(size=size, style_id=style_id, mode=mode, niche=niche, cache_enabled=False, **kwargs)
    style = get_caption_style(config.style_id, fallback_mode=config.caption_mode)
    img = render_text_image(segment, style, config)
    path = Path(output_path or PNG_DIR / f"{_hash_payload({'text': segment.text, 'style': config.style_id, 'size': size})}.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return str(path)


def render_segments_to_pngs(words, size=(1080, 1920), style_id=None, mode="word_by_word", niche="default", output_dir=None, **kwargs):
    output_dir = Path(output_dir or PNG_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    segments = renderer_build_segments(words, size=size, style_id=style_id, mode=mode, niche=niche, **kwargs)
    paths = []
    for i, seg in enumerate(segments):
        sid = style_id or choose_default_style_for_niche(niche, mode)
        path = output_dir / f"caption_{i:05d}_{_hash_payload(str(seg))}.png"
        paths.append(render_segment_png(seg, size=size, style_id=sid, mode=mode, niche=niche, output_path=path, **kwargs))
    return paths


def create_caption_image_clips(words, size=(1080, 1920), style_id=None, mode="word_by_word", niche="default", **kwargs):
    if BASE_ENGINE_AVAILABLE:
        return create_caption_clips(words, size=size, style_id=style_id, mode=mode, niche=niche, **kwargs)
    if ImageClip is None:
        return []
    segments = renderer_build_segments(words, size=size, style_id=style_id, mode=mode, niche=niche, **kwargs)
    clips = []
    for i, seg in enumerate(segments):
        png = render_segment_png(seg, size=size, style_id=style_id, mode=mode, niche=niche, **kwargs)
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start + 0.3))
        clips.append(ImageClip(png, transparent=True).set_start(start).set_duration(max(0.05, end - start)))
    return clips


def composite_captions(video, words, size=None, style_id=None, mode="word_by_word", niche="default", **kwargs):
    if BASE_ENGINE_AVAILABLE:
        return add_captions_to_video(video, words, style_id=style_id, mode=mode, niche=niche, **kwargs)
    if video is None or CompositeVideoClip is None:
        return video
    if size is None:
        try:
            size = tuple(video.size)
        except Exception:
            size = (1080, 1920)
    clips = create_caption_image_clips(words, size=size, style_id=style_id, mode=mode, niche=niche, **kwargs)
    if not clips:
        return video
    try:
        return CompositeVideoClip([video] + clips, size=size).set_duration(video.duration)
    except Exception:
        return video


def render_preview_grid(style_ids=None, mode=None, size=(1080, 1920), columns=3, output_path=None):
    if style_ids is None:
        style_ids = list_style_ids(mode)
    if not style_ids:
        style_ids = [choose_default_style_for_niche("default", mode or "word_by_word")]
    thumbs = []
    for sid in style_ids:
        try:
            path = render_caption_preview(sid, mode=mode or get_caption_style(sid).get("mode", "word_by_word"), size=size) if BASE_ENGINE_AVAILABLE else render_segment_png({"text": sid, "start": 0, "end": 1}, size=size, style_id=sid, mode=mode or "word_by_word")
            img = Image.open(path).convert("RGBA").resize((size[0] // 3, size[1] // 3), Image.Resampling.LANCZOS)
            bg = Image.new("RGBA", img.size, (20, 20, 25, 255))
            bg.alpha_composite(img)
            thumbs.append((sid, bg))
        except Exception as e:
            safe_print(f"[CaptionRenderer] preview failed {sid}: {e}")
    if not thumbs:
        return None
    columns = max(1, int(columns))
    tw, th = thumbs[0][1].size
    rows = math.ceil(len(thumbs) / columns)
    grid = Image.new("RGB", (tw * columns, th * rows), (15, 15, 18))
    for i, (sid, img) in enumerate(thumbs):
        x = (i % columns) * tw
        y = (i // columns) * th
        grid.paste(img.convert("RGB"), (x, y))
    path = Path(output_path or PREVIEW_DIR / f"caption_grid_{_hash_payload(style_ids)}.jpg")
    path.parent.mkdir(parents=True, exist_ok=True)
    grid.save(path, quality=92)
    return str(path)


def export_caption_manifest(words, output_path=None, size=(1080, 1920), style_id=None, mode="word_by_word", niche="default", **kwargs):
    segments = renderer_build_segments(words, size=size, style_id=style_id, mode=mode, niche=niche, **kwargs)
    data = []
    for i, seg in enumerate(segments):
        if BASE_ENGINE_AVAILABLE and hasattr(seg, "__dict__"):
            data.append({
                "index": seg.index,
                "text": seg.text,
                "start": seg.start,
                "end": seg.end,
                "duration": round(seg.end - seg.start, 3),
                "mode": seg.mode,
                "style_id": seg.style_id,
                "words": [w.__dict__ for w in seg.words],
            })
        else:
            data.append({
                "index": i,
                "text": seg.get("text", ""),
                "start": seg.get("start", 0.0),
                "end": seg.get("end", 0.0),
                "duration": round(seg.get("end", 0.0) - seg.get("start", 0.0), 3),
                "mode": normalize_caption_mode(mode),
                "style_id": style_id or choose_default_style_for_niche(niche, mode),
                "words": seg.get("words", []),
            })
    path = Path(output_path or DATA_DIR / f"caption_manifest_{_hash_payload(data)}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def render_caption_burn_in_frames(words, frame_count=10, size=(1080, 1920), style_id=None, mode="word_by_word", niche="default", output_dir=None, **kwargs):
    output_dir = Path(output_dir or FRAME_DIR / f"burnin_{_hash_payload({'style': style_id, 'mode': mode, 'niche': niche})}")
    output_dir.mkdir(parents=True, exist_ok=True)
    segments = renderer_build_segments(words, size=size, style_id=style_id, mode=mode, niche=niche, **kwargs)
    if not segments:
        return []
    total_end = max(float(getattr(s, "end", s.get("end", 0.0) if isinstance(s, dict) else 0.0)) for s in segments)
    frames = []
    for i in range(max(1, int(frame_count))):
        t = total_end * (i / max(1, frame_count - 1))
        canvas = Image.new("RGBA", _safe_tuple_size(size), (0, 0, 0, 255))
        active = None
        for seg in segments:
            s = float(getattr(seg, "start", seg.get("start", 0.0) if isinstance(seg, dict) else 0.0))
            e = float(getattr(seg, "end", seg.get("end", 0.0) if isinstance(seg, dict) else 0.0))
            if s <= t <= e:
                active = seg
                break
        if active is not None:
            png = render_segment_png(active, size=size, style_id=style_id, mode=mode, niche=niche, **kwargs)
            cap = Image.open(png).convert("RGBA")
            canvas.alpha_composite(cap)
        path = output_dir / f"frame_{i:04d}.png"
        canvas.save(path)
        frames.append(str(path))
    return frames


def renderer_report():
    return {
        "base_engine_available": BASE_ENGINE_AVAILABLE,
        "style_registry_available": STYLE_REGISTRY_AVAILABLE,
        "output_dir": str(OUTPUT_DIR),
        "png_dir": str(PNG_DIR),
        "preview_dir": str(PREVIEW_DIR),
        "data_dir": str(DATA_DIR),
        "registry": validate_registry(),
        "base_report": caption_engine_report() if BASE_ENGINE_AVAILABLE else None,
        "word_style_count": len(list_style_ids("word_by_word")),
        "phrase_style_count": len(list_style_ids("phrase")),
    }


def clear_renderer_outputs(kind="png"):
    targets = {
        "png": PNG_DIR,
        "frames": FRAME_DIR,
        "preview": PREVIEW_DIR,
        "data": DATA_DIR,
    }
    folder = targets.get(kind, PNG_DIR)
    count = 0
    for p in folder.rglob("*"):
        if p.is_file():
            try:
                p.unlink()
                count += 1
            except Exception:
                pass
    return count


def render_word_by_word(video, words, style_id=None, niche="default", **kwargs):
    return composite_captions(video, words, style_id=style_id, mode="word_by_word", niche=niche, **kwargs)


def render_phrase_captions(video, words, style_id=None, niche="default", **kwargs):
    return composite_captions(video, words, style_id=style_id, mode="phrase", niche=niche, **kwargs)


def apply_rendered_captions(video, words, style_id=None, mode="word_by_word", niche="default", **kwargs):
    return composite_captions(video, words, style_id=style_id, mode=mode, niche=niche, **kwargs)


def add_rendered_captions(video, words, style_id=None, mode="word_by_word", niche="default", **kwargs):
    return composite_captions(video, words, style_id=style_id, mode=mode, niche=niche, **kwargs)


def caption_renderer_ui_payload(niche="default"):
    return {
        "report": renderer_report(),
        "preview_cards": get_preview_cards(),
        "defaults": {
            "word_by_word": choose_default_style_for_niche(niche, "word_by_word"),
            "phrase": choose_default_style_for_niche(niche, "phrase"),
        },
        "styles": {
            "word_by_word": list_style_ids("word_by_word"),
            "phrase": list_style_ids("phrase"),
        },
    }


class CaptionRenderer:
    def __init__(self, size=(1080, 1920), niche="default", mode="word_by_word", style_id=None, **kwargs):
        self.size = _safe_tuple_size(size)
        self.niche = niche
        self.mode = normalize_caption_mode(mode)
        self.style_id = style_id or choose_default_style_for_niche(niche, self.mode)
        self.kwargs = dict(kwargs)

    def segments(self, words):
        return renderer_build_segments(words, size=self.size, style_id=self.style_id, mode=self.mode, niche=self.niche, **self.kwargs)

    def pngs(self, words, output_dir=None):
        return render_segments_to_pngs(words, size=self.size, style_id=self.style_id, mode=self.mode, niche=self.niche, output_dir=output_dir, **self.kwargs)

    def clips(self, words):
        return create_caption_image_clips(words, size=self.size, style_id=self.style_id, mode=self.mode, niche=self.niche, **self.kwargs)

    def apply(self, video, words):
        return composite_captions(video, words, size=self.size, style_id=self.style_id, mode=self.mode, niche=self.niche, **self.kwargs)

    def manifest(self, words, output_path=None):
        return export_caption_manifest(words, output_path=output_path, size=self.size, style_id=self.style_id, mode=self.mode, niche=self.niche, **self.kwargs)

    def preview(self, text=None):
        return render_caption_preview(self.style_id, mode=self.mode, size=self.size, text=text) if BASE_ENGINE_AVAILABLE else render_segment_png({"text": text or "PREVIEW", "start": 0, "end": 1}, size=self.size, style_id=self.style_id, mode=self.mode, niche=self.niche)

    def frame_samples(self, words, frame_count=10, output_dir=None):
        return render_caption_burn_in_frames(words, frame_count=frame_count, size=self.size, style_id=self.style_id, mode=self.mode, niche=self.niche, output_dir=output_dir, **self.kwargs)


def legacy_caption_renderer(video, words, style="default"):
    style_id = None if style == "default" else style
    return composite_captions(video, words, style_id=style_id, mode="word_by_word", niche="default")


if __name__ == "__main__":
    print(json.dumps(renderer_report(), indent=2))

def _renderer_payload_tool_1(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_2(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_3(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_4(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_5(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_6(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_7(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_8(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_9(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_10(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_11(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_12(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_13(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_14(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_15(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_16(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_17(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_18(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_19(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_20(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_21(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_22(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_23(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_24(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_25(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_26(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_27(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_28(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_29(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_30(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_31(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_32(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_33(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_34(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_35(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_36(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_37(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_38(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_39(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_40(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_41(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_42(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_43(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_44(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_45(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_46(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_47(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_48(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_49(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_50(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_51(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_52(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_53(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_54(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_55(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_56(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_57(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_58(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_59(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_60(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_61(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_62(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_63(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_64(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_65(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_66(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_67(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_68(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_69(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_70(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_71(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_72(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_73(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_74(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_75(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_76(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_77(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_78(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_79(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_80(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_81(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_82(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_83(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_84(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_85(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_86(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_87(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_88(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_89(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_90(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_91(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_92(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_93(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_94(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_95(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_96(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_97(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_98(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_99(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_100(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_101(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_102(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_103(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_104(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_105(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_106(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_107(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_108(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_109(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_110(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_111(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_112(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_113(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_114(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_115(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_116(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_117(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_118(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_119(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_120(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_121(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_122(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_123(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_124(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_125(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_126(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_127(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_128(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_129(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_130(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_131(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_132(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_133(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_134(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_135(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_136(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_137(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_138(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_139(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_140(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_141(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_142(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_143(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_144(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_145(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_146(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_147(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_148(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_149(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_150(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_151(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_152(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_153(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_154(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_155(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_156(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_157(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_158(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_159(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_160(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_161(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_162(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_163(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_164(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_165(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_166(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_167(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_168(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_169(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_170(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_171(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_172(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_173(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_174(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_175(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_176(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_177(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_178(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_179(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_180(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_181(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_182(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_183(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_184(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_185(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_186(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_187(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_188(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_189(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_190(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_191(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_192(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_193(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_194(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_195(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_196(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_197(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_198(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_199(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_200(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_201(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_202(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_203(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_204(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_205(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_206(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_207(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_208(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_209(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_210(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_211(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_212(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_213(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_214(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_215(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_216(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_217(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_218(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_219(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_220(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_221(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_222(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_223(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_224(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_225(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_226(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_227(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_228(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_229(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload


def _renderer_payload_tool_230(payload=None, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    return payload
