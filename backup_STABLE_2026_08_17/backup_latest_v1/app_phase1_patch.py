"""
============================================================
MY CREATION VIDEO GENERATOR — PHASE 1
app_phase1_patch.py — UI + Pipeline Integration v2.0
============================================================

UPDATED for:
  - niche_editing_presets.py v2.0 (new _m/_t/_c/_g/_a/_au helpers)
  - auto_editing_brain.py (auto_detect_niche, auto_choose_preset, get_auto_brain)
  - No old import names (PRESET_REGISTRY, get_preset_with_variation, etc.)

PURPOSE:
  User input → AI brain → niche + preset# → full editing config
  → UI display → batch_long_renderer.py render
============================================================
"""

from __future__ import annotations

import json
import logging
import os
import random
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ============================================================
# IMPORT FILE 1 — niche_editing_presets.py
# ============================================================
try:
    from niche_editing_presets import (
        EditingPreset,
        get_preset,
        get_presets_for_niche,
        get_all_presets,
        get_niche_display_name,
        get_niche_family,
        get_preset_summary,
        get_total_preset_count,
        get_all_niches,
        list_all_presets_summary,
        get_niches_with_presets,
        apply_variation,
        get_clip_motion,
        get_clip_transition,
        get_clip_animation,
        build_ffmpeg_color_filter,
        build_ffmpeg_motion_filter,
        build_ffmpeg_transition_filter,
        build_ffmpeg_audio_filter,
        NICHE_DISPLAY_NAMES,
        NICHE_FAMILY_MAP,
        MOTION_14,
        TRANSITION_16,
        ANIMATION_9,
    )
    PRESETS_AVAILABLE = True
    logger_presets = logging.getLogger(__name__ + ".presets")
except ImportError as e:
    PRESETS_AVAILABLE = False
    print(f"\u26a0\ufe0f  niche_editing_presets.py not found — presets disabled ({e})")

# ============================================================
# IMPORT FILE 2 — auto_editing_brain.py
# ============================================================
try:
    from auto_editing_brain import (
        auto_detect_niche,
        auto_choose_preset,
        get_auto_brain,
        AutoEditingBrain,
    )
    BRAIN_AVAILABLE = True
except ImportError as e:
    BRAIN_AVAILABLE = False
    print(f"\u26a0\ufe0f  auto_editing_brain.py not found — auto-detect disabled ({e})")


# ============================================================
# CONFIGURATION
# ============================================================
BASE_DIR = Path(__file__).parent
RENDERER_SCRIPT = BASE_DIR / "batch_long_renderer.py"
MUSIC_DATA_FILE = BASE_DIR / "background_music_data.json"
OUTPUT_DIR = BASE_DIR / "output"
RENDER_LOG_FILE = BASE_DIR / "render_log.json"
COUNTER_FILE = BASE_DIR / "render_counter.json"

MAX_RENDER_TIME_MINUTES = 30
DEFAULT_VIDEO_WIDTH = 854
DEFAULT_VIDEO_HEIGHT = 480
DEFAULT_FPS = 24

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "app_phase1.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ============================================================
# RENDER COUNTER
# ============================================================
class RenderCounter:
    def __init__(self, counter_file: Path):
        self.counter_file = counter_file
        self.count = self._load()

    def _load(self) -> int:
        try:
            if self.counter_file.exists():
                raw = self.counter_file.read_bytes()
                data = json.loads(raw.decode("utf-8", errors="replace"))
                return data.get("render_count", 0)
        except Exception:
            pass
        return 0

    def _save(self):
        self.counter_file.write_bytes(
            json.dumps({"render_count": self.count}, indent=2).encode("utf-8")
        )

    def next(self) -> int:
        current = self.count
        self.count += 1
        self._save()
        return current

    def reset(self):
        self.count = 0
        self._save()


render_counter = RenderCounter(COUNTER_FILE)


# ============================================================
# FALLBACK NICHE KEYWORDS (when brain unavailable)
# ============================================================
NICHE_KEYWORDS: Dict[str, List[str]] = {
    "luxury_lifestyle": [
        "luxury", "luxurious", "wealthy", "rich", "expensive", "premium",
        "high-end", "exclusive", "yacht", "supercar", "ferrari", "lamborghini",
        "rolex", "gucci", "louis vuitton", "chanel", "dior", "billionaire",
        "millionaire", "private jet", "penthouse", "mansion", "villa",
        "champagne", "caviar", "designer", "couture", "bespoke",
        "gold", "diamond", "platinum", "luxury watch", "luxury car",
        "5-star", "five star", "first class", "estate", "wine cellar",
    ],
    "quantum_future": [
        "ai", "artificial intelligence", "machine learning", "deep learning",
        "quantum", "future", "tech", "technology", "robot", "automation",
        "neural", "algorithm", "data science", "blockchain", "crypto",
        "metaverse", "vr", "virtual reality", "ar", "augmented reality",
        "spacex", "nasa", "rocket", "mars", "singularity", "cyborg",
        "digital", "code", "programming", "software", "hardware",
        "chip", "processor", "gpu", "nvidia", "openai", "chatgpt",
        "innovation", "disrupt", "startup", "silicon valley",
        "elon musk", "tesla", "neuralink", "boston dynamics",
    ],
    "mystery": [
        "mystery", "crime", "murder", "detective", "investigation",
        "suspense", "thriller", "horror", "paranormal", "supernatural",
        "ghost", "haunted", "unsolved", "disappearance", "cold case",
        "evidence", "suspect", "witness", "clue", "conspiracy",
        "secret", "hidden", "dark", "shadow", "noir",
        "forensic", "autopsy", "crime scene", "serial killer",
        "true crime", "whodunit",
    ],
    "stoic_wisdom": [
        "stoic", "stoicism", "marcus aurelius", "seneca", "epictetus",
        "philosophy", "wisdom", "discipline", "mindset", "meditation",
        "mindfulness", "zen", "virtue", "character", "resilience",
        "perseverance", "inner peace", "tranquility", "self-improvement",
        "self-control", "courage", "daily stoic", "reflection",
        "morning routine", "habits", "focus", "purpose", "meaning",
        "adversity", "obstacle", "growth mindset", "mental toughness",
        "ryan holiday", "ego is the enemy", "stillness",
    ],
    "interior_design": [
        "interior", "design", "decor", "decoration", "home", "house",
        "apartment", "room", "furniture", "renovation", "remodel",
        "architecture", "architect", "minimalist", "scandinavian",
        "bohemian", "industrial", "modern", "contemporary", "vintage",
        "kitchen", "bathroom", "bedroom", "living room", "lighting",
        "color palette", "texture", "fabric", "wallpaper", "flooring",
        "tile", "marble", "wood", "concrete", "open plan", "layout",
        "feng shui", "aesthetic", "diy", "makeover", "transformation",
        "before after", "interior designer",
    ],
    "finance_simulation": [
        "finance", "financial", "money", "wealth", "invest", "investing",
        "stock", "stocks", "market", "trading", "trader", "wall street",
        "dividend", "portfolio", "asset", "real estate", "property",
        "passive income", "retirement", "saving", "budget", "debt",
        "credit", "loan", "mortgage", "tax", "crypto", "bitcoin",
        "ethereum", "forex", "commodity", "gold", "bond", "etf",
        "index fund", "mutual fund", "hedge fund", "venture capital",
        "startup funding", "ipo", "revenue", "profit", "loss",
        "balance sheet", "cash flow", "net worth", "financial freedom",
        "warren buffett", "economics", "inflation", "recession",
    ],
}


# ============================================================
# CORE: FALLBACK NICHE DETECTION
# ============================================================
def _fallback_niche_detect(content: str) -> str:
    content_lower = content.lower()
    scores: Dict[str, int] = {}
    for niche, keywords in NICHE_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in content_lower:
                score += len(kw.split()) * 2
        scores[niche] = score
    best_niche = max(scores, key=scores.get)
    best_score = scores[best_niche]
    if best_score == 0:
        logger.info("No keywords matched, using default niche")
        return "default"
    logger.info(f"Fallback detection: {best_niche} (score={best_score})")
    return best_niche


# ============================================================
# CORE: CHOOSE BEST PRESET
# ============================================================
def _choose_best_preset(niche: str, content: str, video_duration: float) -> int:
    if video_duration < 30:
        candidates = [3, 4, 7, 8]
    elif video_duration < 120:
        candidates = [1, 2, 3, 5, 6, 7]
    else:
        candidates = [1, 2, 5, 6]
    content_lower = content.lower()
    high_energy_words = ["fast", "exciting", "energetic", "hype", "viral", "trending",
                         "urgent", "breaking", "alert", "wow", "amazing"]
    calm_words = ["calm", "peaceful", "relaxing", "gentle", "slow", "meditation",
                  "reflection", "thoughtful", "quiet", "subtle", "minimal"]
    energy_score = sum(1 for w in high_energy_words if w in content_lower)
    calm_score = sum(1 for w in calm_words if w in content_lower)
    if energy_score > calm_score:
        energetic = [p for p in candidates if p in (3, 4, 7, 8)]
        if energetic:
            candidates = energetic
    elif calm_score > energy_score:
        calm = [p for p in candidates if p in (1, 2, 5, 6)]
        if calm:
            candidates = calm
    chosen = random.choice(candidates)
    logger.info(f"Auto preset chosen: #{chosen} (candidates={candidates}, energy={energy_score}, calm={calm_score})")
    return chosen


# ============================================================
# MAIN PIPELINE: analyze_and_get_config()
# ============================================================
def analyze_and_get_config(
    content: str,
    niche: Optional[str] = None,
    preset_number: Optional[int] = None,
    video_duration: float = 60.0,
) -> Dict[str, Any]:
    logger.info("=" * 60)
    logger.info("ANALYZE & GET CONFIG")
    logger.info(f"Content length: {len(content)} chars")
    logger.info(f"Niche override: {niche}")
    logger.info(f"Preset override: {preset_number}")
    logger.info("=" * 60)

    result = {
        "timestamp": datetime.now().isoformat(),
        "content_length": len(content),
        "video_duration": video_duration,
    }

    # ---- STEP 1: Determine Niche ----
    if niche is None or niche == "auto":
        if BRAIN_AVAILABLE:
            try:
                detected_niche, confidence, info = auto_detect_niche(
                    script_text=content
                )
                logger.info(f"Brain detected: niche={detected_niche}, confidence={confidence:.2f}")
                result["niche_detected"] = detected_niche
                result["niche_confidence"] = confidence
                result["niche_method"] = "auto_editing_brain"
            except Exception as e:
                logger.warning(f"Brain failed: {e}, falling back to keyword match")
                detected_niche = _fallback_niche_detect(content)
                result["niche_method"] = "keyword_fallback"
        else:
            detected_niche = _fallback_niche_detect(content)
            result["niche_method"] = "keyword_fallback"
    else:
        detected_niche = niche
        result["niche_method"] = "manual"

    result["niche"] = detected_niche
    result["niche_display"] = get_niche_display_name(detected_niche)

    # ---- STEP 2: Determine Preset Number ----
    if preset_number is None:
        if BRAIN_AVAILABLE:
            try:
                preset_number = auto_choose_preset(detected_niche, 0, content)
                result["preset_method"] = "brain"
            except Exception:
                preset_number = _choose_best_preset(detected_niche, content, video_duration)
                result["preset_method"] = "heuristic"
        else:
            preset_number = _choose_best_preset(detected_niche, content, video_duration)
            result["preset_method"] = "heuristic"
    else:
        result["preset_method"] = "manual"

    preset_number = max(1, min(8, int(preset_number)))
    result["preset_number"] = preset_number

    # ---- STEP 3: Get Preset Object ----
    render_num = render_counter.next()
    result["render_count"] = render_num

    if PRESETS_AVAILABLE:
        try:
            preset = get_preset(detected_niche, preset_number)
        except (ValueError, KeyError):
            logger.warning(f"Niche '{detected_niche}' not found, falling back to default")
            preset = get_preset("default", 1)
            result["preset_fallback"] = True
            result["niche"] = "default"
            result["niche_display"] = "Default / General"
            detected_niche = "default"
    else:
        # Dummy fallback when presets unavailable
        preset = _build_dummy_preset(detected_niche, preset_number)

    result["preset_label"] = preset.label
    result["preset_description"] = preset.description

    # ---- STEP 4: Generate Per-Clip Configs ----
    result["clips"] = _generate_clip_configs(
        preset=preset,
        detected_niche=detected_niche,
        preset_number=preset_number,
        render_count=render_num,
        video_duration=video_duration,
    )

    # ---- STEP 5: Global Config ----
    result["color_grade"] = {
        "filter": preset.color.grade_filter,
        "temperature_shift": preset.color.temperature_shift,
        "vignette": preset.color.vignette_strength,
        "film_grain": preset.color.film_grain_opacity,
        "sharpness": preset.color.sharpness,
    }
    result["audio_config"] = {
        "voice_volume": preset.audio.voice_volume,
        "music_volume": preset.audio.music_volume,
        "sfx_volume": preset.audio.sfx_volume,
        "target_lufs": preset.audio.target_lufs,
        "ducking_strength": preset.audio.ducking_strength,
    }
    result["motion_config"] = {
        "directions": preset.motion.directions,
        "zoom_min": preset.motion.zoom_min,
        "zoom_max": preset.motion.zoom_max,
        "zoom_step": preset.motion.zoom_step,
    }
    result["transition_config"] = {
        "types": preset.transition.types,
        "duration_base": preset.transition.duration_base,
        "duration_range": list(preset.transition.duration_range),
    }
    result["cut_rhythm"] = {
        "hook_min": preset.cut_rhythm.hook_min,
        "hook_max": preset.cut_rhythm.hook_max,
        "body_min": preset.cut_rhythm.body_min,
        "body_max": preset.cut_rhythm.body_max,
        "emphasis_min": preset.cut_rhythm.emphasis_min,
        "emphasis_max": preset.cut_rhythm.emphasis_max,
        "long_min": preset.cut_rhythm.long_min,
        "long_max": preset.cut_rhythm.long_max,
    }

    # ---- STEP 6: Summary ----
    result["summary"] = {
        "niche": detected_niche,
        "niche_display": get_niche_display_name(detected_niche),
        "niche_family": get_niche_family(detected_niche),
        "preset_number": preset_number,
        "preset_label": preset.label,
        "render_count": render_num,
        "preset_description": preset.description,
    }

    logger.info(f"Config generated: {len(result['clips'])} clips, "
                f"niche={detected_niche}, preset=#{preset_number}, render=#{render_num}")

    return result


def _build_dummy_preset(niche: str, preset_number: int):
    """Minimal preset when niche_editing_presets is not available."""
    return EditingPreset(
        preset_id=f"{niche}_preset_{preset_number}",
        preset_number=preset_number,
        niche=niche,
        label=f"Preset #{preset_number}",
        description="Dummy preset (niche_editing_presets not loaded)",
    )


# ============================================================
# CLIP CONFIG GENERATION
# ============================================================
def _generate_clip_configs(
    preset: "EditingPreset",
    detected_niche: str,
    preset_number: int,
    render_count: int,
    video_duration: float,
) -> List[Dict[str, Any]]:
    cr = preset.cut_rhythm
    avg_clip_duration = (cr.body_min + cr.body_max) / 2
    estimated_clips = max(3, int(video_duration / avg_clip_duration))
    estimated_clips = min(estimated_clips, 60)

    logger.info(f"Generating configs for ~{estimated_clips} clips "
                f"(avg duration: {avg_clip_duration:.1f}s)")

    clips = []
    cumulative_time = 0.0

    for i in range(estimated_clips):
        if i == 0:
            section = "hook"
            clip_dur = random.uniform(cr.hook_min, cr.hook_max)
        elif i == estimated_clips - 1:
            section = "ending"
            clip_dur = random.uniform(cr.emphasis_min, cr.emphasis_max)
        elif i % 5 == 0:
            section = "emphasis"
            clip_dur = random.uniform(cr.emphasis_min, cr.emphasis_max)
        else:
            section = "body"
            clip_dur = random.uniform(cr.body_min, cr.body_max)

        cumulative_time += clip_dur

        motion_dir, zoom = get_clip_motion(preset, i, render_count)
        trans_type, trans_dur = get_clip_transition(preset, i, render_count)
        anim_style = get_clip_animation(preset, i, render_count)

        clips.append({
            "index": i,
            "section": section,
            "duration": round(clip_dur, 1),
            "cumulative_time": round(cumulative_time, 1),
            "motion": {
                "direction": motion_dir,
                "zoom": zoom,
            },
            "transition": {
                "type": trans_type,
                "duration": trans_dur,
            },
            "animation": {
                "style": anim_style,
            },
        })

    return clips


# ============================================================
# RENDER EXECUTION
# ============================================================
def execute_render(
    config: Dict[str, Any],
    content: str,
    output_filename: Optional[str] = None,
    music_file: Optional[str] = None,
    voice_model: str = "default",
) -> Dict[str, Any]:
    if not RENDERER_SCRIPT.exists():
        return {"status": "error", "error": f"Renderer not found: {RENDERER_SCRIPT}"}

    if output_filename is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        niche = config.get("niche", "default")
        preset = config.get("preset_number", 1)
        output_filename = f"{niche}_preset{preset}_{ts}.mp4"

    output_path = OUTPUT_DIR / output_filename
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    render_config = {
        "niche": config.get("niche", "default"),
        "preset_number": config.get("preset_number", 1),
        "render_count": config.get("render_count", 0),
        "clips": config.get("clips", []),
        "color_grade": config.get("color_grade", {}),
        "audio_config": config.get("audio_config", {}),
        "cut_rhythm": config.get("cut_rhythm", {}),
        "video_width": DEFAULT_VIDEO_WIDTH,
        "video_height": DEFAULT_VIDEO_HEIGHT,
        "fps": DEFAULT_FPS,
    }

    config_path = BASE_DIR / "temp_render_config.json"
    config_path.write_text(json.dumps(render_config, indent=2), encoding="utf-8")

    cmd = [
        sys.executable, str(RENDERER_SCRIPT),
        "--config", str(config_path),
        "--output", str(output_path),
        "--content", content,
    ]
    if music_file:
        cmd.extend(["--music", music_file])
    if voice_model:
        cmd.extend(["--voice", voice_model])

    logger.info(f"RENDER COMMAND: {' '.join(cmd[:5])}...")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(BASE_DIR),
        )
        stdout, stderr = process.communicate(timeout=MAX_RENDER_TIME_MINUTES * 60)

        result = {
            "status": "success" if process.returncode == 0 else "error",
            "returncode": process.returncode,
            "output_file": str(output_path),
            "stdout": stdout[-5000:] if stdout else "",
            "stderr": stderr[-2000:] if stderr else "",
        }
        if process.returncode == 0:
            logger.info(f"Render SUCCESS: {output_path}")
        else:
            logger.error(f"Render FAILED (code {process.returncode})")
        return result

    except subprocess.TimeoutExpired:
        process.kill()
        logger.error(f"Render TIMEOUT after {MAX_RENDER_TIME_MINUTES} min")
        return {"status": "timeout", "error": "Render timeout"}
    except Exception as e:
        logger.error(f"Render exception: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        if config_path.exists():
            config_path.unlink()


# ============================================================
# MUSIC CATALOG
# ============================================================
def load_music_catalog() -> List[Dict[str, Any]]:
    try:
        if MUSIC_DATA_FILE.exists():
            return json.loads(MUSIC_DATA_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Music catalog load failed: {e}")
    return []


def get_music_for_niche(niche: str) -> List[Dict[str, Any]]:
    catalog = load_music_catalog()
    niche_family = NICHE_FAMILY_MAP.get(niche, "general")
    matching = [m for m in catalog if m.get("niche") == niche_family]
    if not matching:
        matching = [m for m in catalog if m.get("niche") == "general"]
    if not matching:
        matching = catalog
    return matching


# ============================================================
# UI HELPERS
# ============================================================
def _get_music_choices() -> List[str]:
    catalog = load_music_catalog()
    choices = []
    for m in catalog:
        name = m.get("name", m.get("file", "unknown"))
        niche_tag = m.get("niche", "general")
        choices.append(f"{name} [{niche_tag}]")
    return choices if choices else ["auto"]


def get_ui_preset_gallery() -> List[List[Any]]:
    """Generate preset gallery data for Gradio Dataframe."""
    gallery = []
    if PRESETS_AVAILABLE:
        for niche in get_all_niches():
            for preset in get_presets_for_niche(niche):
                gallery.append([
                    get_niche_display_name(niche),
                    preset.preset_number,
                    preset.label,
                    "High" if preset.motion.zoom_max > 1.12 else "Medium" if preset.motion.zoom_max > 1.08 else "Low",
                    preset.description[:80] + "...",
                ])
    return gallery


# ============================================================
# SELF-TEST
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("app_phase1_patch.py — SELF-TEST")
    print("=" * 60)

    # Test 1: Imports
    print(f"\n[1] Presets available: {PRESETS_AVAILABLE}")
    print(f"[2] Brain available:    {BRAIN_AVAILABLE}")

    # Test 2: Niche display names
    print(f"\n[3] Niche display names:")
    for k, v in NICHE_DISPLAY_NAMES.items():
        print(f"    {k:25s} → {v}")

    # Test 3: Fallback detection
    print(f"\n[4] Fallback detection tests:")
    test_texts = [
        ("luxury watches rolex supercar mansion", "luxury_lifestyle"),
        ("ai artificial intelligence robot future technology", "quantum_future"),
        ("crime murder mystery detective suspense thriller", "mystery"),
        ("stoic wisdom discipline philosophy marcus aurelius", "stoic_wisdom"),
        ("interior design home renovation modern kitchen", "interior_design"),
        ("stock market trading finance crypto invest", "finance_simulation"),
        ("random text no keywords here", "default"),
    ]
    passed = 0
    for text, expected in test_texts:
        result = _fallback_niche_detect(text)
        status = "OK" if result == expected else f"FAIL (got {result})"
        if result == expected:
            passed += 1
        print(f"    [{status}] \"{text[:50]}...\" → {result}")
    print(f"    Fallback detection: {passed}/{len(test_texts)} correct")

    # Test 4: analyze_and_get_config
    print(f"\n[5] Pipeline test:")
    try:
        config = analyze_and_get_config(
            content="luxury watches for billionaires rolex patek philippe",
            niche=None,
            preset_number=None,
            video_duration=60.0,
        )
        print(f"    Niche:    {config.get('niche_display', '?')}")
        print(f"    Preset:   #{config.get('preset_number', '?')} - {config.get('preset_label', '?')}")
        print(f"    Clips:    {len(config.get('clips', []))}")
        print(f"    Method:   {config.get('niche_method', '?')}")
        print(f"    Render#:  {config.get('render_count', '?')}")
    except Exception as e:
        print(f"    FAILED: {e}")
        traceback.print_exc()

    # Test 5: Variation (same niche, different render = different config)
    if PRESETS_AVAILABLE:
        print(f"\n[6] Variation test:")
        preset1 = get_preset("default", 1)
        _, z1, _, _, _ = apply_variation(preset1, clip_index=0, render_count=0)
        _, z2, _, _, _ = apply_variation(preset1, clip_index=0, render_count=1)
        _, z3, _, _, _ = apply_variation(preset1, clip_index=3, render_count=0)
        print(f"    render#0 clip#0: zoom={z1}")
        print(f"    render#1 clip#0: zoom={z2} (different from {z1}? {z1 != z2})")
        print(f"    render#0 clip#3: zoom={z3} (different from {z1}? {z1 != z3})")

    # Test 6: Total presets
    if PRESETS_AVAILABLE:
        print(f"\n[7] Total presets: {get_total_preset_count()} across {len(get_all_niches())} niches")

    print("\n" + "=" * 60)
    print("SELF-TEST COMPLETE")
    print("=" * 60)
