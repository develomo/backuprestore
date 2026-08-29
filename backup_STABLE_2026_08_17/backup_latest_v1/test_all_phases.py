"""
====================================================================
PHASE 4-6: COMPLETE INTEGRATION TEST (v2 — Updated Checks)
====================================================================
USAGE: python test_all_phases.py
====================================================================
"""

import sys
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).parent
PASSED = 0
FAILED = 0


def test(name, condition):
    global PASSED, FAILED
    if condition:
        print(f"   ✅ {name}")
        PASSED += 1
    else:
        print(f"   ❌ {name}")
        FAILED += 1


def check_file(path, name):
    if Path(path).exists():
        test(f"File exists: {name}", True)
        return True
    else:
        test(f"File exists: {name}", False)
        return False


def check_in_file(path, text, name):
    try:
        content = Path(path).read_text(encoding="utf-8")
        test(name, text in content)
        return text in content
    except Exception:
        test(name, False)
        return False


def main():
    global PASSED, FAILED

    print("=" * 60)
    print("PHASE 4-6 COMPLETE INTEGRATION TEST (v2)")
    print(f"Directory: {BASE_DIR}")
    print("=" * 60)

    # ---- FILES CHECK ----
    print("\n📁 File Existence:")
    files = ["app.py", "master_pipeline.py", "batch_long_renderer.py",
             "voice_humanization_orchestrator.py", "audio_engine.py",
             "caption_engine.py", "niche_editing_presets.py",
             "auto_edit_intelligence.py", "content_analyzer.py",
             "scene_detection_engine.py", "edit_decision_engine.py"]
    for f in files:
        check_file(BASE_DIR / f, f)

    # ---- PHASE 4: APP.PY ----
    print("\n📋 Phase 4: app.py Injections:")
    check_in_file("app.py", "PRESET_ENGINE_AVAILABLE", "Engine import flag")
    check_in_file("app.py", "auto_detect_niche_and_preset", "Auto-detect function")
    check_in_file("app.py", "compute_render_scores", "Scoring function")
    check_in_file("app.py", "preset_selector_section", "Preset selector UI")
    check_in_file("app.py", "scoring_panel_section", "Scoring panel UI")
    check_in_file("app.py", "caption_video_preview_section", "Caption preview UI")
    check_in_file("app.py", "custom_editing_settings_section", "Custom settings UI")
    check_in_file("app.py", "PRESET_LABELS_FALLBACK", "Preset labels dict")
    check_in_file("app.py", "get_preset_label", "get_preset_label()")
    check_in_file("app.py", "render_quality_badge", "Quality badge")
    check_in_file("app.py", "SCORING_STATE", "Scoring state")
    check_in_file("app.py", "phase4_config", "Phase4 config in session")

    # ---- PHASE 4: MASTER PIPELINE ----
    print("\n📋 Phase 4: master_pipeline.py:")
    check_in_file("master_pipeline.py", "PRESET_AVAILABLE", "Preset flag")
    check_in_file("master_pipeline.py", "apply_preset_to_render", "apply_preset_to_render()")
    check_in_file("master_pipeline.py", "resolve_preset_for_render", "resolve_preset_for_render()")

    # ---- PHASE 4: BATCH LONG ----
    print("\n📋 Phase 4: batch_long_renderer.py:")
    check_in_file("batch_long_renderer.py", "BATCH_PRESET_AVAILABLE", "Preset flag")
    check_in_file("batch_long_renderer.py", "def set_preset", "set_preset() method")
    check_in_file("batch_long_renderer.py", "static_hold", "Static hold motion")
    check_in_file("batch_long_renderer.py", "gentle_float_up", "Gentle float up motion")

    # ---- PHASE 5: VOICE ----
    print("\n📋 Phase 5: Voice Fixes:")
    check_in_file("voice_humanization_orchestrator.py", "PHASE 5 FIX", "Phase 5 comment")
    check_in_file("voice_humanization_orchestrator.py", "LRA=6", "LRA target 6")
    check_in_file("voice_humanization_orchestrator.py", "SINGLE-STAGE", "Single compressor")
    check_in_file("voice_humanization_orchestrator.py", "_per_sentence_pacing_filter", "Per-sentence pacing")
    check_in_file("voice_humanization_orchestrator.py", "_micro_pause_profile", "Micro-pause function")
    check_in_file("audio_engine.py", "ratio=1.7", "Compressor softened")

    # ---- PHASE 6: CAPTIONS ----
    print("\n📋 Phase 6: Caption Timing:")
    # Check no -0.10 remains in caption-related lines
    try:
        bl = Path("batch_long_renderer.py").read_text(encoding="utf-8")
        import re
        neg_caption_lines = []
        for i, line in enumerate(bl.split("\n"), 1):
            if re.search(r'caption.*-0\.\d+', line, re.IGNORECASE):
                neg_caption_lines.append(f"Line {i}: {line.strip()[:80]}")
        test("No negative caption offsets in batch_long", len(neg_caption_lines) == 0)
        if neg_caption_lines:
            print(f"      ⚠️ Found {len(neg_caption_lines)} lines with negative offsets:")
            for l in neg_caption_lines[:5]:
                print(f"         {l}")
    except Exception:
        test("No negative caption offsets in batch_long", False)

    check_in_file("caption_engine.py", "word_delay_fix: float = 0.0", "word_delay_fix default 0.0")

    # ---- RUNTIME IMPORTS ----
    print("\n📋 Runtime Import Tests:")
    imports = [
        ("streamlit", "import streamlit as st"),
        ("PIL", "from PIL import Image"),
        ("niche_editing_presets", "from niche_editing_presets import get_all_presets"),
        ("auto_edit_intelligence", "from auto_edit_intelligence import AutoEditIntelligence"),
        ("content_analyzer", "from content_analyzer import ContentAnalyzerEngine"),
        ("scene_detection_engine", "from scene_detection_engine import SceneDetectionEngine"),
        ("edit_decision_engine", "from edit_decision_engine import EditDecisionEngine"),
    ]
    for name, stmt in imports:
        try:
            exec(stmt)
            test(f"Import: {name}", True)
        except Exception as e:
            test(f"Import: {name}", False)
            print(f"      ⚠️ {str(e)[:80]}")

    # ---- SUMMARY ----
    print("\n" + "=" * 60)
    print("🏆 SUMMARY")
    print("=" * 60)
    total = PASSED + FAILED
    print(f"   Passed: {PASSED}/{total}")
    print(f"   Failed: {FAILED}/{total}")

    if FAILED == 0:
        print("\n   🎉 ALL CHECKS PASSED!")
        print("\n   📦 Launch app:")
        print("   streamlit run app.py")
    else:
        print(f"\n   ⚠️ {FAILED} checks failed.")
        print("   Re-run the relevant surgical patch for missing items.")


if __name__ == "__main__":
    main()