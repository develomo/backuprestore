# auto_fix_future_tech.py
# ==========================================================
# PATCH FILE 2 — Fix Future Tech Presets (5-8) 
# for niche_editing_presets.py
# ==========================================================
# Kya karta hai:
#   - _build_future_tech_presets() function dhundta hai
#   - Agar incomplete presets mile (5-8), to fix karta hai
#   - Backup bhi banata hai (.bak)
#
# RUN: python auto_fix_future_tech.py
# ==========================================================

import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Complete Future Tech Presets 5-8 (directly replaces broken ones)
FUTURE_TECH_5_TO_8 = '''    # PRESET 5: "Hologram Display" - 3D/holographic feel, futuristic
    p5 = EditingPreset(
        preset_id=f"{niche}_preset_5",
        preset_number=5, niche=niche,
        label="Hologram Display",
        description="3D holographic interface feel. Float motions, circle transitions, cyan glow aesthetic. Sci-fi UI style.",
        motion=MotionConfig(
            directions=["gentle_float_up","diagonal_soft","gentle_float_down","center_push","left_to_right","right_to_left","slow_pan_left","slow_pan_right"],
            zoom_min=1.058, zoom_max=1.120, zoom_step=0.00055, use_static_contrast=True, static_every_n_clips=6
        ),
        transition=TransitionConfig(
            types=["circleopen","dissolve","wipeleft","rectcrop","circleopen","smoothleft","wiperight","dissolve"],
            min_repeat_gap=6, duration_base=0.30, duration_range=(0.14, 0.42)
        ),
        cut_rhythm=CutRhythmConfig(
            hook_min=1.0, hook_max=1.8, body_min=3.2, body_max=5.8, emphasis_min=5.5, emphasis_max=8.0,
            long_min=4.0, long_max=6.5
        ),
        color=ColorConfig(
            grade_filter="eq=contrast=1.048:saturation=1.045:brightness=0.001",
            temperature_shift=-0.08, vignette_strength=0.025, film_grain_opacity=0.010, sharpness=0.11
        ),
        animation=AnimationConfig(
            styles=["premium_float","gentle_float_up","gentle_float_down","diagonal_soft","left_drift","right_drift","slow_push","soft_reveal"],
            min_repeat_gap=3
        ),
        audio=AudioConfig(voice_volume=1.50, music_volume=0.155, sfx_volume=0.085, target_lufs=-14.0, ducking_strength=0.28),
        variation_seed=1500
    )

    # PRESET 6: "Dark Matrix" - Dark mode, green terminal, code aesthetic
    p6 = EditingPreset(
        preset_id=f"{niche}_preset_6",
        preset_number=6, niche=niche,
        label="Dark Matrix",
        description="Dark terminal/matrix code aesthetic. Green tints, glitch effects, data-stream transitions. Hacker/cyber feel.",
        motion=MotionConfig(
            directions=["right_to_left","bottom_to_top","diagonal_reverse","top_to_bottom","left_to_right","center_push","diagonal_soft","gentle_float_up"],
            zoom_min=1.062, zoom_max=1.128, zoom_step=0.00058, use_static_contrast=False, static_every_n_clips=10
        ),
        transition=TransitionConfig(
            types=["pixelize","rectcrop","wipeup","slideright","pixelize","wipeleft","wipedown","rectcrop"],
            min_repeat_gap=5, duration_base=0.22, duration_range=(0.08, 0.30)
        ),
        cut_rhythm=CutRhythmConfig(
            hook_min=0.7, hook_max=1.5, body_min=2.5, body_max=4.8, emphasis_min=4.0, emphasis_max=6.5,
            long_min=3.0, long_max=5.0
        ),
        color=ColorConfig(
            grade_filter="eq=contrast=1.058:saturation=1.042:brightness=-0.004",
            temperature_shift=-0.07, vignette_strength=0.030, film_grain_opacity=0.018, sharpness=0.14
        ),
        animation=AnimationConfig(
            styles=["hook_punch","mystery_creep","left_drift","right_drift","up_drift","down_drift","diagonal_reverse","diagonal_soft"],
            min_repeat_gap=3
        ),
        audio=AudioConfig(voice_volume=1.48, music_volume=0.165, sfx_volume=0.092, target_lufs=-14.0, ducking_strength=0.32),
        variation_seed=1600
    )

    # PRESET 7: "Future Minimal" - White space, clean, keynote feel
    p7 = EditingPreset(
        preset_id=f"{niche}_preset_7",
        preset_number=7, niche=niche,
        label="Future Minimal",
        description="Future minimal - white space, clean lines, floating UI elements. Apple keynote/product launch feel.",
        motion=MotionConfig(
            directions=["center_push","gentle_float_up","static_hold","slow_pan_right","gentle_float_down","left_to_right","diagonal_soft","static_hold"],
            zoom_min=1.025, zoom_max=1.068, zoom_step=0.00030, use_static_contrast=True, static_every_n_clips=3
        ),
        transition=TransitionConfig(
            types=["smoothleft","fade","smoothright","dissolve","smoothleft","fade","smoothright","dissolve"],
            min_repeat_gap=3, duration_base=0.32, duration_range=(0.18, 0.42)
        ),
        cut_rhythm=CutRhythmConfig(
            hook_min=1.6, hook_max=2.6, body_min=4.5, body_max=7.2, emphasis_min=7.0, emphasis_max=9.5,
            long_min=5.5, long_max=8.0
        ),
        color=ColorConfig(
            grade_filter="eq=contrast=1.025:saturation=1.012:brightness=0.006",
            temperature_shift=-0.01, vignette_strength=0.010, film_grain_opacity=0.008, sharpness=0.13
        ),
        animation=AnimationConfig(
            styles=["documentary_hold","subtle_zoom_in","soft_reveal","left_drift","slow_push","right_drift","static_hold","premium_float"],
            min_repeat_gap=3
        ),
        audio=AudioConfig(voice_volume=1.55, music_volume=0.122, sfx_volume=0.048, target_lufs=-14.0, ducking_strength=0.18),
        variation_seed=1700
    )

    # PRESET 8: "Tech Revolution" - Bold, fast, disruptive
    p8 = EditingPreset(
        preset_id=f"{niche}_preset_8",
        preset_number=8, niche=niche,
        label="Tech Revolution",
        description="Tech revolution style. Bold, fast, disruptive. Startup pitch energy meets sci-fi visuals.",
        motion=MotionConfig(
            directions=["diagonal_reverse","left_to_right","bottom_to_top","center_push","right_to_left","top_to_bottom","diagonal_soft","gentle_float_up"],
            zoom_min=1.068, zoom_max=1.138, zoom_step=0.00065, use_static_contrast=False, static_every_n_clips=11
        ),
        transition=TransitionConfig(
            types=["fadewhite","wipeleft","slideright","pixelize","fadewhite","wiperight","rectcrop","smoothleft"],
            min_repeat_gap=6, duration_base=0.22, duration_range=(0.08, 0.30)
        ),
        cut_rhythm=CutRhythmConfig(
            hook_min=0.6, hook_max=1.3, body_min=2.2, body_max=4.5, emphasis_min=3.5, emphasis_max=6.0,
            long_min=2.8, long_max=4.5
        ),
        color=ColorConfig(
            grade_filter="eq=contrast=1.055:saturation=1.050:brightness=0.000",
            temperature_shift=-0.03, vignette_strength=0.020, film_grain_opacity=0.012, sharpness=0.15
        ),
        animation=AnimationConfig(
            styles=["hook_punch","left_drift","right_drift","up_drift","down_drift","mystery_creep","diagonal_reverse","premium_float"],
            min_repeat_gap=3
        ),
        audio=AudioConfig(voice_volume=1.48, music_volume=0.175, sfx_volume=0.098, target_lufs=-14.0, ducking_strength=0.34),
        variation_seed=1800
    )

    return [p1, p2, p3, p4, p5, p6, p7, p8]'''


def fix_file(filepath):
    """Fix Future Tech preset 5 ke baad ka sab kuch replacement se."""
    path = Path(filepath)
    
    if not path.exists():
        print(f"ERROR: {path} not found!")
        return False

    # --- BACKUP (using shutil.copy for binary-safe copy) ---
    backup_path = str(path) + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(str(path), backup_path)
    print(f"Backup saved: {Path(backup_path).name}")

    # Read as raw bytes, then decode as utf-8
    raw_bytes = path.read_bytes()
    content = raw_bytes.decode("utf-8", errors="replace")

    # Pattern: Find PRESET 5 marker
    preset5_start = content.find('# PRESET 5:')
    if preset5_start == -1:
        print("ERROR: Could not find '# PRESET 5:' marker in Future Tech section")
        return False

    # Find the function return statement after Preset 5
    return_pattern = r'return\s+\[p1,\s*p2,\s*p3,\s*p4'
    return_match = re.search(return_pattern, content[preset5_start:])
    if not return_match:
        print("ERROR: Could not find 'return [p1, p2, p3, p4' after Preset 5")
        return False

    # The broken section is from preset5_start to just before return
    broken_section_end = preset5_start + return_match.start()
    
    # Replace: keep everything before preset5_start, add our fixed code
    before = content[:preset5_start]
    after = content[broken_section_end:]
    
    # Remove old duplicate return from 'after' section
    old_return = content[broken_section_end:preset5_start + return_match.end()]
    after = after.replace(old_return, "")

    new_content = before + FUTURE_TECH_5_TO_8 + after

    # Write back as UTF-8 bytes
    path.write_bytes(new_content.encode("utf-8"))
    print("Future Tech Presets 5-8 REPLACED with complete versions")
    print("   -> Presets fixed: Hologram Display, Dark Matrix, Future Minimal, Tech Revolution")
    
    return True


def validate_fix(filepath):
    """Quick validation after fix."""
    path = Path(filepath)
    raw_bytes = path.read_bytes()
    content = raw_bytes.decode("utf-8", errors="replace")
    
    issues = 0
    
    # Check all 8 Future Tech presets exist
    for i in range(1, 9):
        if f"quantum_future_preset_{i}" not in content:
            print(f"  WARNING: Preset quantum_future_preset_{i} MISSING")
            issues += 1
    
    # Check no incomplete strings
    if 'description="Dark terminal/matrix code aesthetic. Green tints, gl' in content:
        print("  BUG: Dark Matrix description still incomplete!")
        issues += 1
    
    # Check no SyntaxError-level issues
    try:
        compile(content, str(path), 'exec')
        print("  Python compile check: OK")
    except SyntaxError as e:
        print(f"  SYNTAX ERROR: {e}")
        issues += 1

    if issues == 0:
        print("Validation PASSED - All 8 Future Tech presets present and complete!")
    else:
        print(f"{issues} issue(s) found")
    
    return issues


if __name__ == "__main__":
    target = Path(__file__).parent / "niche_editing_presets.py"

    print("=" * 60)
    print("  PATCH: Fix Future Tech Presets 5-8")
    print("  Target: niche_editing_presets.py")
    print("=" * 60)
    print()

    if fix_file(str(target)):
        print()
        issues = validate_fix(str(target))
        
        print()
        print("=" * 60)
        if issues == 0:
            print("  PATCH SUCCESSFUL!")
            print()
            print("  Next steps:")
            print("    1. python auto_fix_presets.py  (fix typos)")
            print("    2. python test_phase1.py       (full validation)")
            print("=" * 60)
        else:
            print("  Patch applied but validation found issues")
            print("  Check above and fix manually if needed")
            print("=" * 60)
    else:
        print()
        print("PATCH FAILED - See errors above")
        sys.exit(1)