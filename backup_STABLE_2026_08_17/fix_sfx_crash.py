#!/usr/bin/env python3
"""
fix_sfx_crash.py
================
Surgical patch: Fixes `sfx` list → Path() crash in batch_long_renderer.py

Bug: `choose_sfx()` in safe_long_video_polished.py returns a LIST of file paths,
but `mux_audio_timeline()` in batch_long_renderer.py expects a SINGLE path string.
When it calls `Path(sfx)` on a list → TypeError crash.

Fix: Add list unwrapping at the top of `mux_audio_timeline()` so that if sfx
is a list/tuple, it takes the first valid file. Surgical addition — no code removed.

Run: python fix_sfx_crash.py
"""

import re
from pathlib import Path

BATCH_FILE = Path("batch_long_renderer.py")

def main():
    print("=" * 60)
    print("fix_sfx_crash.py — Fix sfx list → Path() crash")
    print("=" * 60)

    if not BATCH_FILE.exists():
        print(f"ERROR: {BATCH_FILE} not found!")
        print("Run this script from: D:\\My Creation Video Generator\\backup")
        return 1

    content = BATCH_FILE.read_text(encoding="utf-8")
    lines = content.splitlines()

    # ── FIX 1: mux_audio_timeline — unwrap sfx list before Path() call ──
    # Target: insert after docstring closing """ and before "video = Path(video)"
    # Lines ~2837-2838

    fix1_old = '    """\n    video = Path(video)'
    fix1_new = (
        '    """\n'
        '    # FIX: unwrap sfx if passed as list (choose_sfx returns list)\n'
        '    if isinstance(sfx, (list, tuple)):\n'
        '        sfx = next((Path(p) for p in sfx if Path(p).exists()), None)\n'
        '    video = Path(video)'
    )

    if fix1_old in content:
        content = content.replace(fix1_old, fix1_new)
        print("✓ FIX 1 applied: sfx list unwrapping in mux_audio_timeline()")
    else:
        print("⚠ FIX 1: old_str NOT FOUND. Checking alternatives...")
        # Try with different indentation or spacing
        alt_old = '"""\n    video = Path(video)'
        if alt_old in content:
            content = content.replace(alt_old,
                '"""\n'
                '    # FIX: unwrap sfx if passed as list (choose_sfx returns list)\n'
                '    if isinstance(sfx, (list, tuple)):\n'
                '        sfx = next((Path(p) for p in sfx if Path(p).exists()), None)\n'
                '    video = Path(video)')
            print("✓ FIX 1 applied (alternate match)")
        else:
            print("✗ FIX 1 FAILED: Could not find insertion point.")
            print("  Please check lines ~2837-2838 of batch_long_renderer.py")
            return 1

    # Write back
    BATCH_FILE.write_text(content, encoding="utf-8")
    print("")
    print("=" * 60)
    print("DONE — batch_long_renderer.py patched successfully!")
    print("=" * 60)
    print("")
    print("Now run your app: streamlit run app.py")
    return 0

if __name__ == "__main__":
    exit(main())