import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "outputs" / "smart_clip_engine"
REPORT_DIR = OUTPUT_DIR / "reports"
for folder in (OUTPUT_DIR, REPORT_DIR):
    folder.mkdir(parents=True, exist_ok=True)

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}

CLIP_PROFILES = {
    "quantum_future": {"prefer_fast": True, "repeat_safe": True, "variety": 0.82, "energy": 0.78},
    "stoic_wisdom": {"prefer_fast": False, "repeat_safe": True, "variety": 0.45, "energy": 0.30},
    "luxury_lifestyle": {"prefer_fast": False, "repeat_safe": True, "variety": 0.60, "energy": 0.52},
    "mystery": {"prefer_fast": True, "repeat_safe": True, "variety": 0.72, "energy": 0.62},
    "interior_design": {"prefer_fast": False, "repeat_safe": True, "variety": 0.50, "energy": 0.28},
    "finance_simulation": {"prefer_fast": True, "repeat_safe": True, "variety": 0.66, "energy": 0.58},
    "default": {"prefer_fast": True, "repeat_safe": True, "variety": 0.60, "energy": 0.45},
}


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
    return key if key in CLIP_PROFILES else "default"


def _profile(niche=None, mode="SHORT", render_count=0):
    key = _resolve_niche(niche)
    p = dict(CLIP_PROFILES[key])
    if _mode_key(mode) == "LONG":
        p["variety"] = max(0.35, p["variety"] * 0.82)
    p["niche"] = key
    p["mode"] = _mode_key(mode)
    p["render_count"] = int(render_count or 0)
    return p


def natural_key(path):
    stem = Path(path).stem
    parts = []
    current = ""
    for ch in stem:
        if ch.isdigit():
            current += ch
        else:
            if current:
                parts.append(int(current))
                current = ""
            parts.append(ch.lower())
    if current:
        parts.append(int(current))
    return parts


def list_video_files(folder):
    folder = Path(folder)
    if not folder.exists():
        return []
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS], key=natural_key)


def normalize_clip_paths(clips):
    out = []
    for item in clips or []:
        p = Path(item)
        if p.exists() and p.is_file() and p.suffix.lower() in VIDEO_EXTS:
            out.append(p)
    return sorted(out, key=natural_key)


def clip_name_score(path, niche=None, section=None):
    p = Path(path)
    name = p.stem.lower()
    score = 1.0
    key = _resolve_niche(niche)
    if key in name:
        score += 1.4
    section = str(section or "").lower()
    if section and section in name:
        score += 1.1
    for token in ["hook", "intro", "fast", "close", "detail", "wide", "broll", "premium", "dark", "future"]:
        if token in name:
            score += 0.15
    try:
        if p.stem.isdigit():
            score += 0.3
    except Exception:
        pass
    return score


def section_preferred_keywords(section, niche=None):
    section = str(section or "body").lower()
    key = _resolve_niche(niche)
    base = {
        "hook": ["hook", "intro", "fast", "close", "shock"],
        "setup": ["setup", "wide", "establish", "intro"],
        "body": ["body", "broll", "detail", "main"],
        "payoff": ["reveal", "payoff", "after", "result"],
        "ending": ["ending", "outro", "final", "result"],
    }.get(section, ["broll", "main"])
    niche_words = {
        "quantum_future": ["ai", "robot", "future", "tech"],
        "stoic_wisdom": ["calm", "man", "nature", "dark"],
        "luxury_lifestyle": ["luxury", "car", "home", "watch"],
        "mystery": ["dark", "secret", "mystery", "shadow"],
        "interior_design": ["room", "home", "design", "before", "after"],
        "finance_simulation": ["money", "business", "chart", "office"],
        "default": [],
    }.get(key, [])
    return base + niche_words


def rank_clips_for_section(clips, section="body", niche=None, render_count=0):
    clips = normalize_clip_paths(clips)
    keywords = section_preferred_keywords(section, niche=niche)
    ranked = []
    for p in clips:
        name = p.stem.lower()
        score = clip_name_score(p, niche=niche, section=section)
        for kw in keywords:
            if kw in name:
                score += 0.7
        ranked.append((score, p))
    ranked.sort(key=lambda x: (-x[0], natural_key(x[1])))
    if int(render_count or 0) % 2 == 1 and len(ranked) > 2:
        head = ranked[:2]
        tail = ranked[2:]
        random.Random(int(render_count)).shuffle(tail)
        ranked = head + tail
    return [p for _, p in ranked]


def pick_clip_for_timeline_index(clips, index, section="body", niche=None, render_count=0, used_counts=None):
    ranked = rank_clips_for_section(clips, section=section, niche=niche, render_count=render_count)
    if not ranked:
        return None
    used_counts = used_counts or {}
    scored = []
    for i, p in enumerate(ranked):
        use_penalty = used_counts.get(str(p), 0) * 1.25
        rotation_bonus = 0.35 if (i + int(render_count or 0)) % len(ranked) == int(index or 0) % len(ranked) else 0.0
        score = 10.0 - i - use_penalty + rotation_bonus
        scored.append((score, p))
    scored.sort(key=lambda x: (-x[0], natural_key(x[1])))
    return scored[0][1]


def build_smart_clip_sequence(clips, timeline_plan, words=None, niche=None, render_count=0):
    clips = normalize_clip_paths(clips)
    if not clips:
        return []
    used_counts = {}
    sequence = []
    for i, item in enumerate(timeline_plan or []):
        section = item.get("section", "body")
        picked = pick_clip_for_timeline_index(clips, i, section=section, niche=niche, render_count=render_count, used_counts=used_counts)
        if picked is None:
            continue
        used_counts[str(picked)] = used_counts.get(str(picked), 0) + 1
        sequence.append({
            "index": i,
            "clip_path": str(picked),
            "clip_name": picked.name,
            "timeline_start": item.get("start", 0.0),
            "timeline_end": item.get("end", 0.0),
            "timeline_duration": item.get("duration", 0.0),
            "section": section,
            "use_count": used_counts[str(picked)],
        })
    return sequence


def build_round_robin_sequence(clips, timeline_plan, render_count=0):
    clips = normalize_clip_paths(clips)
    if not clips:
        return []
    sequence = []
    offset = int(render_count or 0) % len(clips)
    for i, item in enumerate(timeline_plan or []):
        p = clips[(i + offset) % len(clips)]
        sequence.append({
            "index": i,
            "clip_path": str(p),
            "clip_name": p.name,
            "timeline_start": item.get("start", 0.0),
            "timeline_end": item.get("end", 0.0),
            "timeline_duration": item.get("duration", 0.0),
            "section": item.get("section", "body"),
        })
    return sequence


def build_clip_usage_report(sequence):
    usage = {}
    for item in sequence or []:
        path = item.get("clip_path")
        usage.setdefault(path, {"count": 0, "duration": 0.0, "name": item.get("clip_name")})
        usage[path]["count"] += 1
        usage[path]["duration"] += float(item.get("timeline_duration", 0.0) or 0.0)
    for key in usage:
        usage[key]["duration"] = round(usage[key]["duration"], 3)
    return usage


def validate_clip_sequence(sequence, total_duration=None):
    issues = []
    if not sequence:
        issues.append("Sequence is empty.")
    for item in sequence or []:
        if not Path(item.get("clip_path", "")).exists():
            issues.append(f"Missing clip: {item.get('clip_path')}")
        if float(item.get("timeline_duration", 0.0) or 0.0) <= 0:
            issues.append(f"Invalid duration at index {item.get('index')}")
    if total_duration is not None and sequence:
        end = float(sequence[-1].get("timeline_end", 0.0) or 0.0)
        if abs(end - float(total_duration)) > 0.5:
            issues.append("Sequence end does not match target duration.")
    return {"ok": len(issues) == 0, "issues": issues}


def sequence_to_format_plan(sequence):
    return [{
        "index": item["index"],
        "source": item["clip_path"],
        "start": item.get("timeline_start", 0.0),
        "end": item.get("timeline_end", 0.0),
        "duration": item.get("timeline_duration", 0.0),
        "section": item.get("section", "body"),
    } for item in sequence or []]


def save_clip_sequence(sequence, output_path=None):
    output_path = Path(output_path or REPORT_DIR / "smart_clip_sequence.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(sequence, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return str(output_path)


def load_clip_sequence(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_clip_inventory(folder_or_clips):
    if isinstance(folder_or_clips, (str, Path)) and Path(folder_or_clips).is_dir():
        clips = list_video_files(folder_or_clips)
    else:
        clips = normalize_clip_paths(folder_or_clips)
    items = []
    for p in clips:
        items.append({"path": str(p), "name": p.name, "stem": p.stem, "suffix": p.suffix.lower(), "numeric_order": natural_key(p)})
    return {"count": len(items), "items": items}


def find_clips_by_keywords(clips, keywords=None):
    clips = normalize_clip_paths(clips)
    keywords = [str(k).lower() for k in (keywords or [])]
    if not keywords:
        return clips
    matched = []
    for p in clips:
        name = p.stem.lower()
        if any(k in name for k in keywords):
            matched.append(p)
    return matched


def build_section_clip_map(clips, niche=None):
    clips = normalize_clip_paths(clips)
    mapping = {}
    for section in ["hook", "setup", "body", "payoff", "ending"]:
        mapping[section] = [str(p) for p in rank_clips_for_section(clips, section=section, niche=niche)]
    return mapping


def clip_engine_report(clips=None, folder=None, timeline_plan=None, niche=None, render_count=0):
    if clips is None and folder is not None:
        clips = list_video_files(folder)
    clips = normalize_clip_paths(clips or [])
    sequence = build_smart_clip_sequence(clips, timeline_plan or [], niche=niche, render_count=render_count)
    return {
        "output_dir": str(OUTPUT_DIR),
        "profiles": CLIP_PROFILES,
        "niche": _resolve_niche(niche),
        "inventory": build_clip_inventory(clips),
        "section_map": build_section_clip_map(clips, niche=niche),
        "sequence": sequence,
        "usage": build_clip_usage_report(sequence),
        "validation": validate_clip_sequence(sequence),
    }


def save_clip_report(report, output_path=None):
    output_path = Path(output_path or REPORT_DIR / "smart_clip_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return str(output_path)


class SmartClipEngine:
    def __init__(self, mode="SHORT", niche=None, render_count=0):
        self.mode = _mode_key(mode)
        self.niche = niche or "default"
        self.render_count = int(render_count or 0)

    def list(self, folder):
        return list_video_files(folder)

    def inventory(self, folder_or_clips):
        return build_clip_inventory(folder_or_clips)

    def rank(self, clips, section="body"):
        return rank_clips_for_section(clips, section=section, niche=self.niche, render_count=self.render_count)

    def sequence(self, clips, timeline_plan, words=None):
        return build_smart_clip_sequence(clips, timeline_plan, words=words, niche=self.niche, render_count=self.render_count)

    def round_robin(self, clips, timeline_plan):
        return build_round_robin_sequence(clips, timeline_plan, render_count=self.render_count)

    def report(self, clips=None, folder=None, timeline_plan=None):
        return clip_engine_report(clips=clips, folder=folder, timeline_plan=timeline_plan, niche=self.niche, render_count=self.render_count)


def smart_sequence(clips, timeline_plan, niche=None):
    return build_smart_clip_sequence(clips, timeline_plan, niche=niche)


def select_clips(clips, timeline_plan, niche=None):
    return build_smart_clip_sequence(clips, timeline_plan, niche=niche)


def build_sequence(clips, timeline_plan, niche=None):
    return build_smart_clip_sequence(clips, timeline_plan, niche=niche)


if __name__ == "__main__":
    print(json.dumps(clip_engine_report(), indent=2))

def _smart_clip_helper_1(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_2(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_3(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_4(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_5(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_6(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_7(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_8(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_9(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_10(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_11(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_12(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_13(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_14(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_15(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_16(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_17(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_18(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_19(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_20(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_21(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_22(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_23(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_24(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_25(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_26(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_27(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_28(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_29(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_30(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_31(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_32(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_33(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_34(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_35(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_36(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_37(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_38(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_39(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_40(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_41(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_42(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_43(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_44(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_45(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_46(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_47(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_48(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_49(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_50(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_51(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_52(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_53(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_54(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_55(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_56(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_57(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_58(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_59(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_60(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_61(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_62(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_63(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_64(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_65(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_66(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_67(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_68(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_69(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_70(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_71(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_72(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_73(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_74(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_75(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_76(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_77(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_78(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_79(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_80(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_81(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_82(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_83(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_84(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_85(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_86(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_87(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_88(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_89(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_90(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_91(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_92(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_93(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_94(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_95(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_96(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_97(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_98(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_99(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_100(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_101(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_102(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_103(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_104(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_105(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_106(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_107(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_108(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_109(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_110(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_111(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_112(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_113(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_114(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_115(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_116(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_117(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_118(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_119(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_120(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_121(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_122(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_123(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_124(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_125(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_126(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_127(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_128(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_129(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_130(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_131(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_132(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_133(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_134(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_135(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_136(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_137(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_138(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_139(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_140(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_141(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_142(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_143(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_144(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_145(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_146(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_147(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_148(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_149(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_150(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_151(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_152(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_153(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_154(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_155(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_156(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_157(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_158(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_159(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_160(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_161(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_162(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_163(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_164(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_165(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_166(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_167(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_168(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_169(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_170(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_171(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_172(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_173(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_174(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_175(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_176(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_177(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_178(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_179(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_180(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_181(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_182(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_183(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_184(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_185(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_186(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_187(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_188(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_189(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_190(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_191(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_192(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_193(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_194(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_195(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_196(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_197(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_198(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_199(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_200(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_201(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_202(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_203(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_204(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_205(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_206(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_207(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_208(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_209(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_210(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_211(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_212(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_213(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_214(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_215(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_216(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_217(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_218(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_219(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _smart_clip_helper_220(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload
