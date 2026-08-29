# auto_fix_presets.py
# ==========================================================
# AUTO-FIX for niche_editing_presets.py
# Fix 1: "disolve" → "dissolve" (typo)
# Fix 2: Interior Preset 7 incomplete code replace
# Fix 3: Duplicate incomplete get_clip_transition delete
# ==========================================================

import re
import sys
from pathlib import Path

# Complete Interior Preset 7 replacement
INTERIOR_PRESET_7_FIX = """    EditingPreset(preset_id="interior_design_preset_7", preset_number=7, niche="interior_design",
        label="Bohemian Dream", variation_seed=4700,
        description="Eclectic bohemian style. Colorful, creative transitions, artistic flow. Maximalist aesthetic.",
        motion=_m(["diagonal_soft","gentle_float_up","diagonal_reverse","gentle_float_down",
                    "slow_pan_right","center_push","left_to_right","right_to_left"],
                   zoom_min=1.038, zoom_max=1.092, zoom_step=0.00042, static_every=5),
        transition=_t(["dissolve","fade","smoothleft","circleopen","dissolve","fade","smoothright","circleclose"],
                      gap=6, dur_base=0.32, dur_lo=0.16, dur_hi=0.44),
        cut_rhythm=_c(1.2,2.2, 3.8,6.5, 6.0,9.0, 4.5,7.2),
        color=_g("eq=contrast=1.028:saturation=1.035:brightness=0.003", 0.04, 0.018, 0.012, 0.07),
        animation=_a(["premium_float","diagonal_soft","gentle_float_up","left_drift","right_drift","soft_reveal","subtle_zoom_in","slow_push"]),
        audio=_au(1.52, 0.138, 0.052, duck=0.20)),"""


def fix_file(filepath: str) -> int:
    """Fix all 3 issues. Returns number of fixes applied."""
    path = Path(filepath)
    original = path.read_text(encoding="utf-8")
    content = original
    fixes = 0

    # -------------------------------------------------------
    # FIX 1: "disolve" → "dissolve" (typo)
    # -------------------------------------------------------
    if "disolve" in content:
        count = content.count("disolve")
        content = content.replace("disolve", "dissolve")
        print(f"✅ FIX 1: Replaced 'disolve' → 'dissolve' ({count} occurrence(s))")
        fixes += 1
    else:
        print("⚪ FIX 1: No 'disolve' typo found — already correct")

    # -------------------------------------------------------
    # FIX 2: Interior Preset 7 incomplete → complete
    # -------------------------------------------------------
    # Pattern: finds the broken Interior Preset 7 entry
    pattern_7_broken = r'EditingPreset\(preset_id="interior_design_preset_7".*?(?=\n\s{4}EditingPreset\()'
    match = re.search(pattern_7_broken, content, re.DOTALL)
    if match:
        broken_block = match.group(0)
        if "left_to" in broken_block and len(broken_block.splitlines()) < 25:
            # It's the broken one — replace it
            content = content.replace(broken_block, INTERIOR_PRESET_7_FIX)
            print("✅ FIX 2: Replaced incomplete Interior Preset 7 with complete version")
            fixes += 1
        else:
            print("⚪ FIX 2: Interior Preset 7 looks complete — skipped")
    else:
        print("⚪ FIX 2: Interior Preset 7 pattern not found — check manually")

    # -------------------------------------------------------
    # FIX 3: Remove duplicate incomplete get_clip_transition
    # -------------------------------------------------------
    # The incomplete one looks like:
    # def get_clip_transition(niche: str, preset_number: int, clip_index: int,
    #                          render_count:
    # Followed IMMEDIATELY by the complete one
    pattern_incomplete = r'(def get_clip_transition\(niche: str, preset_number: int, clip_index: int,\s*\n\s*render_count:\s*\n)(def get_clip_transition)'
    match3 = re.search(pattern_incomplete, content)
    if match3:
        # Replace: keep only the second complete one
        content = content.replace(match3.group(0), match3.group(2))
        print("✅ FIX 3: Removed duplicate incomplete get_clip_transition definition")
        fixes += 1
    else:
        print("⚪ FIX 3: No duplicate incomplete get_clip_transition found — skipping")

    # -------------------------------------------------------
    # SAVE
    # -------------------------------------------------------
    if content != original:
        path.write_text(content, encoding="utf-8")
        print(f"\n{'='*60}")
        print(f"  💾 SAVED: {path.name} ({fixes} fixes applied)")
        print(f"{'='*60}")
    else:
        print(f"\n⚪ No changes needed — file already clean")

    return fixes


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    target = Path(__file__).parent / "niche_editing_presets.py"

    if not target.exists():
        print(f"❌ ERROR: {target} not found!")
        sys.exit(1)

    print(f"🔧 Fixing: {target}")
    print("=" * 60)
    fix_file(str(target))
    print("\n🎉 Done! Now run: test_presets.py")