"""
====================================================================
PATCH 1: safe_long_video_polished.py — Preset Engine Injection
====================================================================
PURPOSE: Long video pipeline mein bhi niche × preset editing inject karna.
         Ab tak sirf master_pipeline (SHORT) mein tha.

USAGE: python patch1_long_preset_injection.py
====================================================================
"""

from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET = BASE_DIR / "safe_long_video_polished.py"
BACKUP = BASE_DIR / "safe_long_video_polished.py.backup_patch1"


def safe_print(msg):
    print(f"[Patch1:LongPreset] {msg}", flush=True)


def inject():
    if not TARGET.exists():
        raise FileNotFoundError(f"{TARGET} not found")

    safe_print("Reading safe_long_video_polished.py...")
    original = TARGET.read_text(encoding="utf-8")
    BACKUP.write_text(original, encoding="utf-8")
    modified = original
    changes = 0

    # ================================================================
    # INJECTION 1: Add preset engine import at the top
    # Anchor: "from pathlib import Path" (second instance after imports)
    # ================================================================
    marker1 = "ROOT=Path(__file__).resolve().parent"
    if marker1 in modified and "PRESET_AVAILABLE_LONG" not in modified:
        preset_import = """# ============================================================
# PATCH 1: PRESET ENGINE IMPORT (Surgical Addition)
# ============================================================
try:
    from niche_editing_presets import (
        get_preset_by_number, get_presets_for_niche, get_all_presets
    )
    from master_pipeline import apply_preset_to_render, resolve_preset_for_render
    PRESET_AVAILABLE_LONG = True
except Exception:
    PRESET_AVAILABLE_LONG = False
    def get_preset_by_number(niche, num): return None
    def get_presets_for_niche(niche): return []
    def get_all_presets(): return {}
    def apply_preset_to_render(preset, kwargs): return kwargs
    def resolve_preset_for_render(niche="default", preset_number=1): return {"preset_object":None,"niche":niche,"preset_number":preset_number}
# ============================================================

ROOT=Path(__file__).resolve().parent"""
        modified = modified.replace(marker1, preset_import)
        changes += 1
        safe_print("✅ Injection 1: Preset engine import ADDED")
    else:
        safe_print("⚠️ Injection 1: Already present or marker not found")

    # ================================================================
    # INJECTION 2: Add preset resolution in run_integrated_long_pipeline
    # Anchor: "preset=dict(preset_overrides or {})"
    # Replace to add preset number extraction
    # ================================================================
    marker2 = "    preset=dict(preset_overrides or {})"
    if marker2 in modified:
        injection2 = """    # PATCH 1: Extract preset_number from kwargs for long pipeline
    preset_number = int(kwargs.get("preset_number", 1))
    preset_label = str(kwargs.get("preset_label", "Style 1"))
    preset=dict(preset_overrides or {})

    # PATCH 1: Resolve preset for long video editing
    if PRESET_AVAILABLE_LONG:
        try:
            resolved = resolve_preset_for_render(niche=niche, preset_number=preset_number)
            if resolved.get("preset_object"):
                preset["_preset_obj"] = resolved["preset_object"]
                preset["_preset_number"] = preset_number
                preset["_preset_label"] = preset_label
                preset["_variation_seed"] = resolved.get("variation_seed", preset_number * 1000)
        except Exception as e:
            safe_print(f"[SafeLongPreset] Preset resolve skipped: {e}")"""
        modified = modified.replace(marker2, injection2)
        changes += 1
        safe_print("✅ Injection 2: Preset resolution in long pipeline ADDED")
    else:
        safe_print("⚠️ Injection 2: marker not found")

    # ================================================================
    # INJECTION 3: Pass preset_number to render_long_batch_memory call
    # Already passes preset_overrides — we just ensure it flows through
    # ================================================================
    marker3 = "render_long_batch_memory(voice_path=voice"
    if marker3 in modified:
        injection3 = """        # PATCH 1: Inject preset info into batch_long_renderer
        if PRESET_AVAILABLE_LONG and preset.get("_preset_obj"):
            preset_overrides_local = dict(preset)
            preset_overrides_local["_preset_number"] = preset.get("_preset_number", 1)
        else:
            preset_overrides_local = preset"""
        modified = modified.replace(marker3, injection3 + "\n        " + marker3)
        changes += 1
        safe_print("✅ Injection 3: Preset overrides passed to batch renderer ADDED")
    else:
        safe_print("⚠️ Injection 3: render_long_batch_memory call not found")

    # ================================================================
    # INJECTION 4: Add grain overlay flag to preset for long videos
    # ================================================================
    marker4 = '"force_final_aspect_ratio":"16:9"'
    if marker4 in modified:
        grain_injection = ', "film_grain_enabled": True, "film_grain_opacity": 0.03, "sfx_cut_sync": True'
        # Find the last occurrence in the long preset dict
        last_idx = modified.rfind(marker4)
        if last_idx > 0:
            insert_pos = last_idx + len(marker4)
            modified = modified[:insert_pos] + grain_injection + modified[insert_pos:]
            changes += 1
            safe_print("✅ Injection 4: Film grain + SFX flags ADDED to long preset")
    else:
        safe_print("⚠️ Injection 4: preset dict marker not found")

    # ================================================================
    # WRITE
    # ================================================================
    if changes > 0:
        TARGET.write_text(modified, encoding="utf-8")
        safe_print(f"✅ safe_long_video_polished.py UPDATED ({changes} injections, {len(modified)} chars)")
        return True
    safe_print("⚠️ No changes made")
    return False


def verify():
    content = TARGET.read_text(encoding="utf-8")
    for check in ["PRESET_AVAILABLE_LONG", "resolve_preset_for_render", "film_grain_enabled", "sfx_cut_sync"]:
        print(f"   {'✅' if check in content else '❌'} {check}: {'FOUND' if check in content else 'MISSING'}")


if __name__ == "__main__":
    print("=" * 60)
    print("PATCH 1: safe_long_video_polished.py — Preset Injection")
    print("=" * 60)
    inject()
    print("\n📋 Verification:")
    verify()