# test_presets.py
# ==========================================================
# COMPLETE VALIDATION TEST for niche_editing_presets.py
# ==========================================================

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}  → {detail}")

print("=" * 65)
print("  NICHE EDITING PRESETS — COMPLETE VALIDATION")
print("=" * 65)

# --- TEST 1: IMPORT ---
print("\n📦 TEST 1: Import niche_editing_presets...")
try:
    from niche_editing_presets import (
        EditingPreset, MotionConfig, TransitionConfig, CutRhythmConfig,
        ColorConfig, AnimationConfig, AudioConfig,
        PRESET_REGISTRY, NICHE_DISPLAY_NAMES,
        get_presets_for_niche, get_preset_by_number,
        get_preset_with_variation, get_preset_summary,
        get_clip_motion, get_clip_transition, get_clip_color_grade,
        get_audio_config, get_animation_for_clip,
        get_motion_filter_for_ffmpeg, list_all_presets_for_ui,
    )
    check("Import successful", True)
except Exception as e:
    check("Import successful", False, str(e))
    sys.exit(1)

# --- TEST 2: 7 NICHES x 8 PRESETS = 56 ---
print("\n📊 TEST 2: Registry integrity (7 niches × 8 presets = 56 total)...")
expected_niches = {
    "luxury_lifestyle", "quantum_future", "mystery",
    "stoic_wisdom", "interior_design", "finance_simulation", "default"
}
actual_niches = set(PRESET_REGISTRY.keys())
check("All 7 niches present", actual_niches == expected_niches,
      "Missing: " + str(expected_niches - actual_niches) + ", Extra: " + str(actual_niches - expected_niches))

total = 0
all_8 = True
for niche in expected_niches:
    count = len(PRESET_REGISTRY[niche])
    if count != 8:
        all_8 = False
        check(niche + " has 8 presets", False, "has " + str(count))
    total += count
check("All niches have exactly 8 presets", all_8)
check("Total 56 presets", total == 56, "got " + str(total))

# --- TEST 3: NO TYPOS ---
print("\n🔍 TEST 3: No typos in raw file...")
raw = Path(__file__).parent / "niche_editing_presets.py"
raw_text = raw.read_text(encoding="utf-8")
check("No 'disolve' typo", "disolve" not in raw_text)
check("No 'fadeblak' typo", "fadeblak" not in raw_text)
check("No 'smoothlef' typo", "smoothlef" not in raw_text)

count_id7 = raw_text.count('preset_id="interior_design_preset_7"')
check("No 'preset_id' duplicate", count_id7 == 1, "Found " + str(count_id7) + " times")

check("No incomplete 'render_count:' line", 'render_count:\n' not in raw_text)

# --- TEST 4: PRESET IDs MATCH NICHE ---
print("\n🏷️  TEST 4: All preset IDs match their niche...")
all_match = True
for niche, presets in PRESET_REGISTRY.items():
    for p in presets:
        if not p.preset_id.startswith(niche):
            all_match = False
            check(p.preset_id + " starts with " + niche, False)
check("All 56 preset IDs match their niche", all_match)

# --- TEST 5: DISPLAY NAMES ---
print("\n📛 TEST 5: Display names present...")
check("All 7 display names", len(NICHE_DISPLAY_NAMES) == 7)

# --- TEST 6: PRESET SUMMARY ---
print("\n📋 TEST 6: get_preset_summary() for all presets...")
all_ok = True
for niche, presets in PRESET_REGISTRY.items():
    for p in presets:
        summary = get_preset_summary(niche, p.preset_number)
        if not all(k in summary for k in ("label", "energy", "cut_rhythm_body")):
            all_ok = False
            check("Summary for " + p.preset_id, False)
            break
    if not all_ok:
        break
check("All 56 preset summaries valid", all_ok)

# --- TEST 7: NICHE RESOLUTION ---
print("\n🗺️  TEST 7: get_presets_for_niche() resolution...")
tests = [
    ("luxury_lifestyle", "luxury_lifestyle"),
    ("quantum_future", "quantum_future"),
    ("mystery", "mystery"),
    ("stoic_wisdom", "stoic_wisdom"),
    ("interior_design", "interior_design"),
    ("finance_simulation", "finance_simulation"),
    ("default", "default"),
    ("auto", "default"),
    ("crypto", "finance_simulation"),
    ("ai", "quantum_future"),
    ("tech", "quantum_future"),
    ("business", "finance_simulation"),
    ("unknown", "default"),
    ("LUXURY_LIFESTYLE", "luxury_lifestyle"),
]
all_resolved = True
for input_niche, expected_niche in tests:
    result = get_presets_for_niche(input_niche)
    actual = result[0].niche
    if actual != expected_niche:
        all_resolved = False
        check("'" + input_niche + "' → " + expected_niche, False, "got " + actual)
check("All 14 niche resolutions correct", all_resolved)

# --- TEST 8: VARIATION ---
print("\n🎲 TEST 8: get_preset_with_variation() uniqueness...")
variations = []
for nc in range(5):
    vp = get_preset_with_variation("luxury_lifestyle", 4, render_count=nc)
    variations.append((vp.motion.zoom_min, vp.motion.zoom_max, vp.transition.duration_base))
unique_vars = len(set(variations))
check("Variation produces uniqueness (" + str(unique_vars) + "/5 unique)", unique_vars >= 2,
      "All 5 identical — variation not working")

# --- TEST 9: CLIP FUNCTIONS ---
print("\n🎬 TEST 9: get_clip_motion / get_clip_transition / get_clip_color_grade...")
m = get_clip_motion("luxury_lifestyle", 1, clip_index=0, render_count=2)
check("get_clip_motion returns dict", isinstance(m, dict))
check("get_clip_motion has keys", all(k in m for k in ("zoom_min","zoom_max","step","direction")))

t = get_clip_transition("luxury_lifestyle", 1, clip_index=0, render_count=2)
check("get_clip_transition returns dict", isinstance(t, dict))
check("get_clip_transition has keys", all(k in t for k in ("transition","duration","index","is_chapter")))

c = get_clip_color_grade("luxury_lifestyle", 1, render_count=2)
check("get_clip_color_grade returns dict", isinstance(c, dict))
check("get_clip_color_grade has keys", all(k in c for k in ("grade_filter","grade_eq_only","vignette","grain","sharpness")))

# --- TEST 10: AUDIO ---
print("\n🔊 TEST 10: get_audio_config()...")
a = get_audio_config("luxury_lifestyle", 1, render_count=0)
check("get_audio_config returns dict", isinstance(a, dict))
check("get_audio_config has keys", all(k in a for k in ("voice_volume","music_volume","sfx_volume","target_lufs")))

# --- TEST 11: ANIMATION ---
print("\n✨ TEST 11: get_animation_for_clip()...")
anim_hook = get_animation_for_clip("luxury_lifestyle", 1, clip_index=0, section="hook")
anim_body = get_animation_for_clip("luxury_lifestyle", 1, clip_index=1, section="body")
anim_end = get_animation_for_clip("luxury_lifestyle", 1, clip_index=10, section="ending")
check("Hook animation is string", isinstance(anim_hook, str))
check("Body animation is string", isinstance(anim_body, str))
check("Ending animation is string", isinstance(anim_end, str))

# --- TEST 12: FFMPEG FILTER ---
print("\n🎞️  TEST 12: get_motion_filter_for_ffmpeg()...")
ff = get_motion_filter_for_ffmpeg("luxury_lifestyle", 1, clip_index=0, render_count=0,
                                    video_width=854, video_height=480, fps=24)
check("Returns string", isinstance(ff, str))
check("Contains zoompan", "zoompan" in ff)
check("Contains scale", "scale=" in ff)
check("Contains crop", "crop=" in ff)
check("Contains eq=", "eq=" in ff)
check("Contains unsharp", "unsharp" in ff)

# --- TEST 13: UI LIST ---
print("\n🖥️  TEST 13: list_all_presets_for_ui()...")
ui_list = list_all_presets_for_ui()
check("Returns 56 items", len(ui_list) == 56, "got " + str(len(ui_list)))
check("Each has required keys", all(
    all(k in item for k in ("niche","niche_display","number","label","description","preset_id"))
    for item in ui_list
))

# --- TEST 14: DATACLASS INSTANTIATION ---
print("\n🏗️  TEST 14: Direct dataclass instantiation...")
try:
    p = EditingPreset(
        preset_id="test_preset_1", preset_number=1, niche="test",
        label="Test", description="Test preset",
        variation_seed=9999
    )
    check("EditingPreset created", True)
    d = p.to_dict()
    check("to_dict() works", isinstance(d, dict) and "preset_id" in d)
except Exception as e:
    check("EditingPreset creation", False, str(e))

# ============================================================
print("\n" + "=" * 65)
print("  RESULTS: " + str(passed) + " PASSED / " + str(failed) + " FAILED / " + str(passed + failed) + " TOTAL")
if failed == 0:
    print("  🎉 ALL TESTS PASSED — File 1 is 100% PERFECT!")
else:
    print("  ⚠️  " + str(failed) + " test(s) FAILED — check above")
print("=" * 65)
sys.exit(0 if failed == 0 else 1)
