from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.ai_video_editor_v2 import AIVideoEditorV2, save_phase_report


def main():
    context = {
        "mode": "LONG",
        "niche": "luxury",
        "transcript_text": (
            "Imagine a private mansion hidden deep inside the frozen mountains. "
            "Every room feels calm, cinematic, and luxurious. "
            "Then a hidden spa level is revealed beneath the floor."
        ),
        "voice_duration": 180.0,
        "clips": [f"scene_{i}.mp4" for i in range(1, 21)],
        "add_captions": True,
        "caption_mode": "phrase",
        "style_id": "phrase_gold_orange",
        "quality": "480p",
    }

    editor = AIVideoEditorV2()
    report = editor.plan_only(context)
    out = save_phase_report(report)

    caption = report["brains"]["caption_brain"]["data"]

    print("PHASE 6 CAPTION BRAIN TEST")
    print("ok:", report["ok"])
    print("render_executed:", report["render_executed"])
    print("final_video_created:", report["final_video_created"])
    print("caption_version:", caption.get("version"))
    print("enabled:", caption.get("enabled"))
    print("mode:", caption.get("mode"))
    print("word_count:", caption.get("word_count"))
    print("segment_count:", caption.get("segment_count"))
    print("language_hint:", caption.get("language_hint"))
    print("report:", out)

    assert report["ok"] is True
    assert report["render_executed"] is False
    assert report["final_video_created"] is False
    assert caption["version"] == "caption_brain_v2_phase6"
    assert caption["enabled"] is True
    assert caption["segment_count"] > 0
    assert caption["renderer_handoff"]["render_now"] is False
    assert caption["renderer_handoff"]["fake_words_forbidden"] is True


if __name__ == "__main__":
    main()
