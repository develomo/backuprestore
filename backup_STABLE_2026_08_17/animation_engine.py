import json
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from moviepy.editor import vfx, CompositeVideoClip, ColorClip, ImageClip
except Exception as e:
    print(f"[AnimationEngine] MoviePy import failed: {e}", flush=True)
    vfx = None
    CompositeVideoClip = None
    ColorClip = None
    ImageClip = None

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs" / "animation_engine"
REPORT_DIR = OUTPUT_DIR / "reports"
for folder in (OUTPUT_DIR, REPORT_DIR):
    folder.mkdir(parents=True, exist_ok=True)

ANIMATION_PROFILES = {
    "quantum_future": {"zoom": 0.045, "slide": 18, "shake": 2.0, "fade": 0.18, "energy": 0.78},
    "stoic_wisdom": {"zoom": 0.018, "slide": 8, "shake": 0.0, "fade": 0.35, "energy": 0.30},
    "luxury_lifestyle": {"zoom": 0.030, "slide": 10, "shake": 0.0, "fade": 0.28, "energy": 0.52},
    "mystery": {"zoom": 0.034, "slide": 12, "shake": 1.2, "fade": 0.34, "energy": 0.62},
    "interior_design": {"zoom": 0.018, "slide": 6, "shake": 0.0, "fade": 0.38, "energy": 0.28},
    "finance_simulation": {"zoom": 0.026, "slide": 9, "shake": 0.0, "fade": 0.22, "energy": 0.58},
    "default": {"zoom": 0.026, "slide": 8, "shake": 0.0, "fade": 0.25, "energy": 0.45},
}

ANIMATION_NAMES = [
    "none",
    "subtle_zoom_in",
    "subtle_zoom_out",
    "slow_push",
    "slow_pull",
    "left_drift",
    "right_drift",
    "up_drift",
    "down_drift",
    "premium_float",
    "mystery_creep",
    "micro_shake",
    "hook_punch",
    "soft_reveal",
    "documentary_hold",
]


def safe_print(message):
    try:
        print(str(message).replace("→", "->").replace("—", "-").replace("–", "-"), flush=True)
    except Exception:
        pass


def _mode_key(mode="SHORT"):
    mode = str(mode or "SHORT").upper()
    if mode in ("LONG", "YOUTUBE_LONG", "HORIZONTAL"):
        return "LONG"
    return "SHORT"


def _resolve_niche(niche=None):
    key = str(niche or "default").strip().lower()
    return key if key in ANIMATION_PROFILES else "default"


def _profile(niche=None, mode="SHORT", render_count=0):
    key = _resolve_niche(niche)
    p = dict(ANIMATION_PROFILES[key])
    if _mode_key(mode) == "LONG":
        p["zoom"] = min(p["zoom"], 0.026)
        p["slide"] = min(p["slide"], 10)
        p["shake"] = min(p["shake"], 0.8)
    offset = ((int(render_count or 0) % 7) - 3) * 0.002
    p["zoom"] = max(0.0, p["zoom"] + offset)
    p["niche"] = key
    p["mode"] = _mode_key(mode)
    return p


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


def clamp(value, low, high):
    return max(low, min(high, float(value)))


def ease_out(t):
    t = clamp(t, 0.0, 1.0)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def choose_animation(niche=None, mode="SHORT", render_count=0, clip_index=0, section="body"):
    profile = _profile(niche=niche, mode=mode, render_count=render_count)
    section = str(section or "body").lower()
    rng = random.Random((int(render_count or 0) + 31) * 1009 + int(clip_index or 0) * 131)
    if section == "hook":
        pool = ["hook_punch", "slow_push", "premium_float", "mystery_creep"]
    elif section in ("payoff", "ending"):
        pool = ["soft_reveal", "documentary_hold", "slow_pull", "premium_float"]
    else:
        if profile["energy"] > 0.65:
            pool = ["subtle_zoom_in", "left_drift", "right_drift", "slow_push", "premium_float"]
        elif profile["energy"] < 0.35:
            pool = ["documentary_hold", "soft_reveal", "subtle_zoom_in"]
        else:
            pool = ["subtle_zoom_in", "slow_push", "premium_float", "left_drift"]
    if profile["shake"] > 0.5 and section == "hook":
        pool.append("micro_shake")
    return rng.choice(pool)


def resize_with_dynamic_zoom(clip, amount=0.03, direction="in"):
    if clip is None or vfx is None:
        return clip
    duration = clip_duration(clip)
    amount = max(0.0, float(amount))
    direction = str(direction or "in").lower()
    def scale(t):
        p = clamp(t / max(duration, 0.05), 0.0, 1.0)
        e = ease_in_out(p)
        if direction == "out":
            return 1.0 + amount * (1.0 - e)
        return 1.0 + amount * e
    try:
        return clip.fx(vfx.resize, scale).set_duration(duration)
    except Exception:
        return clip


def crop_to_original_size(clip, size=None):
    if clip is None:
        return clip
    size = size or clip_size(clip)
    try:
        return clip.crop(x_center=clip.w / 2, y_center=clip.h / 2, width=size[0], height=size[1]).set_duration(clip_duration(clip))
    except Exception:
        return clip


def apply_zoom_animation(clip, amount=0.03, direction="in"):
    size = clip_size(clip)
    out = resize_with_dynamic_zoom(clip, amount=amount, direction=direction)
    return crop_to_original_size(out, size=size)


def apply_drift_animation(clip, dx=0, dy=0):
    if clip is None or CompositeVideoClip is None:
        return clip
    duration = clip_duration(clip)
    size = clip_size(clip)
    base = apply_zoom_animation(clip, amount=0.025, direction="in")
    def pos(t):
        p = ease_in_out(t / max(duration, 0.05))
        return (int(-abs(dx) + dx * p), int(-abs(dy) + dy * p))
    try:
        return CompositeVideoClip([base.set_position(pos)], size=size).set_duration(duration)
    except Exception:
        return clip


def apply_micro_shake(clip, intensity=1.0, frequency=18):
    if clip is None or CompositeVideoClip is None:
        return clip
    duration = clip_duration(clip)
    size = clip_size(clip)
    intensity = max(0.0, float(intensity))
    def pos(t):
        x = math.sin(t * frequency) * intensity
        y = math.cos(t * frequency * 0.9) * intensity
        return (int(x), int(y))
    try:
        bigger = apply_zoom_animation(clip, amount=0.018 + intensity * 0.003, direction="in")
        return CompositeVideoClip([bigger.set_position(pos)], size=size).set_duration(duration)
    except Exception:
        return clip


def apply_fade_polish(clip, fade=0.20):
    if clip is None or vfx is None:
        return clip
    duration = clip_duration(clip)
    fade = min(float(fade or 0.0), duration * 0.25)
    out = clip
    try:
        if fade > 0:
            out = out.fx(vfx.fadein, fade)
    except Exception:
        pass
    try:
        if fade > 0:
            out = out.fx(vfx.fadeout, fade)
    except Exception:
        pass
    return out.set_duration(duration)


def apply_animation(clip, animation_name="subtle_zoom_in", niche=None, mode="SHORT", render_count=0, section="body"):
    if clip is None:
        return clip
    profile = _profile(niche=niche, mode=mode, render_count=render_count)
    name = str(animation_name or "subtle_zoom_in").lower()
    amount = profile["zoom"]
    slide = profile["slide"]
    out = clip
    if name == "none":
        out = clip
    elif name == "subtle_zoom_in":
        out = apply_zoom_animation(clip, amount=amount, direction="in")
    elif name == "subtle_zoom_out":
        out = apply_zoom_animation(clip, amount=amount, direction="out")
    elif name == "slow_push":
        out = apply_zoom_animation(clip, amount=amount * 1.25, direction="in")
    elif name == "slow_pull":
        out = apply_zoom_animation(clip, amount=amount * 1.10, direction="out")
    elif name == "left_drift":
        out = apply_drift_animation(clip, dx=-slide, dy=0)
    elif name == "right_drift":
        out = apply_drift_animation(clip, dx=slide, dy=0)
    elif name == "up_drift":
        out = apply_drift_animation(clip, dx=0, dy=-slide)
    elif name == "down_drift":
        out = apply_drift_animation(clip, dx=0, dy=slide)
    elif name == "premium_float":
        out = apply_drift_animation(apply_zoom_animation(clip, amount=amount * 0.8, direction="in"), dx=int(slide * 0.45), dy=int(slide * 0.25))
    elif name == "mystery_creep":
        out = apply_drift_animation(apply_zoom_animation(clip, amount=amount * 1.20, direction="in"), dx=-int(slide * 0.35), dy=int(slide * 0.18))
    elif name == "micro_shake":
        out = apply_micro_shake(clip, intensity=profile["shake"])
    elif name == "hook_punch":
        out = apply_zoom_animation(clip, amount=amount * 1.60, direction="in")
    elif name == "soft_reveal":
        out = apply_zoom_animation(clip, amount=amount * 0.65, direction="in")
    elif name == "documentary_hold":
        out = apply_zoom_animation(clip, amount=amount * 0.35, direction="in")
    else:
        out = apply_zoom_animation(clip, amount=amount, direction="in")
    out = apply_fade_polish(out, fade=profile.get("fade", 0.20) if section in ("hook", "ending") else 0.0)
    try:
        return out.set_duration(clip_duration(clip))
    except Exception:
        return out


def apply_auto_animation(clip, niche=None, mode="SHORT", render_count=0, clip_index=0, section="body"):
    name = choose_animation(niche=niche, mode=mode, render_count=render_count, clip_index=clip_index, section=section)
    return apply_animation(clip, animation_name=name, niche=niche, mode=mode, render_count=render_count, section=section)


def apply_animation_sequence(clips, niche=None, mode="SHORT", render_count=0, sections=None):
    output = []
    sections = sections or []
    for i, clip in enumerate(clips or []):
        section = sections[i] if i < len(sections) else "body"
        output.append(apply_auto_animation(clip, niche=niche, mode=mode, render_count=render_count, clip_index=i, section=section))
    return output


def apply_timeline_animation(clips, timeline_plan=None, niche=None, mode="SHORT", render_count=0):
    timeline_plan = timeline_plan or []
    output = []
    for i, clip in enumerate(clips or []):
        section = "body"
        if i < len(timeline_plan):
            section = timeline_plan[i].get("section", "body")
        output.append(apply_auto_animation(clip, niche=niche, mode=mode, render_count=render_count, clip_index=i, section=section))
    return output


def build_animation_plan(clip_count=10, niche=None, mode="SHORT", render_count=0, timeline_plan=None):
    plan = []
    for i in range(int(clip_count or 0)):
        section = "body"
        if timeline_plan and i < len(timeline_plan):
            section = timeline_plan[i].get("section", "body")
        name = choose_animation(niche=niche, mode=mode, render_count=render_count, clip_index=i, section=section)
        plan.append({"index": i, "section": section, "animation": name})
    return plan


def animation_report(niche=None, mode="SHORT", render_count=0):
    return {
        "output_dir": str(OUTPUT_DIR),
        "profiles": ANIMATION_PROFILES,
        "animation_names": ANIMATION_NAMES,
        "resolved_profile": _profile(niche=niche, mode=mode, render_count=render_count),
        "moviepy_available": vfx is not None,
    }


def save_animation_report(report, output_path=None):
    output_path = Path(output_path or REPORT_DIR / "animation_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return str(output_path)


class AnimationEngine:
    def __init__(self, niche=None, mode="SHORT", render_count=0):
        self.niche = niche or "default"
        self.mode = _mode_key(mode)
        self.render_count = int(render_count or 0)

    def choose(self, clip_index=0, section="body"):
        return choose_animation(niche=self.niche, mode=self.mode, render_count=self.render_count, clip_index=clip_index, section=section)

    def apply(self, clip, animation_name=None, clip_index=0, section="body"):
        animation_name = animation_name or self.choose(clip_index=clip_index, section=section)
        return apply_animation(clip, animation_name=animation_name, niche=self.niche, mode=self.mode, render_count=self.render_count, section=section)

    def sequence(self, clips, sections=None):
        return apply_animation_sequence(clips, niche=self.niche, mode=self.mode, render_count=self.render_count, sections=sections)

    def timeline(self, clips, timeline_plan=None):
        return apply_timeline_animation(clips, timeline_plan=timeline_plan, niche=self.niche, mode=self.mode, render_count=self.render_count)

    def plan(self, clip_count=10, timeline_plan=None):
        return build_animation_plan(clip_count=clip_count, niche=self.niche, mode=self.mode, render_count=self.render_count, timeline_plan=timeline_plan)

    def report(self):
        return animation_report(niche=self.niche, mode=self.mode, render_count=self.render_count)


def animate_clip(clip, animation_name="subtle_zoom_in"):
    return apply_animation(clip, animation_name=animation_name)


def apply_clip_animation(clip, animation_name="subtle_zoom_in"):
    return apply_animation(clip, animation_name=animation_name)


def animate_sequence(clips, niche=None, mode="SHORT"):
    return apply_animation_sequence(clips, niche=niche, mode=mode)


def auto_animate(clip, niche=None, mode="SHORT"):
    return apply_auto_animation(clip, niche=niche, mode=mode)


if __name__ == "__main__":
    print(json.dumps(animation_report(), indent=2))

def _animation_engine_helper_1(payload=None, fallback=None):
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


def _animation_engine_helper_2(payload=None, fallback=None):
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


def _animation_engine_helper_3(payload=None, fallback=None):
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


def _animation_engine_helper_4(payload=None, fallback=None):
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


def _animation_engine_helper_5(payload=None, fallback=None):
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


def _animation_engine_helper_6(payload=None, fallback=None):
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


def _animation_engine_helper_7(payload=None, fallback=None):
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


def _animation_engine_helper_8(payload=None, fallback=None):
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


def _animation_engine_helper_9(payload=None, fallback=None):
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


def _animation_engine_helper_10(payload=None, fallback=None):
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


def _animation_engine_helper_11(payload=None, fallback=None):
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


def _animation_engine_helper_12(payload=None, fallback=None):
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


def _animation_engine_helper_13(payload=None, fallback=None):
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


def _animation_engine_helper_14(payload=None, fallback=None):
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


def _animation_engine_helper_15(payload=None, fallback=None):
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


def _animation_engine_helper_16(payload=None, fallback=None):
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


def _animation_engine_helper_17(payload=None, fallback=None):
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


def _animation_engine_helper_18(payload=None, fallback=None):
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


def _animation_engine_helper_19(payload=None, fallback=None):
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


def _animation_engine_helper_20(payload=None, fallback=None):
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


def _animation_engine_helper_21(payload=None, fallback=None):
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


def _animation_engine_helper_22(payload=None, fallback=None):
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


def _animation_engine_helper_23(payload=None, fallback=None):
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


def _animation_engine_helper_24(payload=None, fallback=None):
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


def _animation_engine_helper_25(payload=None, fallback=None):
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


def _animation_engine_helper_26(payload=None, fallback=None):
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


def _animation_engine_helper_27(payload=None, fallback=None):
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


def _animation_engine_helper_28(payload=None, fallback=None):
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


def _animation_engine_helper_29(payload=None, fallback=None):
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


def _animation_engine_helper_30(payload=None, fallback=None):
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


def _animation_engine_helper_31(payload=None, fallback=None):
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


def _animation_engine_helper_32(payload=None, fallback=None):
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


def _animation_engine_helper_33(payload=None, fallback=None):
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


def _animation_engine_helper_34(payload=None, fallback=None):
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


def _animation_engine_helper_35(payload=None, fallback=None):
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


def _animation_engine_helper_36(payload=None, fallback=None):
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


def _animation_engine_helper_37(payload=None, fallback=None):
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


def _animation_engine_helper_38(payload=None, fallback=None):
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


def _animation_engine_helper_39(payload=None, fallback=None):
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


def _animation_engine_helper_40(payload=None, fallback=None):
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


def _animation_engine_helper_41(payload=None, fallback=None):
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


def _animation_engine_helper_42(payload=None, fallback=None):
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


def _animation_engine_helper_43(payload=None, fallback=None):
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


def _animation_engine_helper_44(payload=None, fallback=None):
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


def _animation_engine_helper_45(payload=None, fallback=None):
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


def _animation_engine_helper_46(payload=None, fallback=None):
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


def _animation_engine_helper_47(payload=None, fallback=None):
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


def _animation_engine_helper_48(payload=None, fallback=None):
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


def _animation_engine_helper_49(payload=None, fallback=None):
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


def _animation_engine_helper_50(payload=None, fallback=None):
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


def _animation_engine_helper_51(payload=None, fallback=None):
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


def _animation_engine_helper_52(payload=None, fallback=None):
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


def _animation_engine_helper_53(payload=None, fallback=None):
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


def _animation_engine_helper_54(payload=None, fallback=None):
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


def _animation_engine_helper_55(payload=None, fallback=None):
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


def _animation_engine_helper_56(payload=None, fallback=None):
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


def _animation_engine_helper_57(payload=None, fallback=None):
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


def _animation_engine_helper_58(payload=None, fallback=None):
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


def _animation_engine_helper_59(payload=None, fallback=None):
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


def _animation_engine_helper_60(payload=None, fallback=None):
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


def _animation_engine_helper_61(payload=None, fallback=None):
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


def _animation_engine_helper_62(payload=None, fallback=None):
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


def _animation_engine_helper_63(payload=None, fallback=None):
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


def _animation_engine_helper_64(payload=None, fallback=None):
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


def _animation_engine_helper_65(payload=None, fallback=None):
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


def _animation_engine_helper_66(payload=None, fallback=None):
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


def _animation_engine_helper_67(payload=None, fallback=None):
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


def _animation_engine_helper_68(payload=None, fallback=None):
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


def _animation_engine_helper_69(payload=None, fallback=None):
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


def _animation_engine_helper_70(payload=None, fallback=None):
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


def _animation_engine_helper_71(payload=None, fallback=None):
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


def _animation_engine_helper_72(payload=None, fallback=None):
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


def _animation_engine_helper_73(payload=None, fallback=None):
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


def _animation_engine_helper_74(payload=None, fallback=None):
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


def _animation_engine_helper_75(payload=None, fallback=None):
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


def _animation_engine_helper_76(payload=None, fallback=None):
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


def _animation_engine_helper_77(payload=None, fallback=None):
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


def _animation_engine_helper_78(payload=None, fallback=None):
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


def _animation_engine_helper_79(payload=None, fallback=None):
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


def _animation_engine_helper_80(payload=None, fallback=None):
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


def _animation_engine_helper_81(payload=None, fallback=None):
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


def _animation_engine_helper_82(payload=None, fallback=None):
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


def _animation_engine_helper_83(payload=None, fallback=None):
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


def _animation_engine_helper_84(payload=None, fallback=None):
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


def _animation_engine_helper_85(payload=None, fallback=None):
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


def _animation_engine_helper_86(payload=None, fallback=None):
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


def _animation_engine_helper_87(payload=None, fallback=None):
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


def _animation_engine_helper_88(payload=None, fallback=None):
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


def _animation_engine_helper_89(payload=None, fallback=None):
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


def _animation_engine_helper_90(payload=None, fallback=None):
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


def _animation_engine_helper_91(payload=None, fallback=None):
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


def _animation_engine_helper_92(payload=None, fallback=None):
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


def _animation_engine_helper_93(payload=None, fallback=None):
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


def _animation_engine_helper_94(payload=None, fallback=None):
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


def _animation_engine_helper_95(payload=None, fallback=None):
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


def _animation_engine_helper_96(payload=None, fallback=None):
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


def _animation_engine_helper_97(payload=None, fallback=None):
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


def _animation_engine_helper_98(payload=None, fallback=None):
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


def _animation_engine_helper_99(payload=None, fallback=None):
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


def _animation_engine_helper_100(payload=None, fallback=None):
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


def _animation_engine_helper_101(payload=None, fallback=None):
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


def _animation_engine_helper_102(payload=None, fallback=None):
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


def _animation_engine_helper_103(payload=None, fallback=None):
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


def _animation_engine_helper_104(payload=None, fallback=None):
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


def _animation_engine_helper_105(payload=None, fallback=None):
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


def _animation_engine_helper_106(payload=None, fallback=None):
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


def _animation_engine_helper_107(payload=None, fallback=None):
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


def _animation_engine_helper_108(payload=None, fallback=None):
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


def _animation_engine_helper_109(payload=None, fallback=None):
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


def _animation_engine_helper_110(payload=None, fallback=None):
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


def _animation_engine_helper_111(payload=None, fallback=None):
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


def _animation_engine_helper_112(payload=None, fallback=None):
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


def _animation_engine_helper_113(payload=None, fallback=None):
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


def _animation_engine_helper_114(payload=None, fallback=None):
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


def _animation_engine_helper_115(payload=None, fallback=None):
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


def _animation_engine_helper_116(payload=None, fallback=None):
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


def _animation_engine_helper_117(payload=None, fallback=None):
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


def _animation_engine_helper_118(payload=None, fallback=None):
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


def _animation_engine_helper_119(payload=None, fallback=None):
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


def _animation_engine_helper_120(payload=None, fallback=None):
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


def _animation_engine_helper_121(payload=None, fallback=None):
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


def _animation_engine_helper_122(payload=None, fallback=None):
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


def _animation_engine_helper_123(payload=None, fallback=None):
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


def _animation_engine_helper_124(payload=None, fallback=None):
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


def _animation_engine_helper_125(payload=None, fallback=None):
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


def _animation_engine_helper_126(payload=None, fallback=None):
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


def _animation_engine_helper_127(payload=None, fallback=None):
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


def _animation_engine_helper_128(payload=None, fallback=None):
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


def _animation_engine_helper_129(payload=None, fallback=None):
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


def _animation_engine_helper_130(payload=None, fallback=None):
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


def _animation_engine_helper_131(payload=None, fallback=None):
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


def _animation_engine_helper_132(payload=None, fallback=None):
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


def _animation_engine_helper_133(payload=None, fallback=None):
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


def _animation_engine_helper_134(payload=None, fallback=None):
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


def _animation_engine_helper_135(payload=None, fallback=None):
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


def _animation_engine_helper_136(payload=None, fallback=None):
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


def _animation_engine_helper_137(payload=None, fallback=None):
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


def _animation_engine_helper_138(payload=None, fallback=None):
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


def _animation_engine_helper_139(payload=None, fallback=None):
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


def _animation_engine_helper_140(payload=None, fallback=None):
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


def _animation_engine_helper_141(payload=None, fallback=None):
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


def _animation_engine_helper_142(payload=None, fallback=None):
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


def _animation_engine_helper_143(payload=None, fallback=None):
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


def _animation_engine_helper_144(payload=None, fallback=None):
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


def _animation_engine_helper_145(payload=None, fallback=None):
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


def _animation_engine_helper_146(payload=None, fallback=None):
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


def _animation_engine_helper_147(payload=None, fallback=None):
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


def _animation_engine_helper_148(payload=None, fallback=None):
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


def _animation_engine_helper_149(payload=None, fallback=None):
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


def _animation_engine_helper_150(payload=None, fallback=None):
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


def _animation_engine_helper_151(payload=None, fallback=None):
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


def _animation_engine_helper_152(payload=None, fallback=None):
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


def _animation_engine_helper_153(payload=None, fallback=None):
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


def _animation_engine_helper_154(payload=None, fallback=None):
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


def _animation_engine_helper_155(payload=None, fallback=None):
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


def _animation_engine_helper_156(payload=None, fallback=None):
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


def _animation_engine_helper_157(payload=None, fallback=None):
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


def _animation_engine_helper_158(payload=None, fallback=None):
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


def _animation_engine_helper_159(payload=None, fallback=None):
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


def _animation_engine_helper_160(payload=None, fallback=None):
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


def _animation_engine_helper_161(payload=None, fallback=None):
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


def _animation_engine_helper_162(payload=None, fallback=None):
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


def _animation_engine_helper_163(payload=None, fallback=None):
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


def _animation_engine_helper_164(payload=None, fallback=None):
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


def _animation_engine_helper_165(payload=None, fallback=None):
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


def _animation_engine_helper_166(payload=None, fallback=None):
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


def _animation_engine_helper_167(payload=None, fallback=None):
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


def _animation_engine_helper_168(payload=None, fallback=None):
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


def _animation_engine_helper_169(payload=None, fallback=None):
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


def _animation_engine_helper_170(payload=None, fallback=None):
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


def _animation_engine_helper_171(payload=None, fallback=None):
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


def _animation_engine_helper_172(payload=None, fallback=None):
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


def _animation_engine_helper_173(payload=None, fallback=None):
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


def _animation_engine_helper_174(payload=None, fallback=None):
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


def _animation_engine_helper_175(payload=None, fallback=None):
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


def _animation_engine_helper_176(payload=None, fallback=None):
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


def _animation_engine_helper_177(payload=None, fallback=None):
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


def _animation_engine_helper_178(payload=None, fallback=None):
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


def _animation_engine_helper_179(payload=None, fallback=None):
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


def _animation_engine_helper_180(payload=None, fallback=None):
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


def _animation_engine_helper_181(payload=None, fallback=None):
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


def _animation_engine_helper_182(payload=None, fallback=None):
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


def _animation_engine_helper_183(payload=None, fallback=None):
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


def _animation_engine_helper_184(payload=None, fallback=None):
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


def _animation_engine_helper_185(payload=None, fallback=None):
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


def _animation_engine_helper_186(payload=None, fallback=None):
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


def _animation_engine_helper_187(payload=None, fallback=None):
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


def _animation_engine_helper_188(payload=None, fallback=None):
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


def _animation_engine_helper_189(payload=None, fallback=None):
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


def _animation_engine_helper_190(payload=None, fallback=None):
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


def _animation_engine_helper_191(payload=None, fallback=None):
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


def _animation_engine_helper_192(payload=None, fallback=None):
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


def _animation_engine_helper_193(payload=None, fallback=None):
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


def _animation_engine_helper_194(payload=None, fallback=None):
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


def _animation_engine_helper_195(payload=None, fallback=None):
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


def _animation_engine_helper_196(payload=None, fallback=None):
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


def _animation_engine_helper_197(payload=None, fallback=None):
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


def _animation_engine_helper_198(payload=None, fallback=None):
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


def _animation_engine_helper_199(payload=None, fallback=None):
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


def _animation_engine_helper_200(payload=None, fallback=None):
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


def _animation_engine_helper_201(payload=None, fallback=None):
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


def _animation_engine_helper_202(payload=None, fallback=None):
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


def _animation_engine_helper_203(payload=None, fallback=None):
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


def _animation_engine_helper_204(payload=None, fallback=None):
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


def _animation_engine_helper_205(payload=None, fallback=None):
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


def _animation_engine_helper_206(payload=None, fallback=None):
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


def _animation_engine_helper_207(payload=None, fallback=None):
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


def _animation_engine_helper_208(payload=None, fallback=None):
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


def _animation_engine_helper_209(payload=None, fallback=None):
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


def _animation_engine_helper_210(payload=None, fallback=None):
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


def _animation_engine_helper_211(payload=None, fallback=None):
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


def _animation_engine_helper_212(payload=None, fallback=None):
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


def _animation_engine_helper_213(payload=None, fallback=None):
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


def _animation_engine_helper_214(payload=None, fallback=None):
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


def _animation_engine_helper_215(payload=None, fallback=None):
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


def _animation_engine_helper_216(payload=None, fallback=None):
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


def _animation_engine_helper_217(payload=None, fallback=None):
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


def _animation_engine_helper_218(payload=None, fallback=None):
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


def _animation_engine_helper_219(payload=None, fallback=None):
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


def _animation_engine_helper_220(payload=None, fallback=None):
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


# ============================================================
# PREMIUM MOTION / ZOOM / TRANSITION FEEL PATCH
# Focus areas:
#   - Zoom Effects target 95.
#   - Motion Blur target 93.
#   - Camera Motion target 95.
#   - Viewer retention through visual rhythm, not caption animation.
# ============================================================

PREMIUM_MOTION_STRENGTH = 1.18
PREMIUM_ZOOM_MIN = 0.030
PREMIUM_ZOOM_MAX_SHORT = 0.060
PREMIUM_ZOOM_MAX_LONG = 0.034

def _premium_anim_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return float(default)

try:
    for _anim_key, _anim_profile in ANIMATION_PROFILES.items():
        mode_long_limit = _anim_key in ("stoic_wisdom", "interior_design")
        _anim_profile["zoom"] = min(max(_premium_anim_float(_anim_profile.get("zoom"), 0.026) * PREMIUM_MOTION_STRENGTH, PREMIUM_ZOOM_MIN if not mode_long_limit else 0.020), PREMIUM_ZOOM_MAX_SHORT)
        _anim_profile["slide"] = int(max(_premium_anim_float(_anim_profile.get("slide"), 8) * 1.15, 10))
        _anim_profile["fade"] = max(0.16, min(_premium_anim_float(_anim_profile.get("fade"), 0.25), 0.32))
        _anim_profile["premium_motion_mode"] = True
except Exception:
    pass

try:
    _premium_anim_original_choose_animation = choose_animation
    def choose_animation(niche=None, mode="SHORT", render_count=0, clip_index=0, section="body"):
        chosen = _premium_anim_original_choose_animation(niche=niche, mode=mode, render_count=render_count, clip_index=clip_index, section=section)
        if str(section or "").lower() == "hook":
            premium_pool = ["slow_push", "hook_punch", "premium_float", "subtle_zoom_in"]
        elif int(clip_index or 0) % 5 == 0:
            premium_pool = ["left_drift", "right_drift", "premium_float", "slow_push"]
        elif int(clip_index or 0) % 3 == 0:
            premium_pool = ["subtle_zoom_in", "slow_push", "soft_reveal"]
        else:
            premium_pool = [chosen, "premium_float", "subtle_zoom_in"]
        try:
            rng = random.Random((int(render_count or 0) + 97) * 1777 + int(clip_index or 0) * 313)
            return rng.choice([x for x in premium_pool if x in ANIMATION_NAMES] or [chosen])
        except Exception:
            return chosen
except Exception:
    pass

try:
    _premium_anim_original_apply_auto_animation = apply_auto_animation
    def apply_auto_animation(clip, *args, **kwargs):
        kwargs.setdefault("premium_motion_mode", True)
        kwargs.setdefault("motion_strength", 0.92)
        return _premium_anim_original_apply_auto_animation(clip, *args, **kwargs)
except Exception:
    pass

try:
    _premium_anim_original_apply_animation_sequence = apply_animation_sequence
    def apply_animation_sequence(clips, *args, **kwargs):
        kwargs.setdefault("premium_motion_mode", True)
        kwargs.setdefault("motion_strength", 0.92)
        return _premium_anim_original_apply_animation_sequence(clips, *args, **kwargs)
except Exception:
    pass

def premium_motion_report():
    return {
        "camera_motion_target": 95,
        "zoom_effects_target": 95,
        "motion_blur_target": 93,
        "caption_animation_changed": False,
        "viewer_retention_pattern_interrupts": True,
    }



# ============================================================
# ANIMATION ENGINE FINAL PREMIUM INTEGRATION PATCH
# Practical goals:
#   Subtle micro camera movement, stabilization feel,
#   3-4 second pattern interrupt, premium zoom variation,
#   non-repetitive motion scheduler, without touching captions.
# ============================================================

ANIMATION_PREMIUM_VERSION = "2026-06-final-premium-animation"
ANIMATION_PATTERN_SECONDS_SHORT = 3.4
ANIMATION_PATTERN_SECONDS_LONG = 4.2
ANIMATION_MICRO_ZOOM_MIN = 0.012
ANIMATION_MICRO_ZOOM_MAX_SHORT = 0.055
ANIMATION_MICRO_ZOOM_MAX_LONG = 0.032
ANIMATION_STABILIZE_ZOOM_PAD = 0.018

def _anim_premium_print(message):
    try:
        safe_print(str(message))
    except Exception:
        try:
            print(str(message), flush=True)
        except Exception:
            pass

def _anim_premium_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return float(default)

def _anim_premium_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return int(default)

def _anim_premium_mode(mode="SHORT"):
    try:
        return _mode_key(mode)
    except Exception:
        mode = str(mode or "SHORT").upper()
        return "LONG" if mode in ("LONG", "YOUTUBE_LONG", "HORIZONTAL") else "SHORT"

def _anim_premium_duration(clip):
    try:
        return max(0.05, float(clip.duration))
    except Exception:
        return 0.05

def _anim_premium_clamp(value, low, high):
    return max(float(low), min(float(high), _anim_premium_float(value, low)))

def _anim_premium_pattern_interval(mode="SHORT"):
    return ANIMATION_PATTERN_SECONDS_LONG if _anim_premium_mode(mode) == "LONG" else ANIMATION_PATTERN_SECONDS_SHORT

def _anim_premium_zoom_limit(mode="SHORT"):
    return ANIMATION_MICRO_ZOOM_MAX_LONG if _anim_premium_mode(mode) == "LONG" else ANIMATION_MICRO_ZOOM_MAX_SHORT

def _anim_premium_motion_amount(niche=None, mode="SHORT", render_count=0, clip_index=0, section="body"):
    profile = _profile(niche=niche, mode=mode, render_count=render_count)
    base_zoom = _anim_premium_float(profile.get("zoom"), 0.026)
    energy = _anim_premium_float(profile.get("energy"), 0.45)
    section = str(section or "body").lower()
    multiplier = 1.25 if section == "hook" else 0.85 if section in ("payoff", "ending") else 1.0
    variation = (((_anim_premium_int(clip_index, 0) % 5) - 2) * 0.003)
    amount = base_zoom * multiplier + variation + (energy * 0.006)
    return _anim_premium_clamp(amount, ANIMATION_MICRO_ZOOM_MIN, _anim_premium_zoom_limit(mode))

def _anim_premium_choose_motion(niche=None, mode="SHORT", render_count=0, clip_index=0, section="body"):
    section = str(section or "body").lower()
    rng = random.Random((_anim_premium_int(render_count, 0) + 97) * 1009 + (_anim_premium_int(clip_index, 0) + 11) * 313)
    profile = _profile(niche=niche, mode=mode, render_count=render_count)
    energy = _anim_premium_float(profile.get("energy"), 0.45)
    if section == "hook":
        pool = ["slow_push", "hook_punch", "premium_float", "subtle_zoom_in"]
    elif section in ("payoff", "ending"):
        pool = ["soft_reveal", "slow_pull", "documentary_hold", "premium_float"]
    elif energy > 0.65:
        pool = ["subtle_zoom_in", "slow_push", "left_drift", "right_drift", "premium_float"]
    elif energy < 0.35:
        pool = ["documentary_hold", "soft_reveal", "subtle_zoom_in", "premium_float"]
    else:
        pool = ["subtle_zoom_in", "slow_push", "premium_float", "left_drift", "right_drift"]
    safe_pool = [x for x in pool if x in ANIMATION_NAMES]
    return rng.choice(safe_pool or ["subtle_zoom_in"])

def _anim_premium_apply_micro_stabilization(clip, mode="SHORT", strength=0.35):
    if clip is None or vfx is None:
        return clip
    duration = _anim_premium_duration(clip)
    try:
        size = tuple(clip.size)
    except Exception:
        size = (1080, 1920)
    pad = _anim_premium_clamp(ANIMATION_STABILIZE_ZOOM_PAD * _anim_premium_float(strength, 0.35), 0.003, 0.018)
    try:
        stabilized = resize_with_dynamic_zoom(clip, amount=pad, direction="in")
        stabilized = crop_to_original_size(stabilized, size=size)
        return stabilized.set_duration(duration)
    except Exception:
        return clip

def _anim_premium_apply_motion_variation(clip, animation_name=None, niche=None, mode="SHORT", render_count=0, clip_index=0, section="body", motion_strength=0.70):
    if clip is None:
        return clip
    duration = _anim_premium_duration(clip)
    amount = _anim_premium_motion_amount(niche=niche, mode=mode, render_count=render_count, clip_index=clip_index, section=section)
    amount *= _anim_premium_clamp(motion_strength, 0.25, 1.25)
    animation_name = animation_name or _anim_premium_choose_motion(niche=niche, mode=mode, render_count=render_count, clip_index=clip_index, section=section)
    try:
        clip = _anim_premium_apply_micro_stabilization(clip, mode=mode, strength=0.45)
    except Exception:
        pass
    try:
        if animation_name == "subtle_zoom_in":
            return apply_zoom_animation(clip, amount=amount, direction="in").set_duration(duration)
        if animation_name == "subtle_zoom_out":
            return apply_zoom_animation(clip, amount=amount, direction="out").set_duration(duration)
        if animation_name == "slow_push":
            return apply_zoom_animation(clip, amount=amount * 1.10, direction="in").set_duration(duration)
        if animation_name == "slow_pull":
            return apply_zoom_animation(clip, amount=amount * 0.85, direction="out").set_duration(duration)
        if animation_name == "left_drift":
            return apply_drift_animation(clip, dx=10, dy=0).set_duration(duration)
        if animation_name == "right_drift":
            return apply_drift_animation(clip, dx=-10, dy=0).set_duration(duration)
        if animation_name == "premium_float":
            return apply_drift_animation(clip, dx=7 if _anim_premium_int(clip_index) % 2 == 0 else -7, dy=4 if _anim_premium_int(clip_index) % 2 == 0 else -4).set_duration(duration)
        if animation_name == "hook_punch":
            return apply_zoom_animation(clip, amount=min(amount * 1.35, _anim_premium_zoom_limit(mode)), direction="in").set_duration(duration)
        if animation_name == "soft_reveal":
            return apply_zoom_animation(clip, amount=amount * 0.65, direction="in").set_duration(duration)
        if animation_name == "documentary_hold":
            return apply_zoom_animation(clip, amount=amount * 0.45, direction="in").set_duration(duration)
    except Exception as exc:
        _anim_premium_print(f"[AnimationPremium] motion variation skipped: {exc}")
    return clip

def build_premium_motion_plan(duration=60.0, mode="SHORT", niche=None, render_count=0, clip_count=None):
    duration = max(0.1, _anim_premium_float(duration, 60.0))
    interval = _anim_premium_pattern_interval(mode)
    count = clip_count or max(1, int(duration / interval))
    plan = []
    for i in range(int(count)):
        section = "hook" if i == 0 else "payoff" if i == int(count) - 1 else "body"
        plan.append({
            "index": i,
            "section": section,
            "animation": _anim_premium_choose_motion(niche=niche, mode=mode, render_count=render_count, clip_index=i, section=section),
            "zoom_amount": _anim_premium_motion_amount(niche=niche, mode=mode, render_count=render_count, clip_index=i, section=section),
            "pattern_interrupt": True,
            "micro_stabilization": True,
            "caption_animation_changed": False,
        })
    return plan

try:
    for _anim_key, _anim_profile in ANIMATION_PROFILES.items():
        _is_soft = _anim_key in ("stoic_wisdom", "interior_design")
        _limit = 0.030 if _is_soft else 0.052
        _anim_profile["zoom"] = _anim_premium_clamp(_anim_premium_float(_anim_profile.get("zoom"), 0.026) * 1.12, 0.014 if _is_soft else 0.024, _limit)
        _anim_profile["slide"] = int(_anim_premium_clamp(_anim_premium_float(_anim_profile.get("slide"), 8) * 1.08, 5, 18))
        _anim_profile["fade"] = _anim_premium_clamp(_anim_premium_float(_anim_profile.get("fade"), 0.25), 0.16, 0.38)
        _anim_profile["premium_motion_mode"] = True
except Exception:
    pass

try:
    _anim_premium_original_choose_animation = choose_animation
    def choose_animation(niche=None, mode="SHORT", render_count=0, clip_index=0, section="body"):
        chosen = _anim_premium_choose_motion(niche=niche, mode=mode, render_count=render_count, clip_index=clip_index, section=section)
        return chosen or _anim_premium_original_choose_animation(niche=niche, mode=mode, render_count=render_count, clip_index=clip_index, section=section)
except Exception:
    pass

try:
    _anim_premium_original_apply_auto_animation = apply_auto_animation
    def apply_auto_animation(clip, *args, **kwargs):
        kwargs = dict(kwargs or {})
        try:
            return _anim_premium_apply_motion_variation(
                clip,
                animation_name=kwargs.get("animation_name", None),
                niche=kwargs.get("niche", None),
                mode=kwargs.get("mode", "SHORT"),
                render_count=kwargs.get("render_count", 0),
                clip_index=kwargs.get("clip_index", 0),
                section=kwargs.get("section", "body"),
                motion_strength=kwargs.get("motion_strength", 0.70),
            )
        except Exception:
            clean_kwargs = dict(kwargs)
            for bad in ["premium_motion_mode", "motion_strength", "animation_name"]:
                clean_kwargs.pop(bad, None)
            try:
                return _anim_premium_original_apply_auto_animation(clip, *args, **clean_kwargs)
            except Exception:
                return clip
except Exception:
    pass

try:
    _anim_premium_original_apply_animation_sequence = apply_animation_sequence
    def apply_animation_sequence(clips, *args, **kwargs):
        clips = list(clips or [])
        output = []
        for i, clip in enumerate(clips):
            section = "hook" if i == 0 else "payoff" if i == len(clips) - 1 else "body"
            output.append(_anim_premium_apply_motion_variation(
                clip,
                niche=kwargs.get("niche", None),
                mode=kwargs.get("mode", "SHORT"),
                render_count=kwargs.get("render_count", 0),
                clip_index=i,
                section=section,
                motion_strength=kwargs.get("motion_strength", 0.70),
            ))
        return output
except Exception:
    pass

def animation_engine_premium_report(duration=60.0, mode="SHORT", niche=None, render_count=0):
    return {
        "version": ANIMATION_PREMIUM_VERSION,
        "mode": _anim_premium_mode(mode),
        "pattern_interrupt_seconds": _anim_premium_pattern_interval(mode),
        "motion_plan": build_premium_motion_plan(duration=duration, mode=mode, niche=niche, render_count=render_count),
        "caption_animation_changed": False,
        "motion_stabilization": True,
        "micro_camera_movement": True,
        "zoom_target_score": 95,
        "camera_motion_target_score": 95,
        "motion_blur_target_score": 93,
    }



# ============================================================
# PHASE 13 - AI ANIMATION ENGINE V2 COMPAT LAYER
# ============================================================
# This section is intentionally appended at the end of animation_engine.py.
# It does not remove old functions. It adds AI-plan-aware helpers that can
# be used by batch_long_renderer.py, safe_long_video_polished.py, or future
# short/long pipelines.
#
# Goals:
# - Use Editing Brain camera_motion plan
# - Use Effects Brain pattern interrupts
# - Avoid same animation repeatedly
# - Keep old animation functions working
# - Stay MoviePy-safe for existing short pipelines
# - Provide FFmpeg-friendly plan output for long pipeline
# ============================================================

PHASE13_ANIMATION_ENGINE_VERSION = "animation_engine_phase13_ai_motion_v2"


def _phase13_safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return float(default)


def _phase13_safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return int(default)


def phase13_animation_report():
    return {
        "version": PHASE13_ANIMATION_ENGINE_VERSION,
        "ai_camera_motion": True,
        "ai_pattern_interrupts": True,
        "anti_repeat": True,
        "legacy_functions_preserved": True,
        "moviepy_optional": True,
        "ffmpeg_plan_supported": True,
    }


def normalize_ai_motion_name(value=None):
    """Normalize camera motion names from Editing Brain / Effects Brain."""
    text = str(value or "").lower().strip()

    if not text:
        return "slow_push_in"

    if "zoom_out" in text or "pull" in text or "out" == text:
        return "slow_zoom_out"
    if "push" in text or "zoom_in" in text or "center_push" in text:
        return "slow_push_in"
    if "left" in text:
        return "pan_left"
    if "right" in text:
        return "pan_right"
    if "up" in text or "top" in text:
        return "pan_up"
    if "down" in text or "bottom" in text:
        return "pan_down"
    if "parallax" in text:
        return "micro_parallax"
    if "shake" in text:
        return "micro_shake"
    if "hold" in text:
        return "documentary_hold"

    return "slow_push_in"


def build_ai_animation_decision(
    clip_index=0,
    niche="default",
    mode="LONG",
    render_count=0,
    editing_item=None,
    effects_plan=None,
    memory_state=None,
):
    """Build one animation decision from AI plans.

    This does not render anything. It returns a stable decision object.
    Long FFmpeg renderer can translate this into zoompan expressions.
    MoviePy pipeline can translate it into apply_animation().
    """
    editing_item = editing_item or {}
    effects_plan = effects_plan or {}
    memory_state = memory_state or {}

    camera_motion = editing_item.get("camera_motion") if isinstance(editing_item, dict) else {}
    if not isinstance(camera_motion, dict):
        camera_motion = {}

    pattern_interrupt = editing_item.get("pattern_interrupt") if isinstance(editing_item, dict) else {}
    if not isinstance(pattern_interrupt, dict):
        pattern_interrupt = {}

    motion_type = normalize_ai_motion_name(camera_motion.get("type") or camera_motion.get("pan"))
    pan = str(camera_motion.get("pan") or "").lower()
    strength = str(camera_motion.get("strength") or "balanced").lower()

    interrupt_enabled = bool(pattern_interrupt.get("enabled"))
    if not interrupt_enabled:
        pi = effects_plan.get("pattern_interrupts") if isinstance(effects_plan, dict) else {}
        if isinstance(pi, dict) and pi.get("enabled"):
            interrupt_enabled = int(clip_index or 0) > 0 and int(clip_index or 0) % 6 == 0

    zoom_start = _phase13_safe_float(camera_motion.get("zoom_start"), 1.0)
    zoom_end = _phase13_safe_float(camera_motion.get("zoom_end"), 1.055)

    if strength in ("gentle", "smooth"):
        zoom_end = min(zoom_end, 1.065)
    elif strength in ("medium_dynamic", "dynamic"):
        zoom_end = max(zoom_end, 1.075)
    elif strength in ("strong", "hook"):
        zoom_end = max(zoom_end, 1.09)

    if interrupt_enabled:
        zoom_end = min(1.14, zoom_end + 0.018)

    # Anti-repeat memory: if last motion repeats too many times, rotate.
    recent = list(memory_state.get("recent_motions", [])) if isinstance(memory_state, dict) else []
    if len(recent) >= 2 and recent[-1] == motion_type and recent[-2] == motion_type:
        rotation = ["slow_push_in", "slow_zoom_out", "pan_left", "pan_right", "micro_parallax"]
        try:
            current_pos = rotation.index(motion_type)
            motion_type = rotation[(current_pos + 1) % len(rotation)]
        except Exception:
            motion_type = rotation[int(clip_index or 0) % len(rotation)]

    if "left" in pan:
        pan = "left_to_right"
    elif "right" in pan:
        pan = "right_to_left"
    elif "bottom" in pan or "up" in pan:
        pan = "bottom_to_top"
    elif "top" in pan or "down" in pan:
        pan = "top_to_bottom"
    elif motion_type == "micro_parallax":
        pan = "micro_diagonal"
    else:
        pan = "center"

    return {
        "version": PHASE13_ANIMATION_ENGINE_VERSION,
        "clip_index": int(clip_index or 0),
        "niche": str(niche or "default"),
        "mode": str(mode or "LONG").upper(),
        "motion_type": motion_type,
        "pan": pan,
        "zoom_start": max(1.0, zoom_start),
        "zoom_end": max(1.005, min(1.14, zoom_end)),
        "interrupt": interrupt_enabled,
        "strength": strength,
        "moviepy_animation": map_ai_motion_to_legacy_animation(motion_type, interrupt_enabled),
        "ffmpeg_zoompan": build_ffmpeg_zoompan_params(motion_type, pan, zoom_end, interrupt_enabled),
    }


def map_ai_motion_to_legacy_animation(motion_type, interrupt=False):
    motion_type = normalize_ai_motion_name(motion_type)
    if interrupt:
        return "hook_punch"
    if motion_type == "slow_zoom_out":
        return "subtle_zoom_out"
    if motion_type == "pan_left":
        return "left_drift"
    if motion_type == "pan_right":
        return "right_drift"
    if motion_type == "pan_up":
        return "up_drift"
    if motion_type == "pan_down":
        return "down_drift"
    if motion_type == "micro_parallax":
        return "premium_float"
    if motion_type == "micro_shake":
        return "micro_shake"
    if motion_type == "documentary_hold":
        return "documentary_hold"
    return "subtle_zoom_in"


def build_ffmpeg_zoompan_params(motion_type, pan, zoom_end=1.055, interrupt=False):
    """Return FFmpeg zoompan-friendly parameters.

    batch_long_renderer.py already has its own implementation, but this helper
    gives a shared standard for future pipelines.
    """
    motion_type = normalize_ai_motion_name(motion_type)
    pan = str(pan or "center").lower()
    zoom_end = max(1.005, min(1.14, _phase13_safe_float(zoom_end, 1.055)))

    if interrupt:
        zoom_end = min(1.14, zoom_end + 0.015)

    if "left" in pan:
        x = "(iw-iw/zoom)*0.35"
        y = "(ih-ih/zoom)/2"
    elif "right" in pan:
        x = "(iw-iw/zoom)*0.65"
        y = "(ih-ih/zoom)/2"
    elif "bottom" in pan:
        x = "(iw-iw/zoom)/2"
        y = "(ih-ih/zoom)*0.65"
    elif "top" in pan:
        x = "(iw-iw/zoom)/2"
        y = "(ih-ih/zoom)*0.35"
    elif "diagonal" in pan:
        x = "(iw-iw/zoom)*0.55"
        y = "(ih-ih/zoom)*0.45"
    else:
        x = "(iw-iw/zoom)/2"
        y = "(ih-ih/zoom)/2"

    step = 0.00028
    if zoom_end >= 1.08:
        step = 0.00036

    return {
        "zoom_end": zoom_end,
        "zoom_step": step,
        "x": x,
        "y": y,
    }


def build_ai_animation_sequence(
    edit_plan=None,
    effects_plan=None,
    niche="default",
    mode="LONG",
    render_count=0,
    max_items=None,
):
    edit_plan = edit_plan or []
    if not isinstance(edit_plan, list):
        edit_plan = []

    total = len(edit_plan)
    if max_items:
        total = min(total, int(max_items))

    memory = {"recent_motions": []}
    sequence = []

    for i in range(total):
        decision = build_ai_animation_decision(
            clip_index=i,
            niche=niche,
            mode=mode,
            render_count=render_count,
            editing_item=edit_plan[i],
            effects_plan=effects_plan,
            memory_state=memory,
        )
        sequence.append(decision)
        memory["recent_motions"].append(decision["motion_type"])
        memory["recent_motions"] = memory["recent_motions"][-4:]

    return sequence


def apply_ai_animation(
    clip,
    clip_index=0,
    niche=None,
    mode="LONG",
    render_count=0,
    editing_item=None,
    effects_plan=None,
    memory_state=None,
):
    """MoviePy-compatible AI animation wrapper.

    If MoviePy is unavailable or clip is None, returns clip unchanged.
    """
    decision = build_ai_animation_decision(
        clip_index=clip_index,
        niche=niche,
        mode=mode,
        render_count=render_count,
        editing_item=editing_item,
        effects_plan=effects_plan,
        memory_state=memory_state,
    )

    anim_name = decision.get("moviepy_animation") or "subtle_zoom_in"

    try:
        return apply_animation(
            clip,
            animation_name=anim_name,
            niche=niche,
            mode=mode,
            render_count=render_count,
            section="body",
        )
    except Exception:
        return clip


def choose_ai_transition(index=0, editing_item=None, niche="default", render_count=0):
    """Return transition decision from Editing Brain item.

    This is a planning helper. Rendering side can read kind/duration.
    """
    editing_item = editing_item or {}
    transition = editing_item.get("transition") if isinstance(editing_item, dict) else {}
    if not isinstance(transition, dict):
        transition = {}

    kind = str(transition.get("kind") or "").lower()
    duration = _phase13_safe_float(transition.get("duration"), 0.18)

    if not kind:
        if int(index or 0) % 6 == 0:
            kind = "creative_soft_transition"
            duration = 0.28
        else:
            kind = "clean_cut"
            duration = 0.10

    if str(niche or "").lower() == "islamic" and ("flash" in kind or "shake" in kind):
        kind = "soft_fade"
        duration = 0.25

    return {
        "index": int(index or 0),
        "kind": kind,
        "duration": max(0.05, min(0.60, duration)),
        "source": "editing_brain" if transition else "fallback",
    }


def build_transition_sequence(edit_plan=None, niche="default", render_count=0):
    edit_plan = edit_plan or []
    if not isinstance(edit_plan, list):
        edit_plan = []
    return [
        choose_ai_transition(i, item, niche=niche, render_count=render_count)
        for i, item in enumerate(edit_plan)
    ]


def phase13_apply_animation_plan_to_clip(clip, plan_item=None, niche=None, mode="LONG", render_count=0, clip_index=0):
    """Compatibility function for future renderers."""
    return apply_ai_animation(
        clip,
        clip_index=clip_index,
        niche=niche,
        mode=mode,
        render_count=render_count,
        editing_item=plan_item,
        effects_plan=None,
        memory_state=None,
    )


# Backward-compatible alias names some pipelines may try.
apply_phase13_ai_animation = apply_ai_animation
build_phase13_animation_decision = build_ai_animation_decision
build_phase13_animation_sequence = build_ai_animation_sequence
choose_phase13_transition = choose_ai_transition


if __name__ == "__main__":
    print(json.dumps(phase13_animation_report(), indent=2))
