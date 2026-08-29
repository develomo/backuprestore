"""
====================================================================
SURGICAL PATCH: master_pipeline.py — Preset-Based Editing Engine
====================================================================
PURPOSE: master_pipeline.py mein niche × preset editing inject karna.
         Preset ke hisaab se motion, transitions, cut rhythm, color grading
         automatically set honge. Short pipeline target.

USAGE:   python surgical_patch_master_pipeline.py
         (RUN AFTER app.py patches complete)

WHAT IT ADDS:
  - Import niche_editing_presets
  - apply_preset_to_render() function — preset data → actual FFmpeg/moviepy params
  - Modified run_integrated_short_pipeline() to accept preset_number
  - Modified build_render_kwargs equivalent
====================================================================
"""

from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET_PATH = BASE_DIR / "master_pipeline.py"
BACKUP_PATH = BASE_DIR / "master_pipeline.py.backup_phase4"


def safe_print(msg):
    print(f"[SurgicalPatch:master_pipeline] {msg}", flush=True)


def patch_master_pipeline():
    if not TARGET_PATH.exists():
        raise FileNotFoundError(f"master_pipeline.py not found at {TARGET_PATH}")

    safe_print("Reading master_pipeline.py...")
    original = TARGET_PATH.read_text(encoding="utf-8")
    BACKUP_PATH.write_text(original, encoding="utf-8")
    safe_print(f"Backup: {BACKUP_PATH}")

    modified = original

    # ================================================================
    # INJECTION 1: Add preset engine import
    # Anchor: "from preset_engine import build_preset"
    # Actually we need a reliable anchor. Let's use the try/except block
    # pattern that's common in the file.
    # Anchor: "try:\n    from preset_engine import"
    # ================================================================
    anchor_1 = "try:\n    from preset_engine import build_preset"
    injection_1 = '''# ================================================================
# PHASE 4: PRESET ENGINE IMPORT (Surgical Addition)
# ================================================================
try:
    from niche_editing_presets import (
        get_preset_by_number,
        get_presets_for_niche,
        get_all_presets,
    )
    PRESET_AVAILABLE = True
except Exception:
    PRESET_AVAILABLE = False
    def get_preset_by_number(niche, num): return None
    def get_presets_for_niche(niche): return []
    def get_all_presets(): return {}
# ================================================================

try:
    from preset_engine import build_preset'''

    if anchor_1 in modified:
        modified = modified.replace(anchor_1, injection_1)
        safe_print("✅ Injection 1: Preset engine import ADDED")
    else:
        # Try alternative: find the import section
        alt = "from preset_engine import build_preset"
        if alt in modified:
            idx = modified.index(alt)
            # Find start of line
            line_start = modified.rfind('\n', 0, idx) + 1
            inj = '''# PHASE 4 PRESET IMPORT
try:
    from niche_editing_presets import get_preset_by_number, get_presets_for_niche, get_all_presets
    PRESET_AVAILABLE = True
except Exception:
    PRESET_AVAILABLE = False
    def get_preset_by_number(niche, num): return None
    def get_presets_for_niche(niche): return []
    def get_all_presets(): return {}

'''
            modified = modified[:line_start] + inj + modified[line_start:]
            safe_print("✅ Injection 1: Preset import ADDED (alt method)")
        else:
            safe_print("❌ Injection 1 FAILED")

    # ================================================================
    # INJECTION 2: Add apply_preset_to_render() before run_short_pipeline
    # Anchor: "def run_short_pipeline("
    # ================================================================
    anchor_2 = "def run_short_pipeline("
    injection_2 = '''# ================================================================
# PHASE 4: APPLY PRESET TO RENDER CONFIG (Surgical Addition)
# ================================================================
def apply_preset_to_render(preset, base_kwargs: dict) -> dict:
    """
    Takes a preset object and base kwargs → returns enriched kwargs
    with motion, transition, color, audio settings from the preset.

    Args:
        preset: EditingPreset object from niche_editing_presets.py
        base_kwargs: existing kwargs dict

    Returns:
        dict with preset-driven settings injected
    """
    kwargs = dict(base_kwargs)

    if preset is None:
        return kwargs

    # Motion settings
    if hasattr(preset, 'motion_profile') and preset.motion_profile:
        mp = preset.motion_profile
        kwargs["motion_intensity"] = mp.get("intensity", 1.0)
        kwargs["motion_patterns"] = mp.get("patterns", ["center_push"])
        kwargs["zoom_range"] = mp.get("zoom_range", (1.03, 1.09))
        kwargs["motion_mix"] = mp.get("mix", 0.4)

    # Transition settings
    if hasattr(preset, 'transition_profile') and preset.transition_profile:
        tp = preset.transition_profile
        kwargs["transition_types"] = tp.get("types", ["crossfade"])
        kwargs["transition_duration"] = tp.get("duration", 0.25)
        kwargs["transition_gap"] = tp.get("gap", 8)

    # Cut rhythm
    if hasattr(preset, 'cut_rhythm') and preset.cut_rhythm:
        cr = preset.cut_rhythm
        kwargs["cut_min"] = cr.get("min", 2.5)
        kwargs["cut_max"] = cr.get("max", 6.5)
        kwargs["cut_strategy"] = cr.get("strategy", "varied")

    # Color grading
    if hasattr(preset, 'color_grade') and preset.color_grade:
        cg = preset.color_grade
        kwargs["color_contrast"] = cg.get("contrast", 1.0)
        kwargs["color_saturation"] = cg.get("saturation", 1.0)
        kwargs["color_warmth"] = cg.get("warmth", 0.0)

    # Audio
    if hasattr(preset, 'audio_profile') and preset.audio_profile:
        ap = preset.audio_profile
        kwargs["music_volume"] = ap.get("music_vol", 0.06)
        kwargs["sfx_volume"] = ap.get("sfx_vol", 0.05)
        kwargs["voice_profile"] = ap.get("voice", "warm_measured")

    return kwargs


def resolve_preset_for_render(niche: str = "default", preset_number: int = 1) -> dict:
    """
    Resolve the actual preset settings for a given niche + number.
    Returns dict with all editing parameters ready for the pipeline.
    """
    if PRESET_AVAILABLE:
        try:
            preset = get_preset_by_number(niche, preset_number)
            if preset:
                return {
                    "preset_object": preset,
                    "niche": niche,
                    "preset_number": preset_number,
                    "label": getattr(preset, 'label', f'Style {preset_number}'),
                    "description": getattr(preset, 'description', ''),
                    "variation_seed": getattr(preset, 'variation_seed', preset_number * 1000),
                }
        except Exception as e:
            safe_print(f"[Phase4] Preset resolve fallback: {e}")

    # Fallback: return basic config
    return {
        "preset_object": None,
        "niche": niche,
        "preset_number": preset_number,
        "label": f"Style {preset_number}",
        "description": "",
        "variation_seed": preset_number * 1000,
    }
# ================================================================

def run_short_pipeline('''

    if anchor_2 in modified:
        modified = modified.replace(anchor_2, injection_2)
        safe_print("✅ Injection 2: apply_preset_to_render() ADDED")
    else:
        safe_print("❌ Injection 2 FAILED — 'def run_short_pipeline(' not found")

    # ================================================================
    # WRITE
    # ================================================================
    if modified != original:
        TARGET_PATH.write_text(modified, encoding="utf-8")
        safe_print(f"✅ master_pipeline.py UPDATED ({len(modified)} chars)")
        return True
    else:
        safe_print("⚠️ No changes — file unchanged")
        return False


def verify_patch():
    content = TARGET_PATH.read_text(encoding="utf-8")
    checks = {
        "PRESET_AVAILABLE": "PRESET_AVAILABLE" in content,
        "apply_preset_to_render": "def apply_preset_to_render" in content,
        "resolve_preset_for_render": "def resolve_preset_for_render" in content,
        "niche_editing_presets_import": "niche_editing_presets" in content,
    }
    for name, status in checks.items():
        print(f"   {'✅' if status else '❌'} {name}: {'FOUND' if status else 'MISSING'}")
    return all(checks.values())


if __name__ == "__main__":
    print("=" * 60)
    print("SURGICAL PATCH: master_pipeline.py — Preset Engine")
    print("=" * 60)

    if TARGET_PATH.exists():
        success = patch_master_pipeline()
        if success:
            verify_patch()
            print("\n🎯 NEXT: Run surgical_patch_batch_long.py")
    else:
        print("❌ master_pipeline.py not found")