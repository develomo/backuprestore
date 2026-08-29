import json
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from moviepy.editor import CompositeVideoClip, concatenate_videoclips, ColorClip
    from moviepy.video.fx.all import fadein, fadeout
except Exception as e:
    print(f"[TransitionEngine] MoviePy import failed: {e}", flush=True)
    CompositeVideoClip = None
    concatenate_videoclips = None
    ColorClip = None
    fadein = None
    fadeout = None

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs" / "transition_engine"
REPORT_DIR = OUTPUT_DIR / "reports"
for folder in (OUTPUT_DIR, REPORT_DIR):
    folder.mkdir(parents=True, exist_ok=True)

TRANSITION_PROFILES = {
    "quantum_future": {"duration": 0.18, "soft": 0.10, "style": "fast_clean", "energy": 0.78, "allowed": ["cut", "crossfade", "flash", "slide"]},
    "stoic_wisdom": {"duration": 0.38, "soft": 0.22, "style": "calm_fade", "energy": 0.30, "allowed": ["cut", "crossfade", "fade"]},
    "luxury_lifestyle": {"duration": 0.30, "soft": 0.18, "style": "premium_smooth", "energy": 0.52, "allowed": ["cut", "crossfade", "fade", "slide"]},
    "mystery": {"duration": 0.34, "soft": 0.22, "style": "dark_suspense", "energy": 0.62, "allowed": ["cut", "crossfade", "fade", "flash"]},
    "interior_design": {"duration": 0.42, "soft": 0.26, "style": "soft_reveal", "energy": 0.28, "allowed": ["cut", "crossfade", "fade"]},
    "finance_simulation": {"duration": 0.24, "soft": 0.14, "style": "clean_business", "energy": 0.58, "allowed": ["cut", "crossfade", "slide"]},
    "default": {"duration": 0.25, "soft": 0.15, "style": "clean", "energy": 0.45, "allowed": ["cut", "crossfade", "fade"]},
}

TRANSITION_NAMES = ["cut", "crossfade", "fade", "flash", "slide", "premium_crossfade", "soft_fade", "hook_flash", "documentary_cut"]

def safe_print(message):
    try:
        print(str(message).replace("→", "->").replace("—", "-").replace("–", "-"), flush=True)
    except Exception:
        pass

def _mode_key(mode="SHORT"):
    mode = str(mode or "SHORT").upper()
    return "LONG" if mode in ("LONG", "YOUTUBE_LONG", "HORIZONTAL") else "SHORT"

def _resolve_niche(niche=None):
    key = str(niche or "default").strip().lower()
    return key if key in TRANSITION_PROFILES else "default"

def _profile(niche=None, mode="SHORT", render_count=0):
    key = _resolve_niche(niche)
    profile = dict(TRANSITION_PROFILES[key])
    if _mode_key(mode) == "LONG":
        profile["duration"] = min(0.45, max(profile["duration"], profile["soft"]))
    else:
        profile["duration"] = min(0.30, profile["duration"])
    offset = ((int(render_count or 0) % 5) - 2) * 0.015
    profile["duration"] = max(0.06, min(0.60, profile["duration"] + offset))
    profile["niche"] = key
    profile["mode"] = _mode_key(mode)
    return profile

def clip_duration(clip):
    try:
        return max(float(clip.duration), 0.05)
    except Exception:
        return 0.05

def clip_size(clip):
    try:
        return tuple(clip.size)
    except Exception:
        return (1080, 1920)

def choose_transition(niche=None, mode="SHORT", render_count=0, index=0, section="body"):
    profile = _profile(niche=niche, mode=mode, render_count=render_count)
    allowed = list(profile.get("allowed", ["cut", "crossfade"]))
    section = str(section or "body").lower()
    if section == "hook" and _mode_key(mode) == "SHORT":
        allowed = [x for x in allowed + ["hook_flash", "cut"] if x in TRANSITION_NAMES]
    if section in ("ending", "payoff"):
        allowed = [x for x in allowed + ["soft_fade", "premium_crossfade"] if x in TRANSITION_NAMES]
    if _mode_key(mode) == "LONG":
        allowed = [x for x in allowed if x not in ("flash", "hook_flash")] or ["crossfade"]
    rng = random.Random((int(render_count or 0) + 41) * 1009 + int(index or 0) * 151)
    return rng.choice(allowed)

def apply_fade_to_clip(clip, duration=0.20, fade_in_enabled=True, fade_out_enabled=True):
    if clip is None:
        return clip
    out = clip
    d = min(float(duration or 0.0), clip_duration(clip) * 0.30)
    if d <= 0:
        return clip
    try:
        if fade_in_enabled and fadein is not None:
            out = fadein(out, d)
    except Exception:
        pass
    try:
        if fade_out_enabled and fadeout is not None:
            out = fadeout(out, d)
    except Exception:
        pass
    try:
        return out.set_duration(clip_duration(clip))
    except Exception:
        return out

def crossfade_clips(clips, transition_duration=0.20):
    clips = [c for c in clips or [] if c is not None]
    if not clips:
        return None
    if len(clips) == 1:
        return clips[0]
    if concatenate_videoclips is None:
        return clips[0]
    transition_duration = max(0.02, float(transition_duration or 0.20))
    prepared = [clips[0]]
    for c in clips[1:]:
        try:
            prepared.append(c.crossfadein(min(transition_duration, clip_duration(c) * 0.30)))
        except Exception:
            prepared.append(c)
    try:
        return concatenate_videoclips(prepared, method="compose", padding=-transition_duration)
    except Exception:
        try:
            return concatenate_videoclips(clips, method="compose")
        except Exception:
            return clips[0]

def cut_concatenate(clips):
    clips = [c for c in clips or [] if c is not None]
    if not clips:
        return None
    if concatenate_videoclips is None:
        return clips[0]
    try:
        return concatenate_videoclips(clips, method="compose")
    except Exception:
        return concatenate_videoclips(clips)

def add_flash_between_clips(clips, duration=0.08, color=(255, 255, 255)):
    clips = [c for c in clips or [] if c is not None]
    if not clips:
        return None
    if ColorClip is None or concatenate_videoclips is None:
        return cut_concatenate(clips)
    output = []
    for i, clip in enumerate(clips):
        output.append(clip)
        if i < len(clips) - 1:
            size = clip_size(clip)
            flash = ColorClip(size=size, color=color, duration=max(0.02, float(duration)))
            output.append(flash)
    try:
        return concatenate_videoclips(output, method="compose")
    except Exception:
        return cut_concatenate(clips)

def slide_transition_pair(a, b, duration=0.25, direction="left"):
    if a is None:
        return b
    if b is None:
        return a
    if CompositeVideoClip is None or concatenate_videoclips is None:
        return crossfade_clips([a, b], duration)
    duration = min(float(duration or 0.25), clip_duration(a) * 0.35, clip_duration(b) * 0.35)
    if duration <= 0.02:
        return cut_concatenate([a, b])
    size = clip_size(a)
    w, h = size
    a_main = a.subclip(0, max(0.05, clip_duration(a) - duration))
    a_tail = a.subclip(max(0, clip_duration(a) - duration), clip_duration(a))
    b_head = b.subclip(0, duration)
    b_rest = b.subclip(duration, clip_duration(b)) if clip_duration(b) > duration else None
    def pos_a(t):
        p = t / max(duration, 0.01)
        if direction == "right":
            return (int(w * p), 0)
        if direction == "up":
            return (0, int(-h * p))
        if direction == "down":
            return (0, int(h * p))
        return (int(-w * p), 0)
    def pos_b(t):
        p = t / max(duration, 0.01)
        if direction == "right":
            return (int(-w + w * p), 0)
        if direction == "up":
            return (0, int(h - h * p))
        if direction == "down":
            return (0, int(-h + h * p))
        return (int(w - w * p), 0)
    comp = CompositeVideoClip([a_tail.set_position(pos_a), b_head.set_position(pos_b)], size=size).set_duration(duration)
    parts = [a_main, comp]
    if b_rest is not None:
        parts.append(b_rest)
    try:
        return concatenate_videoclips(parts, method="compose")
    except Exception:
        return crossfade_clips([a, b], duration)

def slide_transition_sequence(clips, duration=0.20, direction="left"):
    clips = [c for c in clips or [] if c is not None]
    if not clips:
        return None
    current = clips[0]
    for i in range(1, len(clips)):
        current = slide_transition_pair(current, clips[i], duration=duration, direction=direction)
    return current

def apply_transition_sequence(clips, transition_type="crossfade", duration=0.20, mode="SHORT", niche=None):
    clips = [c for c in clips or [] if c is not None]
    if not clips:
        return None
    transition_type = str(transition_type or "crossfade").lower()
    if transition_type in ("cut", "documentary_cut", "none"):
        return cut_concatenate(clips)
    if transition_type in ("crossfade", "premium_crossfade", "soft_fade", "fade"):
        d = duration * 1.35 if transition_type in ("premium_crossfade", "soft_fade") else duration
        return crossfade_clips(clips, transition_duration=d)
    if transition_type in ("flash", "hook_flash"):
        return add_flash_between_clips(clips, duration=min(0.12, duration * 0.55), color=(255, 255, 255))
    if transition_type == "slide":
        return slide_transition_sequence(clips, duration=duration, direction="left")
    return crossfade_clips(clips, transition_duration=duration)

def apply_auto_transitions(clips, mode="SHORT", niche=None, render_count=0, timeline_plan=None):
    clips = [c for c in clips or [] if c is not None]
    if not clips:
        return None
    profile = _profile(niche=niche, mode=mode, render_count=render_count)
    if _mode_key(mode) == "LONG":
        return crossfade_clips(clips, transition_duration=profile["duration"])
    section = timeline_plan[0].get("section", "body") if timeline_plan else "body"
    t = choose_transition(niche=niche, mode=mode, render_count=render_count, index=0, section=section)
    return apply_transition_sequence(clips, transition_type=t, duration=profile["duration"], mode=mode, niche=niche)

def build_transition_plan(clip_count=10, mode="SHORT", niche=None, render_count=0, timeline_plan=None):
    profile = _profile(niche=niche, mode=mode, render_count=render_count)
    plan = []
    for i in range(max(0, int(clip_count or 0) - 1)):
        section = "body"
        if timeline_plan and i < len(timeline_plan):
            section = timeline_plan[i].get("section", "body")
        transition = choose_transition(niche=niche, mode=mode, render_count=render_count, index=i, section=section)
        plan.append({"index": i, "between": [i, i + 1], "section": section, "transition": transition, "duration": round(profile["duration"], 3)})
    return plan

def normalize_transition_name(name):
    name = str(name or "crossfade").lower().strip()
    aliases = {"smooth": "crossfade", "premium": "premium_crossfade", "soft": "soft_fade", "white_flash": "flash", "hard_cut": "cut", "cinematic": "crossfade"}
    return aliases.get(name, name if name in TRANSITION_NAMES else "crossfade")

def transition_report(niche=None, mode="SHORT", render_count=0):
    return {"output_dir": str(OUTPUT_DIR), "profiles": TRANSITION_PROFILES, "transition_names": TRANSITION_NAMES, "resolved_profile": _profile(niche=niche, mode=mode, render_count=render_count), "moviepy_available": concatenate_videoclips is not None}

def save_transition_report(report, output_path=None):
    output_path = Path(output_path or REPORT_DIR / "transition_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return str(output_path)

class TransitionEngine:
    def __init__(self, mode="SHORT", niche=None, render_count=0):
        self.mode = _mode_key(mode)
        self.niche = niche or "default"
        self.render_count = int(render_count or 0)
        self.profile = _profile(niche=self.niche, mode=self.mode, render_count=self.render_count)

    def choose(self, index=0, section="body"):
        return choose_transition(niche=self.niche, mode=self.mode, render_count=self.render_count, index=index, section=section)

    def plan(self, clip_count=10, timeline_plan=None):
        return build_transition_plan(clip_count=clip_count, mode=self.mode, niche=self.niche, render_count=self.render_count, timeline_plan=timeline_plan)

    def apply(self, clips, transition_type=None, timeline_plan=None):
        if transition_type:
            return apply_transition_sequence(clips, transition_type=normalize_transition_name(transition_type), duration=self.profile["duration"], mode=self.mode, niche=self.niche)
        return apply_auto_transitions(clips, mode=self.mode, niche=self.niche, render_count=self.render_count, timeline_plan=timeline_plan)

    def fade_clip(self, clip, duration=None):
        return apply_fade_to_clip(clip, duration=duration or self.profile["duration"])

    def report(self):
        return transition_report(niche=self.niche, mode=self.mode, render_count=self.render_count)

def add_transitions(clips, mode="SHORT", niche=None, render_count=0):
    return apply_auto_transitions(clips, mode=mode, niche=niche, render_count=render_count)

def apply_transitions(clips, transition_type="crossfade", duration=0.20):
    return apply_transition_sequence(clips, transition_type=transition_type, duration=duration)

def transition_clips(clips, transition_type="crossfade", duration=0.20):
    return apply_transition_sequence(clips, transition_type=transition_type, duration=duration)

def smart_transitions(clips, mode="SHORT", niche=None):
    return apply_auto_transitions(clips, mode=mode, niche=niche)

if __name__ == "__main__":
    print(json.dumps(transition_report(), indent=2))

def _transition_engine_helper_1(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_2(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_3(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_4(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_5(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_6(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_7(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_8(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_9(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_10(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_11(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_12(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_13(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_14(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_15(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_16(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_17(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_18(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_19(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_20(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_21(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_22(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_23(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_24(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_25(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_26(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_27(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_28(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_29(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_30(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_31(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_32(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_33(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_34(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_35(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_36(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_37(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_38(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_39(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_40(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_41(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_42(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_43(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_44(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_45(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_46(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_47(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_48(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_49(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_50(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_51(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_52(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_53(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_54(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_55(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_56(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_57(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_58(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_59(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_60(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_61(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_62(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_63(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_64(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_65(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_66(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_67(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_68(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_69(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_70(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_71(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_72(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_73(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_74(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_75(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_76(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_77(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_78(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_79(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_80(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_81(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_82(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_83(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_84(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_85(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_86(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_87(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_88(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_89(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_90(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_91(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_92(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_93(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_94(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_95(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_96(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_97(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_98(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_99(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_100(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_101(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_102(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_103(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_104(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_105(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_106(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_107(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_108(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_109(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_110(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_111(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_112(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_113(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_114(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_115(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_116(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_117(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_118(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_119(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_120(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_121(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_122(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_123(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_124(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_125(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_126(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_127(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_128(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_129(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_130(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_131(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_132(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_133(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_134(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_135(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_136(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_137(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_138(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_139(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_140(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_141(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_142(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_143(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_144(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_145(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_146(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_147(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_148(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_149(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_150(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_151(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_152(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_153(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_154(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_155(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_156(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_157(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_158(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_159(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_160(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_161(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_162(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_163(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_164(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_165(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_166(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_167(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_168(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_169(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_170(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_171(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_172(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_173(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_174(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_175(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_176(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_177(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_178(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_179(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_180(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_181(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_182(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_183(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_184(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_185(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_186(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_187(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_188(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_189(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_190(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_191(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_192(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_193(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_194(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_195(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_196(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_197(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_198(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_199(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_200(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_201(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_202(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_203(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_204(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_205(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_206(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_207(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_208(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_209(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_210(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_211(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_212(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_213(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_214(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_215(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_216(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_217(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_218(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_219(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _transition_engine_helper_220(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload
