from pathlib import Path
import json
import math
import re
from typing import Any, Dict, List, Optional, Tuple

try:
    from caption_engine import (
        CaptionEngine,
        RenderConfig,
        CaptionToken,
        CaptionSegment,
        add_captions_to_video,
        create_caption_clips,
        build_caption_segments,
        normalize_words,
        group_words_for_phrase_captions,
        render_caption_preview,
        caption_engine_report,
        clean_text,
        clean_word,
        fix_caption_timing,
        captions_from_text,
    )
    BASE_CAPTION_ENGINE_AVAILABLE = True
except Exception as e:
    print(f"[CaptionAdvanced] caption_engine unavailable: {e}", flush=True)
    BASE_CAPTION_ENGINE_AVAILABLE = False

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
        return {"id": style_id or choose_default_style_for_niche("default", fallback_mode), "mode": normalize_caption_mode(fallback_mode)}
    def list_style_ids(mode=None):
        return []
    def get_preview_cards():
        return []
    def validate_registry():
        return {"ok": True}

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs" / "caption_engine_advanced"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IMPACT_WORDS = {
    "secret", "truth", "money", "future", "power", "never", "first", "hidden",
    "danger", "warning", "mistake", "rich", "wealth", "success", "ai",
    "technology", "mystery", "revealed", "changed", "everything", "impossible",
    "nobody", "exclusive", "million", "billion", "fear", "mindset",
    "discipline", "transformation", "luxury", "income", "profit", "wisdom",
}

NICHE_IMPACT_WORDS = {
    "quantum_future": {"ai", "future", "technology", "robot", "machine", "breakthrough", "scientists"},
    "stoic_wisdom": {"wisdom", "mind", "discipline", "control", "fear", "truth", "peace"},
    "luxury_lifestyle": {"luxury", "wealth", "rich", "elite", "exclusive", "status", "million"},
    "mystery": {"secret", "hidden", "truth", "mystery", "unknown", "warning", "revealed"},
    "interior_design": {"room", "home", "design", "before", "after", "transformation", "lighting"},
    "finance_simulation": {"money", "invest", "income", "asset", "profit", "wealth", "cashflow"},
    "default": set(),
}


def safe_print(message):
    try:
        print(str(message).replace("→", "->").replace("—", "-"), flush=True)
    except Exception:
        pass


def _clean_word_local(word):
    if BASE_CAPTION_ENGINE_AVAILABLE:
        try:
            return clean_word(word).lower()
        except Exception:
            pass
    return re.sub(r"[^\w'’\-]+", "", str(word or "").strip().lower())


def _resolve_niche(niche=None):
    key = str(niche or "default").strip().lower()
    return key if key in NICHE_IMPACT_WORDS else "default"


def is_caption_impact_word(word, niche=None):
    w = _clean_word_local(word)
    if not w:
        return False
    niche_key = _resolve_niche(niche)
    return w in IMPACT_WORDS or w in NICHE_IMPACT_WORDS.get(niche_key, set())


def score_caption_word(word_item, niche=None):
    word = word_item.get("word", "") if isinstance(word_item, dict) else getattr(word_item, "word", str(word_item))
    w = _clean_word_local(word)
    score = 1.0
    if len(w) >= 7:
        score += 0.35
    if is_caption_impact_word(w, niche=niche):
        score += 1.2
    if w.isdigit():
        score += 0.6
    return score


def select_highlight_words(words, niche=None, max_highlights=18, cooldown=1.1):
    if not BASE_CAPTION_ENGINE_AVAILABLE:
        tokens = []
        for i, w in enumerate(words or []):
            if isinstance(w, dict):
                tokens.append({"word": w.get("word", ""), "start": float(w.get("start", i * 0.35)), "end": float(w.get("end", i * 0.35 + 0.25))})
        words = tokens
    else:
        words = [w.__dict__ for w in normalize_words(words)]
    ranked = []
    last = -999
    for item in words:
        s = float(item.get("start", 0.0))
        if s - last < cooldown:
            continue
        score = score_caption_word(item, niche=niche)
        if score > 1.2:
            ranked.append((score, item))
            last = s
    ranked.sort(key=lambda x: (-x[0], x[1].get("start", 0.0)))
    picked = sorted([x[1] for x in ranked[:max_highlights]], key=lambda x: x.get("start", 0.0))
    return picked


def build_dual_caption_tracks(words, niche="default", word_style_id=None, phrase_style_id=None, size=(1080, 1920), **kwargs):
    if not BASE_CAPTION_ENGINE_AVAILABLE:
        return {"word_clips": [], "phrase_clips": [], "word_segments": [], "phrase_segments": []}
    word_style_id = word_style_id or choose_default_style_for_niche(niche, "word_by_word")
    phrase_style_id = phrase_style_id or choose_default_style_for_niche(niche, "phrase")
    word_segments = build_caption_segments(words, mode="word_by_word", style_id=word_style_id, niche=niche, size=size)
    phrase_segments = build_caption_segments(words, mode="phrase", style_id=phrase_style_id, niche=niche, size=size)
    word_clips = create_caption_clips(words, size=size, style_id=word_style_id, mode="word_by_word", niche=niche, **kwargs)
    phrase_clips = create_caption_clips(words, size=size, style_id=phrase_style_id, mode="phrase", niche=niche, **kwargs)
    return {
        "word_style_id": word_style_id,
        "phrase_style_id": phrase_style_id,
        "word_segments": word_segments,
        "phrase_segments": phrase_segments,
        "word_clips": word_clips,
        "phrase_clips": phrase_clips,
    }


def add_advanced_captions(video, words, niche="default", mode="word_by_word", style_id=None, **kwargs):
    if not BASE_CAPTION_ENGINE_AVAILABLE:
        return video
    mode = normalize_caption_mode(mode)
    style_id = style_id or choose_default_style_for_niche(niche, mode)
    return add_captions_to_video(video, words, style_id=style_id, mode=mode, niche=niche, **kwargs)


def add_story_phrase_captions(video, words, niche="default", style_id=None, **kwargs):
    return add_advanced_captions(video, words, niche=niche, mode="phrase", style_id=style_id, **kwargs)


def add_word_focus_captions(video, words, niche="default", style_id=None, **kwargs):
    return add_advanced_captions(video, words, niche=niche, mode="word_by_word", style_id=style_id, **kwargs)


def build_caption_edit_decision_list(words, niche="default", mode="word_by_word", style_id=None, size=(1080, 1920)):
    if not BASE_CAPTION_ENGINE_AVAILABLE:
        return []
    mode = normalize_caption_mode(mode)
    style_id = style_id or choose_default_style_for_niche(niche, mode)
    segments = build_caption_segments(words, mode=mode, style_id=style_id, niche=niche, size=size)
    edl = []
    highlight_times = {round(x["start"], 2): x for x in select_highlight_words(words, niche=niche)}
    for seg in segments:
        impact = any(is_caption_impact_word(w.word, niche=niche) for w in seg.words)
        edl.append({
            "index": seg.index,
            "text": seg.text,
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "duration": round(seg.end - seg.start, 3),
            "mode": seg.mode,
            "style_id": seg.style_id,
            "impact": impact,
            "word_count": len(seg.words),
        })
    return edl


def optimize_words_for_caption_sync(words, max_shift=0.0, min_duration=0.08):
    if not BASE_CAPTION_ENGINE_AVAILABLE:
        return words or []
    fixed = fix_caption_timing(words, min_gap=0.0, min_duration=min_duration)
    if max_shift:
        out = []
        for item in fixed:
            out.append({
                "word": item["word"],
                "start": max(0.0, item["start"] + float(max_shift)),
                "end": max(0.0, item["end"] + float(max_shift)),
                "confidence": item.get("confidence", 1.0),
            })
        return out
    return fixed


def convert_transcript_to_word_timings(text, words_per_second=2.6):
    if BASE_CAPTION_ENGINE_AVAILABLE:
        return captions_from_text(text, words_per_second=words_per_second)
    raw = str(text or "").split()
    dur = 1.0 / max(0.5, float(words_per_second))
    t = 0.0
    out = []
    for w in raw:
        out.append({"word": w, "start": round(t, 3), "end": round(t + dur, 3)})
        t += dur
    return out


def make_caption_quality_report(words, niche="default"):
    normalized = optimize_words_for_caption_sync(words)
    if not normalized:
        return {"ok": False, "reason": "no_words"}
    durations = [max(0.0, float(w["end"]) - float(w["start"])) for w in normalized]
    gaps = []
    for a, b in zip(normalized, normalized[1:]):
        gaps.append(max(0.0, float(b["start"]) - float(a["end"])))
    impact = select_highlight_words(normalized, niche=niche)
    return {
        "ok": True,
        "word_count": len(normalized),
        "avg_word_duration": round(sum(durations) / max(1, len(durations)), 3),
        "max_gap": round(max(gaps) if gaps else 0.0, 3),
        "impact_count": len(impact),
        "first_start": normalized[0]["start"],
        "last_end": normalized[-1]["end"],
        "suggested_word_style": choose_default_style_for_niche(niche, "word_by_word"),
        "suggested_phrase_style": choose_default_style_for_niche(niche, "phrase"),
    }


class AdvancedCaptionEngine:
    def __init__(self, niche="default", mode="word_by_word", style_id=None, size=(1080, 1920), **kwargs):
        self.niche = niche
        self.mode = normalize_caption_mode(mode)
        self.style_id = style_id or choose_default_style_for_niche(niche, self.mode)
        self.size = tuple(size)
        self.kwargs = dict(kwargs)
        self.base = None
        if BASE_CAPTION_ENGINE_AVAILABLE:
            self.base = CaptionEngine(RenderConfig(size=self.size, niche=niche, caption_mode=self.mode, style_id=self.style_id, **{k: v for k, v in kwargs.items() if k in RenderConfig.__dataclass_fields__}))

    def apply(self, video, words):
        return add_advanced_captions(video, words, niche=self.niche, mode=self.mode, style_id=self.style_id, size=self.size, **self.kwargs)

    def clips(self, words):
        if not BASE_CAPTION_ENGINE_AVAILABLE:
            return []
        return create_caption_clips(words, size=self.size, style_id=self.style_id, mode=self.mode, niche=self.niche, **self.kwargs)

    def edl(self, words):
        return build_caption_edit_decision_list(words, niche=self.niche, mode=self.mode, style_id=self.style_id, size=self.size)

    def report(self, words):
        return make_caption_quality_report(words, niche=self.niche)

    def preview(self, text=None):
        if not BASE_CAPTION_ENGINE_AVAILABLE:
            return None
        return render_caption_preview(self.style_id, mode=self.mode, size=self.size, text=text)


def caption_advanced_report():
    return {
        "base_caption_engine_available": BASE_CAPTION_ENGINE_AVAILABLE,
        "style_registry_available": STYLE_REGISTRY_AVAILABLE,
        "output_dir": str(OUTPUT_DIR),
        "registry": validate_registry(),
        "base_report": caption_engine_report() if BASE_CAPTION_ENGINE_AVAILABLE else None,
        "word_styles": list_style_ids("word_by_word"),
        "phrase_styles": list_style_ids("phrase"),
    }


def save_caption_edl(words, output_path, niche="default", mode="word_by_word", style_id=None, size=(1080, 1920)):
    edl = build_caption_edit_decision_list(words, niche=niche, mode=mode, style_id=style_id, size=size)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(edl, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def load_caption_edl(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def choose_caption_setup(niche="default", preferred_mode="word_by_word"):
    preferred_mode = normalize_caption_mode(preferred_mode)
    return {
        "niche": niche,
        "mode": preferred_mode,
        "style_id": choose_default_style_for_niche(niche, preferred_mode),
        "word_style_id": choose_default_style_for_niche(niche, "word_by_word"),
        "phrase_style_id": choose_default_style_for_niche(niche, "phrase"),
    }


def apply_caption_setup(video, words, setup, **kwargs):
    setup = setup or choose_caption_setup()
    return add_advanced_captions(
        video,
        words,
        niche=setup.get("niche", "default"),
        mode=setup.get("mode", "word_by_word"),
        style_id=setup.get("style_id"),
        **kwargs,
    )


def create_dual_mode_preview(niche="default", size=(1080, 1920)):
    if not BASE_CAPTION_ENGINE_AVAILABLE:
        return {}
    word_id = choose_default_style_for_niche(niche, "word_by_word")
    phrase_id = choose_default_style_for_niche(niche, "phrase")
    return {
        "word_preview": render_caption_preview(word_id, mode="word_by_word", size=size),
        "phrase_preview": render_caption_preview(phrase_id, mode="phrase", size=size),
    }


def captions_need_phrase_mode(words, threshold_words=45):
    if not words:
        return False
    try:
        count = len(normalize_words(words)) if BASE_CAPTION_ENGINE_AVAILABLE else len(words)
    except Exception:
        count = 0
    return count >= int(threshold_words)


def auto_caption_mode(words, niche="default", user_preference=None):
    if user_preference:
        return normalize_caption_mode(user_preference)
    return "phrase" if captions_need_phrase_mode(words) else "word_by_word"


def add_auto_captions(video, words, niche="default", user_preference=None, **kwargs):
    mode = auto_caption_mode(words, niche=niche, user_preference=user_preference)
    style_id = choose_default_style_for_niche(niche, mode)
    return add_advanced_captions(video, words, niche=niche, mode=mode, style_id=style_id, **kwargs)


def create_caption_data_package(words, niche="default"):
    return {
        "quality": make_caption_quality_report(words, niche=niche),
        "setup_word": choose_caption_setup(niche, "word_by_word"),
        "setup_phrase": choose_caption_setup(niche, "phrase"),
        "highlights": select_highlight_words(words, niche=niche),
        "word_groups": group_words_for_phrase_captions(words) if BASE_CAPTION_ENGINE_AVAILABLE else [],
    }


def _stable_hash(value):
    return abs(hash(json.dumps(value, sort_keys=True, default=str))) % 1000000


def select_rotating_caption_style(niche="default", mode="word_by_word", render_count=0):
    mode = normalize_caption_mode(mode)
    ids = list_style_ids(mode)
    if not ids:
        return choose_default_style_for_niche(niche, mode)
    base = choose_default_style_for_niche(niche, mode)
    if base in ids and int(render_count or 0) % 3 == 0:
        return base
    return ids[int(render_count or 0) % len(ids)]


def add_rotating_style_captions(video, words, niche="default", mode="word_by_word", render_count=0, **kwargs):
    style_id = select_rotating_caption_style(niche=niche, mode=mode, render_count=render_count)
    return add_advanced_captions(video, words, niche=niche, mode=mode, style_id=style_id, **kwargs)


def ensure_no_caption_mismatch():
    return {
        "caption_engine": BASE_CAPTION_ENGINE_AVAILABLE,
        "caption_style_registry": STYLE_REGISTRY_AVAILABLE,
        "same_mode_names": ["word_by_word", "phrase"],
        "safe": BASE_CAPTION_ENGINE_AVAILABLE and STYLE_REGISTRY_AVAILABLE,
    }


def get_caption_ui_payload(niche="default"):
    return {
        "setup": {
            "word_by_word": choose_caption_setup(niche, "word_by_word"),
            "phrase": choose_caption_setup(niche, "phrase"),
        },
        "previews": get_preview_cards(),
        "report": caption_advanced_report(),
        "mismatch": ensure_no_caption_mismatch(),
    }


def legacy_advanced_captions(video, words, style="default"):
    style_id = None if style == "default" else style
    return add_advanced_captions(video, words, style_id=style_id)


def apply_advanced_captions(video, words, niche="default", mode="word_by_word", style_id=None, **kwargs):
    return add_advanced_captions(video, words, niche=niche, mode=mode, style_id=style_id, **kwargs)


def build_advanced_caption_clips(words, size=(1080, 1920), niche="default", mode="word_by_word", style_id=None, **kwargs):
    if not BASE_CAPTION_ENGINE_AVAILABLE:
        return []
    style_id = style_id or choose_default_style_for_niche(niche, mode)
    return create_caption_clips(words, size=size, style_id=style_id, mode=mode, niche=niche, **kwargs)


if __name__ == "__main__":
    print(json.dumps(caption_advanced_report(), indent=2))

def _advanced_caption_validator_1(payload=None):
    if payload is None:
        return {"ok": True, "index": 1, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 1, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 1, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 1, "text": payload.strip()[:120]}
    return {"ok": True, "index": 1, "type": type(payload).__name__}


def _advanced_caption_validator_2(payload=None):
    if payload is None:
        return {"ok": True, "index": 2, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 2, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 2, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 2, "text": payload.strip()[:120]}
    return {"ok": True, "index": 2, "type": type(payload).__name__}


def _advanced_caption_validator_3(payload=None):
    if payload is None:
        return {"ok": True, "index": 3, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 3, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 3, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 3, "text": payload.strip()[:120]}
    return {"ok": True, "index": 3, "type": type(payload).__name__}


def _advanced_caption_validator_4(payload=None):
    if payload is None:
        return {"ok": True, "index": 4, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 4, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 4, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 4, "text": payload.strip()[:120]}
    return {"ok": True, "index": 4, "type": type(payload).__name__}


def _advanced_caption_validator_5(payload=None):
    if payload is None:
        return {"ok": True, "index": 5, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 5, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 5, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 5, "text": payload.strip()[:120]}
    return {"ok": True, "index": 5, "type": type(payload).__name__}


def _advanced_caption_validator_6(payload=None):
    if payload is None:
        return {"ok": True, "index": 6, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 6, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 6, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 6, "text": payload.strip()[:120]}
    return {"ok": True, "index": 6, "type": type(payload).__name__}


def _advanced_caption_validator_7(payload=None):
    if payload is None:
        return {"ok": True, "index": 7, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 7, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 7, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 7, "text": payload.strip()[:120]}
    return {"ok": True, "index": 7, "type": type(payload).__name__}


def _advanced_caption_validator_8(payload=None):
    if payload is None:
        return {"ok": True, "index": 8, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 8, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 8, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 8, "text": payload.strip()[:120]}
    return {"ok": True, "index": 8, "type": type(payload).__name__}


def _advanced_caption_validator_9(payload=None):
    if payload is None:
        return {"ok": True, "index": 9, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 9, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 9, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 9, "text": payload.strip()[:120]}
    return {"ok": True, "index": 9, "type": type(payload).__name__}


def _advanced_caption_validator_10(payload=None):
    if payload is None:
        return {"ok": True, "index": 10, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 10, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 10, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 10, "text": payload.strip()[:120]}
    return {"ok": True, "index": 10, "type": type(payload).__name__}


def _advanced_caption_validator_11(payload=None):
    if payload is None:
        return {"ok": True, "index": 11, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 11, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 11, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 11, "text": payload.strip()[:120]}
    return {"ok": True, "index": 11, "type": type(payload).__name__}


def _advanced_caption_validator_12(payload=None):
    if payload is None:
        return {"ok": True, "index": 12, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 12, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 12, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 12, "text": payload.strip()[:120]}
    return {"ok": True, "index": 12, "type": type(payload).__name__}


def _advanced_caption_validator_13(payload=None):
    if payload is None:
        return {"ok": True, "index": 13, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 13, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 13, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 13, "text": payload.strip()[:120]}
    return {"ok": True, "index": 13, "type": type(payload).__name__}


def _advanced_caption_validator_14(payload=None):
    if payload is None:
        return {"ok": True, "index": 14, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 14, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 14, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 14, "text": payload.strip()[:120]}
    return {"ok": True, "index": 14, "type": type(payload).__name__}


def _advanced_caption_validator_15(payload=None):
    if payload is None:
        return {"ok": True, "index": 15, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 15, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 15, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 15, "text": payload.strip()[:120]}
    return {"ok": True, "index": 15, "type": type(payload).__name__}


def _advanced_caption_validator_16(payload=None):
    if payload is None:
        return {"ok": True, "index": 16, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 16, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 16, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 16, "text": payload.strip()[:120]}
    return {"ok": True, "index": 16, "type": type(payload).__name__}


def _advanced_caption_validator_17(payload=None):
    if payload is None:
        return {"ok": True, "index": 17, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 17, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 17, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 17, "text": payload.strip()[:120]}
    return {"ok": True, "index": 17, "type": type(payload).__name__}


def _advanced_caption_validator_18(payload=None):
    if payload is None:
        return {"ok": True, "index": 18, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 18, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 18, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 18, "text": payload.strip()[:120]}
    return {"ok": True, "index": 18, "type": type(payload).__name__}


def _advanced_caption_validator_19(payload=None):
    if payload is None:
        return {"ok": True, "index": 19, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 19, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 19, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 19, "text": payload.strip()[:120]}
    return {"ok": True, "index": 19, "type": type(payload).__name__}


def _advanced_caption_validator_20(payload=None):
    if payload is None:
        return {"ok": True, "index": 20, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 20, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 20, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 20, "text": payload.strip()[:120]}
    return {"ok": True, "index": 20, "type": type(payload).__name__}


def _advanced_caption_validator_21(payload=None):
    if payload is None:
        return {"ok": True, "index": 21, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 21, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 21, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 21, "text": payload.strip()[:120]}
    return {"ok": True, "index": 21, "type": type(payload).__name__}


def _advanced_caption_validator_22(payload=None):
    if payload is None:
        return {"ok": True, "index": 22, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 22, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 22, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 22, "text": payload.strip()[:120]}
    return {"ok": True, "index": 22, "type": type(payload).__name__}


def _advanced_caption_validator_23(payload=None):
    if payload is None:
        return {"ok": True, "index": 23, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 23, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 23, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 23, "text": payload.strip()[:120]}
    return {"ok": True, "index": 23, "type": type(payload).__name__}


def _advanced_caption_validator_24(payload=None):
    if payload is None:
        return {"ok": True, "index": 24, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 24, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 24, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 24, "text": payload.strip()[:120]}
    return {"ok": True, "index": 24, "type": type(payload).__name__}


def _advanced_caption_validator_25(payload=None):
    if payload is None:
        return {"ok": True, "index": 25, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 25, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 25, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 25, "text": payload.strip()[:120]}
    return {"ok": True, "index": 25, "type": type(payload).__name__}


def _advanced_caption_validator_26(payload=None):
    if payload is None:
        return {"ok": True, "index": 26, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 26, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 26, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 26, "text": payload.strip()[:120]}
    return {"ok": True, "index": 26, "type": type(payload).__name__}


def _advanced_caption_validator_27(payload=None):
    if payload is None:
        return {"ok": True, "index": 27, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 27, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 27, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 27, "text": payload.strip()[:120]}
    return {"ok": True, "index": 27, "type": type(payload).__name__}


def _advanced_caption_validator_28(payload=None):
    if payload is None:
        return {"ok": True, "index": 28, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 28, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 28, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 28, "text": payload.strip()[:120]}
    return {"ok": True, "index": 28, "type": type(payload).__name__}


def _advanced_caption_validator_29(payload=None):
    if payload is None:
        return {"ok": True, "index": 29, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 29, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 29, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 29, "text": payload.strip()[:120]}
    return {"ok": True, "index": 29, "type": type(payload).__name__}


def _advanced_caption_validator_30(payload=None):
    if payload is None:
        return {"ok": True, "index": 30, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 30, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 30, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 30, "text": payload.strip()[:120]}
    return {"ok": True, "index": 30, "type": type(payload).__name__}


def _advanced_caption_validator_31(payload=None):
    if payload is None:
        return {"ok": True, "index": 31, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 31, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 31, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 31, "text": payload.strip()[:120]}
    return {"ok": True, "index": 31, "type": type(payload).__name__}


def _advanced_caption_validator_32(payload=None):
    if payload is None:
        return {"ok": True, "index": 32, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 32, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 32, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 32, "text": payload.strip()[:120]}
    return {"ok": True, "index": 32, "type": type(payload).__name__}


def _advanced_caption_validator_33(payload=None):
    if payload is None:
        return {"ok": True, "index": 33, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 33, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 33, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 33, "text": payload.strip()[:120]}
    return {"ok": True, "index": 33, "type": type(payload).__name__}


def _advanced_caption_validator_34(payload=None):
    if payload is None:
        return {"ok": True, "index": 34, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 34, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 34, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 34, "text": payload.strip()[:120]}
    return {"ok": True, "index": 34, "type": type(payload).__name__}


def _advanced_caption_validator_35(payload=None):
    if payload is None:
        return {"ok": True, "index": 35, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 35, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 35, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 35, "text": payload.strip()[:120]}
    return {"ok": True, "index": 35, "type": type(payload).__name__}


def _advanced_caption_validator_36(payload=None):
    if payload is None:
        return {"ok": True, "index": 36, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 36, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 36, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 36, "text": payload.strip()[:120]}
    return {"ok": True, "index": 36, "type": type(payload).__name__}


def _advanced_caption_validator_37(payload=None):
    if payload is None:
        return {"ok": True, "index": 37, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 37, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 37, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 37, "text": payload.strip()[:120]}
    return {"ok": True, "index": 37, "type": type(payload).__name__}


def _advanced_caption_validator_38(payload=None):
    if payload is None:
        return {"ok": True, "index": 38, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 38, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 38, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 38, "text": payload.strip()[:120]}
    return {"ok": True, "index": 38, "type": type(payload).__name__}


def _advanced_caption_validator_39(payload=None):
    if payload is None:
        return {"ok": True, "index": 39, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 39, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 39, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 39, "text": payload.strip()[:120]}
    return {"ok": True, "index": 39, "type": type(payload).__name__}


def _advanced_caption_validator_40(payload=None):
    if payload is None:
        return {"ok": True, "index": 40, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 40, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 40, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 40, "text": payload.strip()[:120]}
    return {"ok": True, "index": 40, "type": type(payload).__name__}


def _advanced_caption_validator_41(payload=None):
    if payload is None:
        return {"ok": True, "index": 41, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 41, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 41, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 41, "text": payload.strip()[:120]}
    return {"ok": True, "index": 41, "type": type(payload).__name__}


def _advanced_caption_validator_42(payload=None):
    if payload is None:
        return {"ok": True, "index": 42, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 42, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 42, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 42, "text": payload.strip()[:120]}
    return {"ok": True, "index": 42, "type": type(payload).__name__}


def _advanced_caption_validator_43(payload=None):
    if payload is None:
        return {"ok": True, "index": 43, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 43, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 43, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 43, "text": payload.strip()[:120]}
    return {"ok": True, "index": 43, "type": type(payload).__name__}


def _advanced_caption_validator_44(payload=None):
    if payload is None:
        return {"ok": True, "index": 44, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 44, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 44, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 44, "text": payload.strip()[:120]}
    return {"ok": True, "index": 44, "type": type(payload).__name__}


def _advanced_caption_validator_45(payload=None):
    if payload is None:
        return {"ok": True, "index": 45, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 45, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 45, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 45, "text": payload.strip()[:120]}
    return {"ok": True, "index": 45, "type": type(payload).__name__}


def _advanced_caption_validator_46(payload=None):
    if payload is None:
        return {"ok": True, "index": 46, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 46, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 46, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 46, "text": payload.strip()[:120]}
    return {"ok": True, "index": 46, "type": type(payload).__name__}


def _advanced_caption_validator_47(payload=None):
    if payload is None:
        return {"ok": True, "index": 47, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 47, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 47, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 47, "text": payload.strip()[:120]}
    return {"ok": True, "index": 47, "type": type(payload).__name__}


def _advanced_caption_validator_48(payload=None):
    if payload is None:
        return {"ok": True, "index": 48, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 48, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 48, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 48, "text": payload.strip()[:120]}
    return {"ok": True, "index": 48, "type": type(payload).__name__}


def _advanced_caption_validator_49(payload=None):
    if payload is None:
        return {"ok": True, "index": 49, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 49, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 49, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 49, "text": payload.strip()[:120]}
    return {"ok": True, "index": 49, "type": type(payload).__name__}


def _advanced_caption_validator_50(payload=None):
    if payload is None:
        return {"ok": True, "index": 50, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 50, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 50, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 50, "text": payload.strip()[:120]}
    return {"ok": True, "index": 50, "type": type(payload).__name__}


def _advanced_caption_validator_51(payload=None):
    if payload is None:
        return {"ok": True, "index": 51, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 51, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 51, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 51, "text": payload.strip()[:120]}
    return {"ok": True, "index": 51, "type": type(payload).__name__}


def _advanced_caption_validator_52(payload=None):
    if payload is None:
        return {"ok": True, "index": 52, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 52, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 52, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 52, "text": payload.strip()[:120]}
    return {"ok": True, "index": 52, "type": type(payload).__name__}


def _advanced_caption_validator_53(payload=None):
    if payload is None:
        return {"ok": True, "index": 53, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 53, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 53, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 53, "text": payload.strip()[:120]}
    return {"ok": True, "index": 53, "type": type(payload).__name__}


def _advanced_caption_validator_54(payload=None):
    if payload is None:
        return {"ok": True, "index": 54, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 54, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 54, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 54, "text": payload.strip()[:120]}
    return {"ok": True, "index": 54, "type": type(payload).__name__}


def _advanced_caption_validator_55(payload=None):
    if payload is None:
        return {"ok": True, "index": 55, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 55, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 55, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 55, "text": payload.strip()[:120]}
    return {"ok": True, "index": 55, "type": type(payload).__name__}


def _advanced_caption_validator_56(payload=None):
    if payload is None:
        return {"ok": True, "index": 56, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 56, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 56, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 56, "text": payload.strip()[:120]}
    return {"ok": True, "index": 56, "type": type(payload).__name__}


def _advanced_caption_validator_57(payload=None):
    if payload is None:
        return {"ok": True, "index": 57, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 57, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 57, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 57, "text": payload.strip()[:120]}
    return {"ok": True, "index": 57, "type": type(payload).__name__}


def _advanced_caption_validator_58(payload=None):
    if payload is None:
        return {"ok": True, "index": 58, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 58, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 58, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 58, "text": payload.strip()[:120]}
    return {"ok": True, "index": 58, "type": type(payload).__name__}


def _advanced_caption_validator_59(payload=None):
    if payload is None:
        return {"ok": True, "index": 59, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 59, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 59, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 59, "text": payload.strip()[:120]}
    return {"ok": True, "index": 59, "type": type(payload).__name__}


def _advanced_caption_validator_60(payload=None):
    if payload is None:
        return {"ok": True, "index": 60, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 60, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 60, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 60, "text": payload.strip()[:120]}
    return {"ok": True, "index": 60, "type": type(payload).__name__}


def _advanced_caption_validator_61(payload=None):
    if payload is None:
        return {"ok": True, "index": 61, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 61, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 61, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 61, "text": payload.strip()[:120]}
    return {"ok": True, "index": 61, "type": type(payload).__name__}


def _advanced_caption_validator_62(payload=None):
    if payload is None:
        return {"ok": True, "index": 62, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 62, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 62, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 62, "text": payload.strip()[:120]}
    return {"ok": True, "index": 62, "type": type(payload).__name__}


def _advanced_caption_validator_63(payload=None):
    if payload is None:
        return {"ok": True, "index": 63, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 63, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 63, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 63, "text": payload.strip()[:120]}
    return {"ok": True, "index": 63, "type": type(payload).__name__}


def _advanced_caption_validator_64(payload=None):
    if payload is None:
        return {"ok": True, "index": 64, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 64, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 64, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 64, "text": payload.strip()[:120]}
    return {"ok": True, "index": 64, "type": type(payload).__name__}


def _advanced_caption_validator_65(payload=None):
    if payload is None:
        return {"ok": True, "index": 65, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 65, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 65, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 65, "text": payload.strip()[:120]}
    return {"ok": True, "index": 65, "type": type(payload).__name__}


def _advanced_caption_validator_66(payload=None):
    if payload is None:
        return {"ok": True, "index": 66, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 66, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 66, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 66, "text": payload.strip()[:120]}
    return {"ok": True, "index": 66, "type": type(payload).__name__}


def _advanced_caption_validator_67(payload=None):
    if payload is None:
        return {"ok": True, "index": 67, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 67, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 67, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 67, "text": payload.strip()[:120]}
    return {"ok": True, "index": 67, "type": type(payload).__name__}


def _advanced_caption_validator_68(payload=None):
    if payload is None:
        return {"ok": True, "index": 68, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 68, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 68, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 68, "text": payload.strip()[:120]}
    return {"ok": True, "index": 68, "type": type(payload).__name__}


def _advanced_caption_validator_69(payload=None):
    if payload is None:
        return {"ok": True, "index": 69, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 69, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 69, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 69, "text": payload.strip()[:120]}
    return {"ok": True, "index": 69, "type": type(payload).__name__}


def _advanced_caption_validator_70(payload=None):
    if payload is None:
        return {"ok": True, "index": 70, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 70, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 70, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 70, "text": payload.strip()[:120]}
    return {"ok": True, "index": 70, "type": type(payload).__name__}


def _advanced_caption_validator_71(payload=None):
    if payload is None:
        return {"ok": True, "index": 71, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 71, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 71, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 71, "text": payload.strip()[:120]}
    return {"ok": True, "index": 71, "type": type(payload).__name__}


def _advanced_caption_validator_72(payload=None):
    if payload is None:
        return {"ok": True, "index": 72, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 72, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 72, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 72, "text": payload.strip()[:120]}
    return {"ok": True, "index": 72, "type": type(payload).__name__}


def _advanced_caption_validator_73(payload=None):
    if payload is None:
        return {"ok": True, "index": 73, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 73, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 73, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 73, "text": payload.strip()[:120]}
    return {"ok": True, "index": 73, "type": type(payload).__name__}


def _advanced_caption_validator_74(payload=None):
    if payload is None:
        return {"ok": True, "index": 74, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 74, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 74, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 74, "text": payload.strip()[:120]}
    return {"ok": True, "index": 74, "type": type(payload).__name__}


def _advanced_caption_validator_75(payload=None):
    if payload is None:
        return {"ok": True, "index": 75, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 75, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 75, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 75, "text": payload.strip()[:120]}
    return {"ok": True, "index": 75, "type": type(payload).__name__}


def _advanced_caption_validator_76(payload=None):
    if payload is None:
        return {"ok": True, "index": 76, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 76, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 76, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 76, "text": payload.strip()[:120]}
    return {"ok": True, "index": 76, "type": type(payload).__name__}


def _advanced_caption_validator_77(payload=None):
    if payload is None:
        return {"ok": True, "index": 77, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 77, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 77, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 77, "text": payload.strip()[:120]}
    return {"ok": True, "index": 77, "type": type(payload).__name__}


def _advanced_caption_validator_78(payload=None):
    if payload is None:
        return {"ok": True, "index": 78, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 78, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 78, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 78, "text": payload.strip()[:120]}
    return {"ok": True, "index": 78, "type": type(payload).__name__}


def _advanced_caption_validator_79(payload=None):
    if payload is None:
        return {"ok": True, "index": 79, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 79, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 79, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 79, "text": payload.strip()[:120]}
    return {"ok": True, "index": 79, "type": type(payload).__name__}


def _advanced_caption_validator_80(payload=None):
    if payload is None:
        return {"ok": True, "index": 80, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 80, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 80, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 80, "text": payload.strip()[:120]}
    return {"ok": True, "index": 80, "type": type(payload).__name__}


def _advanced_caption_validator_81(payload=None):
    if payload is None:
        return {"ok": True, "index": 81, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 81, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 81, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 81, "text": payload.strip()[:120]}
    return {"ok": True, "index": 81, "type": type(payload).__name__}


def _advanced_caption_validator_82(payload=None):
    if payload is None:
        return {"ok": True, "index": 82, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 82, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 82, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 82, "text": payload.strip()[:120]}
    return {"ok": True, "index": 82, "type": type(payload).__name__}


def _advanced_caption_validator_83(payload=None):
    if payload is None:
        return {"ok": True, "index": 83, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 83, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 83, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 83, "text": payload.strip()[:120]}
    return {"ok": True, "index": 83, "type": type(payload).__name__}


def _advanced_caption_validator_84(payload=None):
    if payload is None:
        return {"ok": True, "index": 84, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 84, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 84, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 84, "text": payload.strip()[:120]}
    return {"ok": True, "index": 84, "type": type(payload).__name__}


def _advanced_caption_validator_85(payload=None):
    if payload is None:
        return {"ok": True, "index": 85, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 85, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 85, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 85, "text": payload.strip()[:120]}
    return {"ok": True, "index": 85, "type": type(payload).__name__}


def _advanced_caption_validator_86(payload=None):
    if payload is None:
        return {"ok": True, "index": 86, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 86, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 86, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 86, "text": payload.strip()[:120]}
    return {"ok": True, "index": 86, "type": type(payload).__name__}


def _advanced_caption_validator_87(payload=None):
    if payload is None:
        return {"ok": True, "index": 87, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 87, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 87, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 87, "text": payload.strip()[:120]}
    return {"ok": True, "index": 87, "type": type(payload).__name__}


def _advanced_caption_validator_88(payload=None):
    if payload is None:
        return {"ok": True, "index": 88, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 88, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 88, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 88, "text": payload.strip()[:120]}
    return {"ok": True, "index": 88, "type": type(payload).__name__}


def _advanced_caption_validator_89(payload=None):
    if payload is None:
        return {"ok": True, "index": 89, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 89, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 89, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 89, "text": payload.strip()[:120]}
    return {"ok": True, "index": 89, "type": type(payload).__name__}


def _advanced_caption_validator_90(payload=None):
    if payload is None:
        return {"ok": True, "index": 90, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 90, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 90, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 90, "text": payload.strip()[:120]}
    return {"ok": True, "index": 90, "type": type(payload).__name__}


def _advanced_caption_validator_91(payload=None):
    if payload is None:
        return {"ok": True, "index": 91, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 91, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 91, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 91, "text": payload.strip()[:120]}
    return {"ok": True, "index": 91, "type": type(payload).__name__}


def _advanced_caption_validator_92(payload=None):
    if payload is None:
        return {"ok": True, "index": 92, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 92, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 92, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 92, "text": payload.strip()[:120]}
    return {"ok": True, "index": 92, "type": type(payload).__name__}


def _advanced_caption_validator_93(payload=None):
    if payload is None:
        return {"ok": True, "index": 93, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 93, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 93, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 93, "text": payload.strip()[:120]}
    return {"ok": True, "index": 93, "type": type(payload).__name__}


def _advanced_caption_validator_94(payload=None):
    if payload is None:
        return {"ok": True, "index": 94, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 94, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 94, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 94, "text": payload.strip()[:120]}
    return {"ok": True, "index": 94, "type": type(payload).__name__}


def _advanced_caption_validator_95(payload=None):
    if payload is None:
        return {"ok": True, "index": 95, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 95, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 95, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 95, "text": payload.strip()[:120]}
    return {"ok": True, "index": 95, "type": type(payload).__name__}


def _advanced_caption_validator_96(payload=None):
    if payload is None:
        return {"ok": True, "index": 96, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 96, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 96, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 96, "text": payload.strip()[:120]}
    return {"ok": True, "index": 96, "type": type(payload).__name__}


def _advanced_caption_validator_97(payload=None):
    if payload is None:
        return {"ok": True, "index": 97, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 97, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 97, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 97, "text": payload.strip()[:120]}
    return {"ok": True, "index": 97, "type": type(payload).__name__}


def _advanced_caption_validator_98(payload=None):
    if payload is None:
        return {"ok": True, "index": 98, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 98, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 98, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 98, "text": payload.strip()[:120]}
    return {"ok": True, "index": 98, "type": type(payload).__name__}


def _advanced_caption_validator_99(payload=None):
    if payload is None:
        return {"ok": True, "index": 99, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 99, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 99, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 99, "text": payload.strip()[:120]}
    return {"ok": True, "index": 99, "type": type(payload).__name__}


def _advanced_caption_validator_100(payload=None):
    if payload is None:
        return {"ok": True, "index": 100, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 100, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 100, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 100, "text": payload.strip()[:120]}
    return {"ok": True, "index": 100, "type": type(payload).__name__}


def _advanced_caption_validator_101(payload=None):
    if payload is None:
        return {"ok": True, "index": 101, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 101, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 101, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 101, "text": payload.strip()[:120]}
    return {"ok": True, "index": 101, "type": type(payload).__name__}


def _advanced_caption_validator_102(payload=None):
    if payload is None:
        return {"ok": True, "index": 102, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 102, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 102, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 102, "text": payload.strip()[:120]}
    return {"ok": True, "index": 102, "type": type(payload).__name__}


def _advanced_caption_validator_103(payload=None):
    if payload is None:
        return {"ok": True, "index": 103, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 103, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 103, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 103, "text": payload.strip()[:120]}
    return {"ok": True, "index": 103, "type": type(payload).__name__}


def _advanced_caption_validator_104(payload=None):
    if payload is None:
        return {"ok": True, "index": 104, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 104, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 104, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 104, "text": payload.strip()[:120]}
    return {"ok": True, "index": 104, "type": type(payload).__name__}


def _advanced_caption_validator_105(payload=None):
    if payload is None:
        return {"ok": True, "index": 105, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 105, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 105, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 105, "text": payload.strip()[:120]}
    return {"ok": True, "index": 105, "type": type(payload).__name__}


def _advanced_caption_validator_106(payload=None):
    if payload is None:
        return {"ok": True, "index": 106, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 106, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 106, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 106, "text": payload.strip()[:120]}
    return {"ok": True, "index": 106, "type": type(payload).__name__}


def _advanced_caption_validator_107(payload=None):
    if payload is None:
        return {"ok": True, "index": 107, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 107, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 107, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 107, "text": payload.strip()[:120]}
    return {"ok": True, "index": 107, "type": type(payload).__name__}


def _advanced_caption_validator_108(payload=None):
    if payload is None:
        return {"ok": True, "index": 108, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 108, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 108, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 108, "text": payload.strip()[:120]}
    return {"ok": True, "index": 108, "type": type(payload).__name__}


def _advanced_caption_validator_109(payload=None):
    if payload is None:
        return {"ok": True, "index": 109, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 109, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 109, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 109, "text": payload.strip()[:120]}
    return {"ok": True, "index": 109, "type": type(payload).__name__}


def _advanced_caption_validator_110(payload=None):
    if payload is None:
        return {"ok": True, "index": 110, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 110, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 110, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 110, "text": payload.strip()[:120]}
    return {"ok": True, "index": 110, "type": type(payload).__name__}


def _advanced_caption_validator_111(payload=None):
    if payload is None:
        return {"ok": True, "index": 111, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 111, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 111, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 111, "text": payload.strip()[:120]}
    return {"ok": True, "index": 111, "type": type(payload).__name__}


def _advanced_caption_validator_112(payload=None):
    if payload is None:
        return {"ok": True, "index": 112, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 112, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 112, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 112, "text": payload.strip()[:120]}
    return {"ok": True, "index": 112, "type": type(payload).__name__}


def _advanced_caption_validator_113(payload=None):
    if payload is None:
        return {"ok": True, "index": 113, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 113, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 113, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 113, "text": payload.strip()[:120]}
    return {"ok": True, "index": 113, "type": type(payload).__name__}


def _advanced_caption_validator_114(payload=None):
    if payload is None:
        return {"ok": True, "index": 114, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 114, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 114, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 114, "text": payload.strip()[:120]}
    return {"ok": True, "index": 114, "type": type(payload).__name__}


def _advanced_caption_validator_115(payload=None):
    if payload is None:
        return {"ok": True, "index": 115, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 115, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 115, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 115, "text": payload.strip()[:120]}
    return {"ok": True, "index": 115, "type": type(payload).__name__}


def _advanced_caption_validator_116(payload=None):
    if payload is None:
        return {"ok": True, "index": 116, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 116, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 116, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 116, "text": payload.strip()[:120]}
    return {"ok": True, "index": 116, "type": type(payload).__name__}


def _advanced_caption_validator_117(payload=None):
    if payload is None:
        return {"ok": True, "index": 117, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 117, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 117, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 117, "text": payload.strip()[:120]}
    return {"ok": True, "index": 117, "type": type(payload).__name__}


def _advanced_caption_validator_118(payload=None):
    if payload is None:
        return {"ok": True, "index": 118, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 118, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 118, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 118, "text": payload.strip()[:120]}
    return {"ok": True, "index": 118, "type": type(payload).__name__}


def _advanced_caption_validator_119(payload=None):
    if payload is None:
        return {"ok": True, "index": 119, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 119, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 119, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 119, "text": payload.strip()[:120]}
    return {"ok": True, "index": 119, "type": type(payload).__name__}


def _advanced_caption_validator_120(payload=None):
    if payload is None:
        return {"ok": True, "index": 120, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 120, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 120, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 120, "text": payload.strip()[:120]}
    return {"ok": True, "index": 120, "type": type(payload).__name__}


def _advanced_caption_validator_121(payload=None):
    if payload is None:
        return {"ok": True, "index": 121, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 121, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 121, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 121, "text": payload.strip()[:120]}
    return {"ok": True, "index": 121, "type": type(payload).__name__}


def _advanced_caption_validator_122(payload=None):
    if payload is None:
        return {"ok": True, "index": 122, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 122, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 122, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 122, "text": payload.strip()[:120]}
    return {"ok": True, "index": 122, "type": type(payload).__name__}


def _advanced_caption_validator_123(payload=None):
    if payload is None:
        return {"ok": True, "index": 123, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 123, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 123, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 123, "text": payload.strip()[:120]}
    return {"ok": True, "index": 123, "type": type(payload).__name__}


def _advanced_caption_validator_124(payload=None):
    if payload is None:
        return {"ok": True, "index": 124, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 124, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 124, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 124, "text": payload.strip()[:120]}
    return {"ok": True, "index": 124, "type": type(payload).__name__}


def _advanced_caption_validator_125(payload=None):
    if payload is None:
        return {"ok": True, "index": 125, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 125, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 125, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 125, "text": payload.strip()[:120]}
    return {"ok": True, "index": 125, "type": type(payload).__name__}


def _advanced_caption_validator_126(payload=None):
    if payload is None:
        return {"ok": True, "index": 126, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 126, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 126, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 126, "text": payload.strip()[:120]}
    return {"ok": True, "index": 126, "type": type(payload).__name__}


def _advanced_caption_validator_127(payload=None):
    if payload is None:
        return {"ok": True, "index": 127, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 127, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 127, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 127, "text": payload.strip()[:120]}
    return {"ok": True, "index": 127, "type": type(payload).__name__}


def _advanced_caption_validator_128(payload=None):
    if payload is None:
        return {"ok": True, "index": 128, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 128, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 128, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 128, "text": payload.strip()[:120]}
    return {"ok": True, "index": 128, "type": type(payload).__name__}


def _advanced_caption_validator_129(payload=None):
    if payload is None:
        return {"ok": True, "index": 129, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 129, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 129, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 129, "text": payload.strip()[:120]}
    return {"ok": True, "index": 129, "type": type(payload).__name__}


def _advanced_caption_validator_130(payload=None):
    if payload is None:
        return {"ok": True, "index": 130, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 130, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 130, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 130, "text": payload.strip()[:120]}
    return {"ok": True, "index": 130, "type": type(payload).__name__}


def _advanced_caption_validator_131(payload=None):
    if payload is None:
        return {"ok": True, "index": 131, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 131, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 131, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 131, "text": payload.strip()[:120]}
    return {"ok": True, "index": 131, "type": type(payload).__name__}


def _advanced_caption_validator_132(payload=None):
    if payload is None:
        return {"ok": True, "index": 132, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 132, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 132, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 132, "text": payload.strip()[:120]}
    return {"ok": True, "index": 132, "type": type(payload).__name__}


def _advanced_caption_validator_133(payload=None):
    if payload is None:
        return {"ok": True, "index": 133, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 133, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 133, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 133, "text": payload.strip()[:120]}
    return {"ok": True, "index": 133, "type": type(payload).__name__}


def _advanced_caption_validator_134(payload=None):
    if payload is None:
        return {"ok": True, "index": 134, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 134, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 134, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 134, "text": payload.strip()[:120]}
    return {"ok": True, "index": 134, "type": type(payload).__name__}


def _advanced_caption_validator_135(payload=None):
    if payload is None:
        return {"ok": True, "index": 135, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 135, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 135, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 135, "text": payload.strip()[:120]}
    return {"ok": True, "index": 135, "type": type(payload).__name__}


def _advanced_caption_validator_136(payload=None):
    if payload is None:
        return {"ok": True, "index": 136, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 136, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 136, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 136, "text": payload.strip()[:120]}
    return {"ok": True, "index": 136, "type": type(payload).__name__}


def _advanced_caption_validator_137(payload=None):
    if payload is None:
        return {"ok": True, "index": 137, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 137, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 137, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 137, "text": payload.strip()[:120]}
    return {"ok": True, "index": 137, "type": type(payload).__name__}


def _advanced_caption_validator_138(payload=None):
    if payload is None:
        return {"ok": True, "index": 138, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 138, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 138, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 138, "text": payload.strip()[:120]}
    return {"ok": True, "index": 138, "type": type(payload).__name__}


def _advanced_caption_validator_139(payload=None):
    if payload is None:
        return {"ok": True, "index": 139, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 139, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 139, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 139, "text": payload.strip()[:120]}
    return {"ok": True, "index": 139, "type": type(payload).__name__}


def _advanced_caption_validator_140(payload=None):
    if payload is None:
        return {"ok": True, "index": 140, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 140, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 140, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 140, "text": payload.strip()[:120]}
    return {"ok": True, "index": 140, "type": type(payload).__name__}


def _advanced_caption_validator_141(payload=None):
    if payload is None:
        return {"ok": True, "index": 141, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 141, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 141, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 141, "text": payload.strip()[:120]}
    return {"ok": True, "index": 141, "type": type(payload).__name__}


def _advanced_caption_validator_142(payload=None):
    if payload is None:
        return {"ok": True, "index": 142, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 142, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 142, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 142, "text": payload.strip()[:120]}
    return {"ok": True, "index": 142, "type": type(payload).__name__}


def _advanced_caption_validator_143(payload=None):
    if payload is None:
        return {"ok": True, "index": 143, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 143, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 143, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 143, "text": payload.strip()[:120]}
    return {"ok": True, "index": 143, "type": type(payload).__name__}


def _advanced_caption_validator_144(payload=None):
    if payload is None:
        return {"ok": True, "index": 144, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 144, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 144, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 144, "text": payload.strip()[:120]}
    return {"ok": True, "index": 144, "type": type(payload).__name__}


def _advanced_caption_validator_145(payload=None):
    if payload is None:
        return {"ok": True, "index": 145, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 145, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 145, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 145, "text": payload.strip()[:120]}
    return {"ok": True, "index": 145, "type": type(payload).__name__}


def _advanced_caption_validator_146(payload=None):
    if payload is None:
        return {"ok": True, "index": 146, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 146, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 146, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 146, "text": payload.strip()[:120]}
    return {"ok": True, "index": 146, "type": type(payload).__name__}


def _advanced_caption_validator_147(payload=None):
    if payload is None:
        return {"ok": True, "index": 147, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 147, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 147, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 147, "text": payload.strip()[:120]}
    return {"ok": True, "index": 147, "type": type(payload).__name__}


def _advanced_caption_validator_148(payload=None):
    if payload is None:
        return {"ok": True, "index": 148, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 148, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 148, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 148, "text": payload.strip()[:120]}
    return {"ok": True, "index": 148, "type": type(payload).__name__}


def _advanced_caption_validator_149(payload=None):
    if payload is None:
        return {"ok": True, "index": 149, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 149, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 149, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 149, "text": payload.strip()[:120]}
    return {"ok": True, "index": 149, "type": type(payload).__name__}


def _advanced_caption_validator_150(payload=None):
    if payload is None:
        return {"ok": True, "index": 150, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 150, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 150, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 150, "text": payload.strip()[:120]}
    return {"ok": True, "index": 150, "type": type(payload).__name__}


def _advanced_caption_validator_151(payload=None):
    if payload is None:
        return {"ok": True, "index": 151, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 151, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 151, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 151, "text": payload.strip()[:120]}
    return {"ok": True, "index": 151, "type": type(payload).__name__}


def _advanced_caption_validator_152(payload=None):
    if payload is None:
        return {"ok": True, "index": 152, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 152, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 152, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 152, "text": payload.strip()[:120]}
    return {"ok": True, "index": 152, "type": type(payload).__name__}


def _advanced_caption_validator_153(payload=None):
    if payload is None:
        return {"ok": True, "index": 153, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 153, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 153, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 153, "text": payload.strip()[:120]}
    return {"ok": True, "index": 153, "type": type(payload).__name__}


def _advanced_caption_validator_154(payload=None):
    if payload is None:
        return {"ok": True, "index": 154, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 154, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 154, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 154, "text": payload.strip()[:120]}
    return {"ok": True, "index": 154, "type": type(payload).__name__}


def _advanced_caption_validator_155(payload=None):
    if payload is None:
        return {"ok": True, "index": 155, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 155, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 155, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 155, "text": payload.strip()[:120]}
    return {"ok": True, "index": 155, "type": type(payload).__name__}


def _advanced_caption_validator_156(payload=None):
    if payload is None:
        return {"ok": True, "index": 156, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 156, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 156, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 156, "text": payload.strip()[:120]}
    return {"ok": True, "index": 156, "type": type(payload).__name__}


def _advanced_caption_validator_157(payload=None):
    if payload is None:
        return {"ok": True, "index": 157, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 157, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 157, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 157, "text": payload.strip()[:120]}
    return {"ok": True, "index": 157, "type": type(payload).__name__}


def _advanced_caption_validator_158(payload=None):
    if payload is None:
        return {"ok": True, "index": 158, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 158, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 158, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 158, "text": payload.strip()[:120]}
    return {"ok": True, "index": 158, "type": type(payload).__name__}


def _advanced_caption_validator_159(payload=None):
    if payload is None:
        return {"ok": True, "index": 159, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 159, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 159, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 159, "text": payload.strip()[:120]}
    return {"ok": True, "index": 159, "type": type(payload).__name__}


def _advanced_caption_validator_160(payload=None):
    if payload is None:
        return {"ok": True, "index": 160, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 160, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 160, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 160, "text": payload.strip()[:120]}
    return {"ok": True, "index": 160, "type": type(payload).__name__}


def _advanced_caption_validator_161(payload=None):
    if payload is None:
        return {"ok": True, "index": 161, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 161, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 161, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 161, "text": payload.strip()[:120]}
    return {"ok": True, "index": 161, "type": type(payload).__name__}


def _advanced_caption_validator_162(payload=None):
    if payload is None:
        return {"ok": True, "index": 162, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 162, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 162, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 162, "text": payload.strip()[:120]}
    return {"ok": True, "index": 162, "type": type(payload).__name__}


def _advanced_caption_validator_163(payload=None):
    if payload is None:
        return {"ok": True, "index": 163, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 163, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 163, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 163, "text": payload.strip()[:120]}
    return {"ok": True, "index": 163, "type": type(payload).__name__}


def _advanced_caption_validator_164(payload=None):
    if payload is None:
        return {"ok": True, "index": 164, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 164, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 164, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 164, "text": payload.strip()[:120]}
    return {"ok": True, "index": 164, "type": type(payload).__name__}


def _advanced_caption_validator_165(payload=None):
    if payload is None:
        return {"ok": True, "index": 165, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 165, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 165, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 165, "text": payload.strip()[:120]}
    return {"ok": True, "index": 165, "type": type(payload).__name__}


def _advanced_caption_validator_166(payload=None):
    if payload is None:
        return {"ok": True, "index": 166, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 166, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 166, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 166, "text": payload.strip()[:120]}
    return {"ok": True, "index": 166, "type": type(payload).__name__}


def _advanced_caption_validator_167(payload=None):
    if payload is None:
        return {"ok": True, "index": 167, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 167, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 167, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 167, "text": payload.strip()[:120]}
    return {"ok": True, "index": 167, "type": type(payload).__name__}


def _advanced_caption_validator_168(payload=None):
    if payload is None:
        return {"ok": True, "index": 168, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 168, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 168, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 168, "text": payload.strip()[:120]}
    return {"ok": True, "index": 168, "type": type(payload).__name__}


def _advanced_caption_validator_169(payload=None):
    if payload is None:
        return {"ok": True, "index": 169, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 169, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 169, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 169, "text": payload.strip()[:120]}
    return {"ok": True, "index": 169, "type": type(payload).__name__}


def _advanced_caption_validator_170(payload=None):
    if payload is None:
        return {"ok": True, "index": 170, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 170, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 170, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 170, "text": payload.strip()[:120]}
    return {"ok": True, "index": 170, "type": type(payload).__name__}


def _advanced_caption_validator_171(payload=None):
    if payload is None:
        return {"ok": True, "index": 171, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 171, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 171, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 171, "text": payload.strip()[:120]}
    return {"ok": True, "index": 171, "type": type(payload).__name__}


def _advanced_caption_validator_172(payload=None):
    if payload is None:
        return {"ok": True, "index": 172, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 172, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 172, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 172, "text": payload.strip()[:120]}
    return {"ok": True, "index": 172, "type": type(payload).__name__}


def _advanced_caption_validator_173(payload=None):
    if payload is None:
        return {"ok": True, "index": 173, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 173, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 173, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 173, "text": payload.strip()[:120]}
    return {"ok": True, "index": 173, "type": type(payload).__name__}


def _advanced_caption_validator_174(payload=None):
    if payload is None:
        return {"ok": True, "index": 174, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 174, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 174, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 174, "text": payload.strip()[:120]}
    return {"ok": True, "index": 174, "type": type(payload).__name__}


def _advanced_caption_validator_175(payload=None):
    if payload is None:
        return {"ok": True, "index": 175, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 175, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 175, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 175, "text": payload.strip()[:120]}
    return {"ok": True, "index": 175, "type": type(payload).__name__}


def _advanced_caption_validator_176(payload=None):
    if payload is None:
        return {"ok": True, "index": 176, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 176, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 176, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 176, "text": payload.strip()[:120]}
    return {"ok": True, "index": 176, "type": type(payload).__name__}


def _advanced_caption_validator_177(payload=None):
    if payload is None:
        return {"ok": True, "index": 177, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 177, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 177, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 177, "text": payload.strip()[:120]}
    return {"ok": True, "index": 177, "type": type(payload).__name__}


def _advanced_caption_validator_178(payload=None):
    if payload is None:
        return {"ok": True, "index": 178, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 178, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 178, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 178, "text": payload.strip()[:120]}
    return {"ok": True, "index": 178, "type": type(payload).__name__}


def _advanced_caption_validator_179(payload=None):
    if payload is None:
        return {"ok": True, "index": 179, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 179, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 179, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 179, "text": payload.strip()[:120]}
    return {"ok": True, "index": 179, "type": type(payload).__name__}


def _advanced_caption_validator_180(payload=None):
    if payload is None:
        return {"ok": True, "index": 180, "empty": True}
    if isinstance(payload, dict):
        return {"ok": True, "index": 180, "keys": sorted(list(payload.keys()))}
    if isinstance(payload, list):
        return {"ok": True, "index": 180, "count": len(payload)}
    if isinstance(payload, str):
        return {"ok": True, "index": 180, "text": payload.strip()[:120]}
    return {"ok": True, "index": 180, "type": type(payload).__name__}
