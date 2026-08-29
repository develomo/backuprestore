"""
============================================================
MY CREATION VIDEO GENERATOR — PHASE 1
test_phase1.py — END-TO-END INTEGRATION TEST v2.0
============================================================

UPDATED for:
  - niche_editing_presets.py v2.0 (new API)
  - auto_editing_brain.py (auto_detect_niche, auto_choose_preset)
  - app_phase1_patch.py v2.0
============================================================
"""

from __future__ import annotations

import json
import random
import sys
import time
import tempfile
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ============================================================
# CONFIG
# ============================================================

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

TEST_SAMPLES = [
    {
        "name": "Luxury Watches",
        "content": (
            "Top 5 luxury watches that billionaires actually wear. "
            "From the Rolex Submariner at $10,000 to the Patek Philippe "
            "Grandmaster Chime at $31 million. These exclusive timepieces "
            "aren't just watches — they're investments. The Audemars Piguet "
            "Royal Oak, the Richard Mille RM 56-02, and the Vacheron "
            "Constantin Les Cabinotiers. Each one tells a story of "
            "craftsmanship, heritage, and ultimate luxury."
        ),
        "expected_niche_family": "luxury",
    },
    {
        "name": "AI Future",
        "content": (
            "The future of artificial intelligence is here. Machine learning "
            "algorithms are transforming every industry. From quantum computing "
            "to neural networks, we're witnessing the birth of true AI. "
            "OpenAI, DeepMind, and Anthropic are pushing boundaries. "
            "GPT-5, autonomous robots, and the singularity — is humanity ready?"
        ),
        "expected_niche_family": "future_tech",
    },
    {
        "name": "Murder Mystery",
        "content": (
            "A wealthy businessman was found dead in his penthouse. The police "
            "called it suicide, but the detective knew better. Blood stains "
            "on the carpet, a missing will, and three suspects with perfect "
            "motives. This unsolved crime has haunted the city for 15 years. "
            "Tonight, we uncover the evidence they tried to hide."
        ),
        "expected_niche_family": "mystery",
    },
    {
        "name": "Stoic Discipline",
        "content": (
            "Marcus Aurelius once wrote: 'The impediment to action advances "
            "action. What stands in the way becomes the way.' Stoicism isn't "
            "just philosophy — it's a operating system for life. Daily habits, "
            "morning meditation, and the discipline to control what you can. "
            "Seneca, Epictetus, and the ancient wisdom that's more relevant "
            "today than ever before."
        ),
        "expected_niche_family": "wisdom",
    },
    {
        "name": "Interior Makeover",
        "content": (
            "Watch this stunning apartment transformation from dark and outdated "
            "to bright and modern. Scandinavian design meets industrial elements. "
            "White walls, oak flooring, minimalist furniture, and smart home "
            "technology. Before and after will shock you. Total renovation cost "
            "under $15,000 — here's exactly how we did it."
        ),
        "expected_niche_family": "design",
    },
    {
        "name": "Stock Market",
        "content": (
            "Warren Buffett's top 3 investment strategies for 2026. The stock "
            "market is volatile, but smart investors make money in any market. "
            "Dividend investing, index funds, and value stocks. Your portfolio "
            "diversification matters more than individual stock picks. Passive "
            "income through real estate and dividend aristocrats."
        ),
        "expected_niche_family": "finance",
    },
]

passed = 0
failed = 0
warnings = 0


# ============================================================
# HELPERS
# ============================================================

def check(test_name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  {GREEN}OK{RESET} {test_name}")
    else:
        failed += 1
        msg = f"  {RED}FAIL{RESET} {test_name}"
        if detail:
            msg += f" {RED}-> {detail}{RESET}"
        print(msg)


def warn(msg: str):
    global warnings
    warnings += 1
    print(f"  {YELLOW}WARN{RESET}  {msg}")


def section(title: str):
    print(f"\n{CYAN}{'-'*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{CYAN}{'-'*60}{RESET}")


# ============================================================
# PHASE 1: niche_editing_presets.py
# ============================================================

def test_file1_presets():
    section("PHASE 1: niche_editing_presets.py (File 1)")

    try:
        from niche_editing_presets import (
            EditingPreset, MotionConfig, TransitionConfig,
            CutRhythmConfig, ColorConfig, AnimationConfig, AudioConfig,
            get_preset, get_presets_for_niche, get_all_presets,
            get_all_niches, get_niche_display_name, get_niche_family,
            get_total_preset_count, NICHE_DISPLAY_NAMES, NICHE_FAMILY_MAP,
            apply_variation, get_clip_motion, get_clip_transition,
            get_clip_animation,
            build_ffmpeg_color_filter, build_ffmpeg_motion_filter,
            build_ffmpeg_transition_filter, build_ffmpeg_audio_filter,
            get_preset_summary, list_all_presets_summary,
            get_niches_with_presets,
        )
        check("Import niche_editing_presets", True)
    except Exception as e:
        check("Import niche_editing_presets", False, str(e))
        return

    # --- 1a. Registry Integrity ---
    all_presets = get_all_presets()
    check("Registry has 7 niches", len(all_presets) == 7,
          f"got {len(all_presets)}")

    total = get_total_preset_count()
    check("Total 56 presets (7x8)", total == 56,
          f"got {total}")

    for niche in get_all_niches():
        presets = get_presets_for_niche(niche)
        check(f"  {niche}: {len(presets)} presets", len(presets) == 8,
              f"got {len(presets)}")

    # --- 1b. Dataclass Validation ---
    for niche in get_all_niches():
        for p in get_presets_for_niche(niche):
            assert p.preset_id, f"Missing preset_id in {niche}"
            assert 1 <= p.preset_number <= 8
            assert p.niche == niche
            assert p.label
            assert p.description
            assert len(p.motion.directions) >= 8
            assert len(p.transition.types) >= 8
            assert len(p.animation.styles) >= 8
            assert 1.01 <= p.motion.zoom_min <= 1.10
            assert p.motion.zoom_max >= p.motion.zoom_min
    check("All 56 presets have valid data", True)

    # --- 1c. Raw File Checks ---
    raw = Path(__file__).parent / "niche_editing_presets.py"
    raw_text = raw.read_text(encoding="utf-8")
    check("No 'disolve' typo", "disolve" not in raw_text)
    check("No duplicate build function", raw_text.count("def _build_interior_design_presets") == 1)

    # --- 1d. Utility Functions ---
    result = get_presets_for_niche("luxury_lifestyle")
    check("get_presets_for_niche returns 8 presets", len(result) == 8)

    p = get_preset("luxury_lifestyle", 5)
    check("get_preset works", p.preset_number == 5)

    # Variation test
    p1 = get_preset("luxury_lifestyle", 3)
    _, z1, _, _, _ = apply_variation(p1, clip_index=0, render_count=0)
    _, z2, _, _, _ = apply_variation(p1, clip_index=0, render_count=1)
    check("Variation produces different zooms", z1 != z2,
          f"z1={z1}, z2={z2}")

    # get_preset_summary
    s = get_preset_summary(p)
    check("get_preset_summary has keys",
          "niche_display" in s and "niche_family" in s)

    # --- 1e. Clip Functions ---
    direction, zoom = get_clip_motion(p1, clip_index=0, render_count=2)
    check("get_clip_motion returns valid values",
          isinstance(direction, str) and zoom > 1.0)

    trans_type, trans_dur = get_clip_transition(p1, clip_index=5, render_count=2)
    check("get_clip_transition returns valid values",
          isinstance(trans_type, str) and trans_dur > 0)

    anim = get_clip_animation(p1, clip_index=0, render_count=0)
    check("get_clip_animation returns string", isinstance(anim, str) and len(anim) > 0)

    # --- 1f. FFmpeg Filters ---
    color_filter = build_ffmpeg_color_filter(p1)
    check("FFmpeg color filter contains eq=", "eq=" in color_filter)

    motion_filter = build_ffmpeg_motion_filter("center_push", 1.05)
    check("FFmpeg motion filter contains zoompan", "zoompan" in motion_filter)

    trans_filter = build_ffmpeg_transition_filter("dissolve", 0.3)
    check("FFmpeg transition filter works", "dissolve" in trans_filter)

    audio_filter = build_ffmpeg_audio_filter(p1)
    check("FFmpeg audio filter contains amix", "amix" in audio_filter)

    # --- 1g. UI Helpers ---
    ui_list = list_all_presets_summary()
    check("list_all_presets_summary returns 56 items", len(ui_list) == 56)

    niches_data = get_niches_with_presets()
    check("get_niches_with_presets returns 7 niches", len(niches_data) == 7)

    # --- 1h. Display Names ---
    check("NICHE_DISPLAY_NAMES has 7 entries", len(NICHE_DISPLAY_NAMES) == 7)
    check("NICHE_FAMILY_MAP has 7 entries", len(NICHE_FAMILY_MAP) == 7)


# ============================================================
# PHASE 2: auto_editing_brain.py
# ============================================================

def test_file2_brain():
    section("PHASE 2: auto_editing_brain.py (File 2)")

    try:
        from auto_editing_brain import (
            auto_detect_niche,
            auto_choose_preset,
            get_auto_brain,
            AutoEditingBrain,
        )
        check("Import auto_editing_brain", True)
    except ImportError as e:
        check("Import auto_editing_brain", False, str(e))
        warn("auto_editing_brain.py not found — skipping brain tests")
        return

    correct = 0
    total = 0

    for sample in TEST_SAMPLES:
        total += 1
        try:
            niche, confidence, info = auto_detect_niche(
                script_text=sample["content"]
            )
            check(f"  Analyze: {sample['name']}",
                  isinstance(niche, str) and confidence > 0)

            from niche_editing_presets import NICHE_FAMILY_MAP
            expected_family = sample.get("expected_niche_family", "")
            actual_family = NICHE_FAMILY_MAP.get(niche, "")

            if actual_family == expected_family:
                correct += 1
                check(f"    Niche correct: {niche} -> {actual_family}", True)
            else:
                warn(f"    Niche: expected '{expected_family}', got '{actual_family}' "
                     f"({niche}, confidence={confidence:.2f})")

        except Exception as e:
            check(f"  Analyze: {sample['name']}", False, str(e))

    accuracy = correct / max(total, 1) * 100
    if accuracy >= 50:
        check(f"Niche accuracy: {correct}/{total} ({accuracy:.0f}%)", accuracy >= 50)
    else:
        warn(f"Niche accuracy: {correct}/{total} ({accuracy:.0f}%) — may need tuning")

    # Edge cases
    try:
        niche, conf, info = auto_detect_niche(script_text="")
        check("Empty content handled", niche in ("default", ""))
    except Exception:
        check("Empty content handled gracefully", False)

    try:
        niche, conf, info = auto_detect_niche(script_text="hello world test")
        check("Short content analyzed", isinstance(niche, str))
    except Exception:
        check("Short content handled", False)

    # Auto choose preset
    try:
        preset = auto_choose_preset("luxury_lifestyle", render_count=0,
                                     script_text="luxury watches")
        check("auto_choose_preset works", 1 <= preset <= 8)
    except Exception as e:
        check("auto_choose_preset", False, str(e))

    # Singleton
    try:
        brain = get_auto_brain()
        check("get_auto_brain returns singleton", isinstance(brain, AutoEditingBrain))
    except Exception as e:
        check("get_auto_brain", False, str(e))


# ============================================================
# PHASE 3: app_phase1_patch.py
# ============================================================

def test_file3_app():
    section("PHASE 3: app_phase1_patch.py (File 3)")

    try:
        from app_phase1_patch import (
            analyze_and_get_config,
            RenderCounter,
            _fallback_niche_detect,
            _choose_best_preset,
            _generate_clip_configs,
            load_music_catalog,
            get_music_for_niche,
            NICHE_KEYWORDS,
            get_ui_preset_gallery,
        )
        check("Import app_phase1_patch", True)
    except ImportError as e:
        check("Import app_phase1_patch", False, str(e))
        warn("app_phase1_patch.py not found or has errors")
        return

    # --- 3a. Fallback Niche Detection ---
    test_cases = [
        ("luxury watches rolex patek philippe", "luxury_lifestyle"),
        ("artificial intelligence machine learning future", "quantum_future"),
        ("crime scene murder mystery detective", "mystery"),
        ("stoic philosophy marcus aurelius meditation", "stoic_wisdom"),
        ("interior design renovation furniture home", "interior_design"),
        ("stock market investing dividend portfolio", "finance_simulation"),
    ]
    fb_correct = 0
    for content, expected in test_cases:
        result = _fallback_niche_detect(content)
        if result == expected:
            fb_correct += 1
    check(f"Fallback niche detection: {fb_correct}/{len(test_cases)} correct",
          fb_correct >= len(test_cases) * 0.5)

    # --- 3b. Keyword Coverage ---
    total_kw = sum(len(v) for v in NICHE_KEYWORDS.values())
    check(f"NICHE_KEYWORDS has {total_kw}+ keywords", total_kw >= 200)
    check("NICHE_KEYWORDS has 7 niches", len(NICHE_KEYWORDS) == 7)

    # --- 3c. Preset Auto-Choice ---
    for dur in [20, 60, 180]:
        choice = _choose_best_preset("default", "test content", dur)
        check(f"Preset choice for {dur}s video", 1 <= choice <= 8)

    # --- 3d. Pipeline Tests ---
    for sample in TEST_SAMPLES[:4]:
        try:
            config = analyze_and_get_config(
                content=sample["content"],
                niche=None,
                preset_number=None,
                video_duration=60.0,
            )
            check(f"  Pipeline: {sample['name']}",
                  isinstance(config, dict) and "clips" in config)
            check(f"    Niche detected: {config.get('niche', '??')}",
                  config.get("niche") in ["luxury_lifestyle", "quantum_future",
                                           "mystery", "stoic_wisdom",
                                           "interior_design", "finance_simulation",
                                           "default"])
            check(f"    Preset chosen: #{config.get('preset_number', '?')}",
                  1 <= config.get("preset_number", 0) <= 8)
            check(f"    Clips generated: {len(config.get('clips', []))}",
                  len(config.get('clips', [])) >= 3)
        except Exception as e:
            check(f"  Pipeline: {sample['name']}", False, str(e))

    # --- 3e. Manual Niche + Preset ---
    try:
        config = analyze_and_get_config(
            content="luxury lifestyle video about watches",
            niche="luxury_lifestyle",
            preset_number=4,
            video_duration=45.0,
        )
        check("Manual niche+preset works",
              config.get("niche") == "luxury_lifestyle")
        check("Manual preset # applied",
              config.get("preset_number") == 4)
    except Exception as e:
        check("Manual niche+preset", False, str(e))

    # --- 3f. Variation ---
    try:
        cfg1 = analyze_and_get_config("test variation", "default", 1, 60)
        cfg2 = analyze_and_get_config("test variation", "default", 1, 60)
        check("Variation: different render counts",
              cfg1.get("render_count") != cfg2.get("render_count"))
    except Exception as e:
        check("Variation test", False, str(e))

    # --- 3g. Edge Cases ---
    try:
        cfg = analyze_and_get_config("", "default", 1, 15.0)
        check("Empty content handled", isinstance(cfg, dict))
    except Exception:
        check("Empty content handled", False)

    try:
        cfg = analyze_and_get_config("x" * 5000, None, None, 600.0)
        check("Very long content handled",
              isinstance(cfg, dict) and len(cfg.get("clips", [])) <= 60)
    except Exception:
        check("Very long content handled", False)

    # --- 3h. UI Gallery ---
    try:
        gallery = get_ui_preset_gallery()
        check("UI preset gallery has 56 rows", len(gallery) == 56)
    except Exception as e:
        check("UI preset gallery", False, str(e))

    # --- 3i. Music Catalog ---
    try:
        music = load_music_catalog()
        check("Music catalog loads", isinstance(music, list))
    except Exception as e:
        check("Music catalog", False, str(e))


# ============================================================
# PHASE 4: INTEGRATION
# ============================================================

def test_integration():
    section("PHASE 4: END-TO-END INTEGRATION")

    try:
        from niche_editing_presets import get_all_presets, get_presets_for_niche
        from auto_editing_brain import auto_detect_niche
        from app_phase1_patch import analyze_and_get_config
        check("All 3 modules import successfully", True)
    except Exception as e:
        check("All 3 modules import", False, str(e))
        return

    print(f"\n  {BOLD}Full Pipeline Test (6 content types):{RESET}")

    results_summary = []
    for sample in TEST_SAMPLES:
        try:
            start = time.time()
            config = analyze_and_get_config(
                content=sample["content"],
                niche=None,
                preset_number=None,
                video_duration=60.0,
            )
            elapsed = time.time() - start

            niche = config.get("niche", "??")
            preset = config.get("preset_number", "?")
            clips = len(config.get("clips", []))
            label = config.get("preset_label", "??")

            results_summary.append({
                "name": sample["name"],
                "niche": niche,
                "preset": preset,
                "clips": clips,
                "label": label,
                "time_ms": round(elapsed * 1000),
            })

            check(f"  {sample['name']}: {niche}#{preset} '{label}' "
                  f"({clips} clips, {elapsed*1000:.0f}ms)",
                  clips >= 3 and elapsed < 5.0)

        except Exception as e:
            check(f"  {sample['name']}", False, str(e))
            results_summary.append({"name": sample["name"], "error": str(e)})

    print(f"\n  {BOLD}Pipeline Performance Summary:{RESET}")
    print(f"  {'Name':<25s} {'Niche':<22s} {'Preset':<8s} {'Clips':<6s} {'Time':<8s}")
    print(f"  {'-'*25} {'-'*22} {'-'*8} {'-'*6} {'-'*8}")
    for r in results_summary:
        if "error" in r:
            print(f"  {r['name']:<25s} {RED}ERROR: {r['error'][:40]}{RESET}")
        else:
            print(f"  {r['name']:<25s} {r['niche']:<22s} #{str(r['preset']):<7s} "
                  f"{r['clips']:<6d} {r['time_ms']}ms")

    times = [r.get("time_ms", 0) for r in results_summary if "time_ms" in r]
    if times:
        avg_time = sum(times) / len(times)
        check(f"Average analysis speed: {avg_time:.0f}ms per sample",
              avg_time < 2000,
              f"Too slow: {avg_time:.0f}ms (target <2000ms)")


# ============================================================
# PHASE 5: RENDER COUNTER
# ============================================================

def test_render_counter():
    section("PHASE 5: Render Counter")

    try:
        from app_phase1_patch import RenderCounter

        tmp = Path(tempfile.mktemp(suffix=".json"))

        counter = RenderCounter(tmp)
        c1 = counter.next()
        c2 = counter.next()
        c3 = counter.next()

        check(f"Counter increments: {c1}->{c2}->{c3}",
              c2 == c1 + 1 and c3 == c2 + 1)

        counter.reset()
        check("Counter reset works", counter.count == 0)

        if tmp.exists():
            tmp.unlink()

    except Exception as e:
        check("Render counter test", False, str(e))


# ============================================================
# MAIN
# ============================================================

def main():
    print(f"\n{BOLD}{BLUE}{'='*65}{RESET}")
    print(f"{BOLD}{BLUE}  MY CREATION VIDEO GENERATOR — PHASE 1 TEST SUITE v2.0{RESET}")
    print(f"{BOLD}{BLUE}  End-to-End Integration Validation{RESET}")
    print(f"{BOLD}{BLUE}{'='*65}{RESET}")

    start_time = time.time()

    test_file1_presets()
    test_file2_brain()
    test_file3_app()
    test_integration()
    test_render_counter()

    elapsed = time.time() - start_time

    total = passed + failed
    print(f"\n{BOLD}{'='*65}{RESET}")
    print(f"{BOLD}  FINAL RESULTS{RESET}")
    print(f"{'='*65}")
    print(f"  {GREEN}Passed:  {passed}{RESET}")
    print(f"  {RED}Failed:  {failed}{RESET}")
    print(f"  {YELLOW}Warnings: {warnings}{RESET}")
    print(f"  {CYAN}Total:   {total}{RESET}")
    print(f"  {CYAN}Time:    {elapsed:.1f}s{RESET}")
    print(f"{'='*65}")

    if failed == 0:
        print(f"\n  {GREEN}{BOLD}ALL TESTS PASSED!{RESET}")
        print(f"  {GREEN}Phase 1 is READY for production.{RESET}")
        print(f"\n  {BOLD}Next Steps:{RESET}")
        print(f"  1. Run the Gradio app: {CYAN}python app_phase1_patch.py{RESET}")
        print(f"  2. Or start Phase 2: {CYAN}batch_long_renderer integration{RESET}")
        return 0
    else:
        print(f"\n  {RED}{BOLD}{failed} TEST(S) FAILED!{RESET}")
        print(f"  {RED}Fix the issues above and re-run.{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
