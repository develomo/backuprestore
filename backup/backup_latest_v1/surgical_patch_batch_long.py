"""
====================================================================
SURGICAL PATCH: batch_long_renderer.py — FIXED (12 Motions)
====================================================================
FIX: Previous version ka MOTION_CANVAS anchor match nahi hua.
     Ye version broader anchor use karta hai.

USAGE: python surgical_patch_batch_long.py
====================================================================
"""

from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET_PATH = BASE_DIR / "batch_long_renderer.py"
BACKUP_PATH = BASE_DIR / "batch_long_renderer.py.backup_phase4_v2"


def safe_print(msg):
    print(f"[BatchLong-FIXED] {msg}", flush=True)


def patch_batch_long():
    if not TARGET_PATH.exists():
        raise FileNotFoundError(f"batch_long_renderer.py not found at {TARGET_PATH}")

    safe_print("Reading batch_long_renderer.py...")
    original = TARGET_PATH.read_text(encoding="utf-8")
    BACKUP_PATH.write_text(original, encoding="utf-8")
    safe_print(f"Backup: {BACKUP_PATH}")

    modified = original
    changes = 0

    # ================================================================
    # INJECTION 1: Add 5 NEW motion directions
    # Strategy: Find "MOTION_CANVAS = OrderedDict([" ke baad wali
    # closing bracket "])" — usse pehle insert karo
    # ================================================================
    # Find the MOTION_CANVAS dict closing
    motion_canvas_start = modified.find("MOTION_CANVAS = OrderedDict([")
    if motion_canvas_start > 0:
        # Find the matching "])" — this is the dict close
        # Search for "    ])" which closes the OrderedDict
        closing_marker = "\n    ])"
        close_pos = modified.find(closing_marker, motion_canvas_start)
        if close_pos > 0:
            # Insert new motions BEFORE the closing
            new_motions = """
        # PHASE 4: 5 NEW MOTION DIRECTIONS (Surgical Addition)
        ("top_right_diag",   ("iw-iw/zoom",                   "0")),
        ("bottom_left_diag", ("0",                            "ih-ih/zoom")),
        ("gentle_float_up",  ("(iw-iw/zoom)*0.35",            "ih*0.15-ih/zoom*0.5")),
        ("gentle_float_down",("(iw-iw/zoom)*0.65",            "ih*0.85-ih/zoom*0.5")),
        ("static_hold",      ("(iw-iw/zoom)/2",               "(ih-ih/zoom)/2")),"""
            modified = modified[:close_pos] + new_motions + modified[close_pos:]
            changes += 1
            safe_print("✅ Injection 1: 5 NEW motion directions ADDED (total 12)")
        else:
            safe_print("⚠️ MOTION_CANVAS closing bracket not found")
    else:
        safe_print("⚠️ MOTION_CANVAS not found — trying alternative search...")
        # Alternative: find "bottom_sweep" line and insert after
        if "bottom_sweep" in modified:
            idx = modified.rindex("bottom_sweep", 0, motion_canvas_start + 500 if motion_canvas_start > 0 else len(modified))
            # Find end of that line
            line_end = modified.index("\n", idx)
            new_motions_alt = """
        # PHASE 4: 5 NEW MOTION DIRECTIONS (Surgical Addition)
        ("top_right_diag",   ("iw-iw/zoom",                   "0")),
        ("bottom_left_diag", ("0",                            "ih-ih/zoom")),
        ("gentle_float_up",  ("(iw-iw/zoom)*0.35",            "ih*0.15-ih/zoom*0.5")),
        ("gentle_float_down",("(iw-iw/zoom)*0.65",            "ih*0.85-ih/zoom*0.5")),
        ("static_hold",      ("(iw-iw/zoom)/2",               "(ih-ih/zoom)/2")),"""
            modified = modified[:line_end + 1] + new_motions_alt + modified[line_end + 1:]
            changes += 1
            safe_print("✅ Injection 1 alt: 5 NEW motions ADDED")
        else:
            safe_print("❌ Injection 1 FAILED — cannot find motion definitions")

    # ================================================================
    # INJECTION 2: Add preset import at module top
    # ================================================================
    marker2 = "from __future__ import annotations"
    if marker2 in modified and "BATCH_PRESET_AVAILABLE" not in modified:
        preset_import = """# PHASE 4: PRESET ENGINE IMPORT (Surgical)
try:
    from niche_editing_presets import get_preset_by_number
    BATCH_PRESET_AVAILABLE = True
except Exception:
    BATCH_PRESET_AVAILABLE = False
    def get_preset_by_number(niche, num): return None

"""
        modified = modified.replace(
            "from __future__ import annotations",
            preset_import + "from __future__ import annotations"
        )
        changes += 1
        safe_print("✅ Injection 2: Preset import ADDED")
    elif "BATCH_PRESET_AVAILABLE" in modified:
        safe_print("✅ Injection 2: Already present (skip)")
    else:
        safe_print("⚠️ Injection 2: marker not found")

    # ================================================================
    # INJECTION 3: Add set_preset() to VariationIntelligence
    # ================================================================
    marker3 = "def pick_motion_direction(self, clip_index, clip_duration):"
    if marker3 in modified and "def set_preset(self" not in modified:
        set_preset_method = """    # ============================================================
    # PHASE 4: PRESET CONFIGURATION (Surgical Addition)
    # ============================================================
    def set_preset(self, preset_number=1, preset_label="Style 1"):
        self._preset_number = preset_number
        self._preset_label = preset_label
        if preset_number <= 2:
            self._energy_bias = "low"
        elif preset_number <= 4:
            self._energy_bias = "medium"
        elif preset_number <= 6:
            self._energy_bias = "high"
        else:
            self._energy_bias = "extreme"
        self._color_temp = 1.0 + (preset_number - 4) * 0.02
    # ============================================================

    def pick_motion_direction(self, clip_index, clip_duration):"""
        modified = modified.replace(marker3, set_preset_method)
        changes += 1
        safe_print("✅ Injection 3: set_preset() method ADDED")
    elif "def set_preset(self" in modified:
        safe_print("✅ Injection 3: Already present (skip)")
    else:
        safe_print("⚠️ Injection 3: pick_motion_direction not found")

    # ================================================================
    # WRITE
    # ================================================================
    if changes > 0:
        TARGET_PATH.write_text(modified, encoding="utf-8")
        safe_print(f"✅ batch_long_renderer.py UPDATED ({changes} injections, {len(modified)} chars)")
        return True
    else:
        safe_print("⚠️ No changes made")
        return False


def verify():
    content = TARGET_PATH.read_text(encoding="utf-8")
    checks = {
        "BATCH_PRESET_AVAILABLE": "BATCH_PRESET_AVAILABLE" in content,
        "set_preset_method": "def set_preset" in content,
        "12_motions": "static_hold" in content and "gentle_float_up" in content,
    }
    for name, ok in checks.items():
        print(f"   {'✅' if ok else '❌'} {name}: {'FOUND' if ok else 'MISSING'}")
    return all(checks.values())


if __name__ == "__main__":
    print("=" * 60)
    print("SURGICAL PATCH: batch_long_renderer.py (FIXED)")
    print("=" * 60)
    if patch_batch_long():
        print("\n📋 Verification:")
        verify()