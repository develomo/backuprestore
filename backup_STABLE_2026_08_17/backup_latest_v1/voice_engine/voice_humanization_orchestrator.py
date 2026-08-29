"""
VOICE HUMANIZATION ORCHESTRATOR
===============================

Central Stage-2 brain for the Voice Humanization System.

This file combines:
1. Voice profile selection
2. Auto niche detection
3. Human variation
4. Emotion mapping
5. Pause planning
6. Breath planning
7. Emphasis planning
8. Human timing planning
9. Audio preprocessing

Final result:
Raw robotic AI voice
    ↓
Humanized niche-specific voice
    ↓
Ready for Short / Long render pipeline
"""

import os
import json
from datetime import datetime

from voice_engine.voice_master_engine import (
    build_voice_humanization_profile,
    build_profile_summary,
)

from voice_engine.voice_settings_manager import (
    save_last_generated_voice_profile,
)

from voice_engine.processing.voice_preprocessor import (
    humanize_voice_file,
)

from voice_engine.processing.emotion_mapper import (
    build_emotion_map,
)

from voice_engine.processing.pause_engine import (
    build_pause_events,
)

from voice_engine.processing.breath_engine import (
    build_breath_plan,
)

from voice_engine.processing.emphasis_engine import (
    build_emphasis_plan,
)

from voice_engine.processing.human_timing_engine import (
    build_timing_plan,
)


BASE = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


def save_orchestrator_report(report):
    """
    Full voice intelligence report save karta hai.
    """

    profile_id = report.get(
        "profile",
        {}
    ).get(
        "profile_id",
        "unknown"
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_path = os.path.join(
        OUTPUT_DIR,
        f"voice_orchestrator_report_{profile_id}_{timestamp}.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            report,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        "✅ Voice orchestrator report saved:",
        output_path
    )

    return output_path


def build_voice_intelligence_stack(
    input_audio,
    selected_profile="auto",
    content_hint="",
    script_text="",
    voice_duration=None,
    mode="short",
    seed=None,
    save_report=True
):
    """
    Full intelligence stack build karta hai.

    Args:
        input_audio:
            raw AI voice path

        selected_profile:
            auto / quantum_future / stoic_wisdom / luxury_lifestyle /
            mystery / interior_design / finance_simulation

        content_hint:
            title / niche / topic

        script_text:
            script text if available

        voice_duration:
            seconds

        mode:
            short / long

        seed:
            optional repeatable variation seed

        save_report:
            save json report or not

    Returns:
        dict report
    """

    profile = build_voice_humanization_profile(
        selected_profile=selected_profile,
        content_hint=content_hint,
        seed=seed,
        save_report=True
    )

    profile_id = profile.get(
        "profile_id",
        "quantum_future"
    )

    emotion_map = build_emotion_map(
        profile_id=profile_id,
        script_text=script_text,
        content_hint=content_hint
    )

    pause_plan = build_pause_events(
        profile=profile,
        script_text=script_text,
        content_hint=content_hint,
        emotion_map=emotion_map
    )

    if voice_duration is None:
        voice_duration = 60

    breath_plan = build_breath_plan(
        profile=profile,
        voice_duration=voice_duration,
        emotion_map=emotion_map,
        pause_plan=pause_plan
    )

    emphasis_plan = build_emphasis_plan(
        profile=profile,
        script_text=script_text,
        content_hint=content_hint,
        emotion_map=emotion_map
    )

    timing_plan = build_timing_plan(
        profile=profile,
        voice_duration=voice_duration,
        emotion_map=emotion_map,
        pause_plan=pause_plan,
        breath_plan=breath_plan,
        emphasis_plan=emphasis_plan
    )

    report = {
        "created_at": datetime.now().isoformat(),
        "mode": mode,
        "input_audio": input_audio,
        "selected_profile_input": selected_profile,
        "content_hint": content_hint,
        "script_text_available": bool(script_text),
        "voice_duration": voice_duration,

        "profile": profile,
        "profile_summary": build_profile_summary(profile),

        "emotion_map": emotion_map,
        "pause_plan": pause_plan,
        "breath_plan": breath_plan,
        "emphasis_plan": emphasis_plan,
        "timing_plan": timing_plan
    }

    if save_report:
        report_path = save_orchestrator_report(
            report
        )

        report["report_path"] = report_path

    return report


def humanize_voice_with_full_stack(
    input_audio,
    selected_profile="auto",
    content_hint="",
    script_text="",
    voice_duration=None,
    mode="short",
    seed=None,
    save_report=True
):
    """
    Main public function.

    Ye function:
    1. Full intelligence stack banata hai
    2. Voice preprocess karta hai
    3. Humanized voice path return karta hai
    """

    report = build_voice_intelligence_stack(
        input_audio=input_audio,
        selected_profile=selected_profile,
        content_hint=content_hint,
        script_text=script_text,
        voice_duration=voice_duration,
        mode=mode,
        seed=seed,
        save_report=save_report
    )

    profile = report.get(
        "profile",
        {}
    )

    output_audio = humanize_voice_file(
        input_audio=input_audio,
        profile=profile
    )

    report["output_audio"] = output_audio

    save_last_generated_voice_profile(
        profile
    )

    print("")
    print("========================================")
    print("🎙 FULL VOICE HUMANIZATION COMPLETE")
    print("========================================")
    print("Mode:", mode)
    print("Input:", input_audio)
    print("Output:", output_audio)
    print("Profile ID:", profile.get("profile_id"))
    print("Profile Name:", profile.get("name"))
    print("Emotion:", report.get("emotion_map", {}).get("emotion"))
    print("Pause Style:", report.get("pause_plan", {}).get("pause_style"))
    print("Breath Style:", report.get("breath_plan", {}).get("breath_style"))
    print("Emphasis Style:", report.get("emphasis_plan", {}).get("emphasis_style"))
    print("Timing Style:", report.get("timing_plan", {}).get("timing_style"))
    print("Delivery Intensity:", report.get("timing_plan", {}).get("delivery_intensity"))
    print("========================================")
    print("")

    return output_audio


if __name__ == "__main__":
    test_input = os.path.join(
        BASE,
        "inputs",
        "shorts",
        "voices",
        "download.wav"
    )

    if not os.path.exists(test_input):
        print("⚠ Test input not found:", test_input)
    else:
        humanize_voice_with_full_stack(
            input_audio=test_input,
            selected_profile="auto",
            content_hint="AI future documentary about machines and humanity",
            script_text="The system was evolving. Humanity was slowly losing control of the future.",
            voice_duration=60,
            mode="short",
            save_report=True
        )
