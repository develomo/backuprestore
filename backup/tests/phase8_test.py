from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.ai_video_editor_v2 import AIVideoEditorV2, save_phase_report


def main():
    transcript = (
        "Imagine a private mansion hidden deep inside the frozen mountains. "
        "From the outside, it looks calm and silent. "
        "But beneath the glass walls, every room is designed like a luxury winter palace. "
        "Then a hidden spa level is revealed beneath the floor. "
        "By the end, the mansion shows why privacy is the real luxury."
    )

    context = {
        "mode": "LONG",
        "niche": "luxury",
        "transcript_text": transcript,
        "voice_duration": 1140.0,
        "clips": [f"scene_{i}.mp4" for i in range(1, 151)],
        "add_captions": True,
        "caption_mode": "phrase",
        "style_id": "phrase_gold_orange",
        "quality": "480p",
    }

    editor = AIVideoEditorV2()
    report = editor.plan_only(context)
    out = save_phase_report(report)

    memory = report["brains"]["memory_brain"]["data"]

    print("PHASE 8 MEMORY BRAIN TEST")
    print("ok:", report["ok"])
    print("render_executed:", report["render_executed"])
    print("final_video_created:", report["final_video_created"])
    print("memory_version:", memory.get("version"))
    print("clip_count:", memory.get("clip_count"))
    print("recommended_batch_size:", memory.get("recommended_batch_size"))
    print("render_strategy:", memory.get("render_strategy"))
    print("crash_recovery:", memory.get("crash_recovery", {}).get("enabled"))
    print("report:", out)

    assert report["ok"] is True
    assert report["render_executed"] is False
    assert report["final_video_created"] is False
    assert memory["version"] == "memory_brain_v2_phase8"
    assert memory["render_strategy"] == "memory_safe_batch_render"
    assert memory["resource_policy"]["avoid_full_moviepy_timeline"] is True
    assert memory["resource_policy"]["hidden_upscale"] is False
    assert memory["integration_handoff"]["render_now"] is False


if __name__ == "__main__":
    main()
