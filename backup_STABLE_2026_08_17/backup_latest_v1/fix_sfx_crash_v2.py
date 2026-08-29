#!/usr/bin/env python3
"""
fix_sfx_crash_v2.py
===================
Surgical patch v2: Fixes `sfx` list → Path() crash in batch_long_renderer.py

v1 BUG: old_str wasn't unique — injected into apply_subscribe_overlay_mid() instead of mux_audio_timeline()
v2 FIX: Uses unique docstring context to target ONLY mux_audio_timeline()

Two steps:
  1. Remove the wrongly injected code from apply_subscribe_overlay_mid()
  2. Inject sfx unwrapping correctly into mux_audio_timeline()

Run: python fix_sfx_crash_v2.py
"""

from pathlib import Path

BATCH_FILE = Path("batch_long_renderer.py")


def main():
    print("=" * 60)
    print("fix_sfx_crash_v2.py — Fix sfx list → Path() crash (corrected)")
    print("=" * 60)

    if not BATCH_FILE.exists():
        print(f"ERROR: {BATCH_FILE} not found!")
        print("Run this script from: D:\\My Creation Video Generator\\backup")
        return 1

    content = BATCH_FILE.read_text(encoding="utf-8")
    original = content

    # ── STEP 1: UNDO the wrongly injected code from v1 ──
    # This was accidentally injected into apply_subscribe_overlay_mid()
    wrong_code = (
        '    # FIX: unwrap sfx if passed as list (choose_sfx returns list)\n'
        '    if isinstance(sfx, (list, tuple)):\n'
        '        sfx = next((Path(p) for p in sfx if Path(p).exists()), None)\n'
        '    video = Path(video)'
    )
    restore_code = '    video = Path(video)'

    count = content.count(wrong_code)
    print(f"  Wrong injections found: {count}")

    if count > 0:
        content = content.replace(wrong_code, restore_code)
        # Check if any wrong injection remains
        remaining = content.count(wrong_code)
        if remaining == 0:
            print("  ✓ All wrong injections removed")
        else:
            print(f"  ⚠ {remaining} wrong injections still remain")
    else:
        print("  - No wrong injection found (clean)")

    # ── STEP 2: Inject sfx unwrapping into mux_audio_timeline() ──
    # UNIQUE match — uses the Returns docstring line that's ONLY in mux_audio_timeline
    fix2_old = (
        '    Returns:\n'
        '        Output path with mixed audio\n'
        '    """\n'
        '    video = Path(video)'
    )
    fix2_new = (
        '    Returns:\n'
        '        Output path with mixed audio\n'
        '    """\n'
        '    # FIX: unwrap sfx if passed as list (choose_sfx returns list)\n'
        '    if isinstance(sfx, (list, tuple)):\n'
        '        sfx = next((Path(p) for p in sfx if Path(p).exists()), None)\n'
        '    video = Path(video)'
    )

    if fix2_old in content:
        content = content.replace(fix2_old, fix2_new)
        print("  ✓ FIX applied: sfx list unwrapping in mux_audio_timeline()")
    else:
        print("  ✗ FIX FAILED: unique match not found.")
        print("    Trying alternate match...")

        # Try without the Returns line (shorter context)
        alt_old = (
            '        Output path with mixed audio\n'
            '    """\n'
            '    video = Path(video)'
        )
        alt_new = (
            '        Output path with mixed audio\n'
            '    """\n'
            '    # FIX: unwrap sfx if passed as list (choose_sfx returns list)\n'
            '    if isinstance(sfx, (list, tuple)):\n'
            '        sfx = next((Path(p) for p in sfx if Path(p).exists()), None)\n'
            '    video = Path(video)'
        )
        if alt_old in content:
            content = content.replace(alt_old, alt_new)
            print("  ✓ FIX applied via alternate match")
        else:
            print("  ✗ All matches failed. Manual fix needed.")
            return 1

    if content == original:
        print("")
        print("⚠ No changes were made. File already patched or patterns not found.")
        return 0

    # Write back
    BATCH_FILE.write_text(content, encoding="utf-8")
    print("")
    print("=" * 60)
    print("DONE — batch_long_renderer.py patched successfully!")
    print("=" * 60)
    print("")
    print("Now run: streamlit run app.py")
    return 0


if __name__ == "__main__":
    exit(main())