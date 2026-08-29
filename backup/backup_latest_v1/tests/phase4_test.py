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
        "The living room opens toward a wide valley covered in snow. "
        "Gold details, soft lights, and marble floors create a quiet premium atmosphere. "
        "Then the story changes, because hidden under the floor is a secret spa level. "
        "This is where the house becomes more than a home. "
        "It becomes a private world built for power, comfort, and complete isolation."
    )

    context = {
        "mode": "LONG",
        "niche": "luxury",
        "transcript_text": transcript,
        "voice_duration": 600.0,
        # These files do not need to exist for Phase 4 test.
        # Visual Brain should still create a plan and mark unknown probe.
        "clips": [
            "scene_1_16x9.mp4",
            "scene_2_vertical.mp4",
            "scene_3_square.mp4",
            "scene_4_ultrawide.mp4",
            "scene_5_mixed.mp4",
        ],
        "add_captions": True,
        "caption_mode": "phrase",
        "style_id": "phrase_gold_orange",
        "quality": "480p",
    }

    editor = AIVideoEditorV2()
    report = editor.plan_only(context)
    out = save_phase_report(report)

    visual = report["brains"]["visual_brain"]["data"]
    editing = report["brains"]["editing_brain"]["data"]

    print("PHASE 4 VISUAL BRAIN TEST")
    print("ok:", report["ok"])
    print("render_executed:", report["render_executed"])
    print("final_video_created:", report["final_video_created"])
    print("visual_version:", visual.get("version"))
    print("target_canvas:", visual.get("target_canvas"))
    print("clip_count:", visual.get("clip_count"))
    print("aspect_summary:", visual.get("aspect_summary"))
    print("risk_summary:", visual.get("risk_summary"))
    print("editing_version:", editing.get("version"))
    print("report:", out)

    assert report["ok"] is True
    assert report["render_executed"] is False
    assert report["final_video_created"] is False
    assert visual["version"] == "visual_brain_v2_phase4"
    assert visual["target_canvas"]["aspect"] == "16:9"
    assert visual["renderer_handoff"]["force_same_aspect_ratio"] is True
    assert visual["renderer_handoff"]["detect_black_bars"] is True
    assert visual["renderer_handoff"]["no_stretch"] is True
    assert visual["renderer_handoff"]["render_now"] is False
    assert visual["clip_count"] == 5


if __name__ == "__main__":
    main()
