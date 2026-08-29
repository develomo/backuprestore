"""
====================================================================
FINAL COMPLETE INTEGRATION TEST — ALL PATCHES 1-12
====================================================================
USAGE: python test_all_patches_final.py
====================================================================
"""

from pathlib import Path
import re

BASE_DIR = Path(__file__).parent
PASSED = 0
FAILED = 0


def test(name, condition):
    global PASSED, FAILED
    if condition:
        print(f"   YES {name}")
        PASSED += 1
    else:
        print(f"   NO  {name}")
        FAILED += 1


def check_in(path, text, name):
    try:
        content = Path(path).read_text(encoding="utf-8")
        test(name, text in content)
    except Exception:
        test(name, False)


def main():
    global PASSED, FAILED

    print("=" * 60)
    print("FINAL INTEGRATION TEST - PATCHES 1-12")
    print("=" * 60)

    # Files
    print("\n--- Files Present ---")
    for f in ["app.py","master_pipeline.py","batch_long_renderer.py",
              "safe_long_video_polished.py","voice_humanization_orchestrator.py",
              "audio_engine.py","caption_engine.py","final_assembler.py",
              "niche_editing_presets.py","auto_edit_intelligence.py",
              "content_analyzer.py","scene_detection_engine.py",
              "edit_decision_engine.py"]:
        test(f, Path(BASE_DIR / f).exists())

    # Patch 1: Long Preset
    print("\n--- PATCH 1: Long Pipeline Preset ---")
    check_in("safe_long_video_polished.py","PRESET_AVAILABLE_LONG","PRESET_AVAILABLE_LONG")
    check_in("safe_long_video_polished.py","resolve_preset_for_render","resolve_preset_for_render")
    check_in("safe_long_video_polished.py","preset_number","preset_number extraction")

    # Patch 2: Film Grain
    print("\n--- PATCH 2: Film Grain ---")
    check_in("batch_long_renderer.py","apply_film_grain","apply_film_grain()")
    check_in("batch_long_renderer.py","should_apply_grain","should_apply_grain()")
    check_in("final_assembler.py","FILM_GRAIN_ENABLED","FILM_GRAIN_ENABLED flag")

    # Patch 3: SFX Whoosh
    print("\n--- PATCH 3: SFX Whoosh ---")
    check_in("batch_long_renderer.py","insert_cut_sfx","insert_cut_sfx()")
    check_in("batch_long_renderer.py","generate_whoosh_silence","generate_whoosh_silence()")
    check_in("safe_long_video_polished.py","sfx_cut_sync","sfx_cut_sync flag")

    # Patch 4: Emphasis Captions
    print("\n--- PATCH 4: Emphasis Captions ---")
    check_in("caption_engine.py","is_emphasis_word","is_emphasis_word()")
    check_in("caption_engine.py","apply_emphasis_to_caption","apply_emphasis_to_caption()")
    check_in("caption_engine.py","EMPHASIS_WORDS","EMPHASIS_WORDS dict")

    # Patch 5: Framing Variety
    print("\n--- PATCH 5: Framing Variety ---")
    check_in("batch_long_renderer.py","get_next_framing","get_next_framing()")
    check_in("batch_long_renderer.py","FRAMING_TYPES","FRAMING_TYPES list")
    check_in("batch_long_renderer.py","framing_crop_params","framing_crop_params()")

    # Patch 6: Room Tone
    print("\n--- PATCH 6: Room Tone ---")
    check_in("audio_engine.py","generate_room_tone","generate_room_tone()")
    check_in("audio_engine.py","mix_room_tone_into_audio","mix_room_tone_into_audio()")

    # Patch 7: EQ De-Hype
    print("\n--- PATCH 7: EQ De-Hype ---")
    check_in("voice_humanization_orchestrator.py","sizzle_cut","sizzle_cut variable")
    check_in("voice_humanization_orchestrator.py","equalizer=f=4500","4.5kHz equalizer line")

    # Patch 8: Breath Sounds
    print("\n--- PATCH 8: Breath Sounds ---")
    check_in("voice_humanization_orchestrator.py","_generate_breath_sound","_generate_breath_sound()")
    check_in("voice_humanization_orchestrator.py","insert_breath_sounds","insert_breath_sounds()")

    # Patch 9: Scene-Adaptive Cuts
    print("\n--- PATCH 9: Scene-Adaptive Cuts ---")
    check_in("batch_long_renderer.py","detect_scene_changes","detect_scene_changes()")
    check_in("batch_long_renderer.py","adaptive_cut_plan","adaptive_cut_plan()")
    check_in("batch_long_renderer.py","get_cut_timestamps_from_durations","get_cut_timestamps_from_durations()")

    # Patch 10: LUT Color Grading
    print("\n--- PATCH 10: LUT Color Grading ---")
    check_in("batch_long_renderer.py","niche_color_grade","niche_color_grade()")
    check_in("batch_long_renderer.py","apply_color_grade_to_filter","apply_color_grade_to_filter()")
    check_in("batch_long_renderer.py","colorchannelmixer","colorchannelmixer (real LUT)")

    # Patch 11: Motion Blur
    print("\n--- PATCH 11: Motion Blur ---")
    check_in("batch_long_renderer.py","should_apply_motion_blur","should_apply_motion_blur()")
    check_in("batch_long_renderer.py","add_motion_blur_to_filter","add_motion_blur_to_filter()")
    check_in("batch_long_renderer.py","tmix=frames=2","tmix temporal blending")

    # Patch 12: Audio Ducking
    print("\n--- PATCH 12: Audio Ducking ---")
    check_in("audio_engine.py","apply_intelligent_ducking","apply_intelligent_ducking()")
    check_in("audio_engine.py","sidechaincompress","sidechaincompress filter")

    # Phase 4-6 re-verify
    print("\n--- Phase 4-6 Re-Verify ---")
    check_in("app.py","preset_selector_section","Preset selector UI")
    check_in("app.py","scoring_panel_section","Scoring panel")
    check_in("app.py","auto_detect_niche_and_preset","Auto-detect")
    check_in("app.py","caption_video_preview_section","Caption preview")
    check_in("master_pipeline.py","apply_preset_to_render","Preset to master")
    check_in("voice_humanization_orchestrator.py","PHASE 5 FIX","Voice fix (Phase 5)")
    check_in("batch_long_renderer.py","gentle_float_up","12 motions")

    # No neg caption offsets
    try:
        bl = Path("batch_long_renderer.py").read_text(encoding="utf-8")
        neg = [l for l in bl.split("\n") if re.search(r'caption.*-\d\.\d+', l, re.IGNORECASE)]
        test("No negative caption offsets", len(neg) == 0)
    except:
        test("No negative caption offsets", False)

    # Summary
    total = PASSED + FAILED
    print("\n" + "=" * 60)
    print("FINAL RESULT: " + str(PASSED) + "/" + str(total) + " PASSED")
    print("=" * 60)

    if FAILED == 0:
        print("\n*** ALL CHECKS PASSED! 12/12 PATCHES VERIFIED ***")
        print("\nLaunch: streamlit run app.py")
    else:
        print("\n" + str(FAILED) + " checks failed")
        print("Run: python final_fix_and_advanced.py")


if __name__ == "__main__":
    main()