from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.ai_video_editor_v2 import AIVideoEditorV2, save_phase1_report


def main():
    transcript = (
        "Imagine a private mansion hidden deep inside the frozen mountains. "
        "From the outside, it looks calm and silent. "
        "But beneath the glass walls, every room is designed like a luxury winter palace. "
        "The living room opens toward a wide valley covered in snow. "
        "Gold details, soft lights, and marble floors create a quiet premium atmosphere. "
        "Then the story changes, because hidden under the floor is a secret spa level. "
        "This is where the house becomes more than a home. "
        "It becomes a private world built for power, comfort, and complete isolation. "
        "By the end, the mansion reveals why luxury is not only about money. "
        "It is about privacy, silence, and control."
    )

    context = {
        "mode": "LONG",
        "niche": "luxury",
        "transcript_text": transcript,
        "voice_duration": 600.0,
        "clips": [f"scene_{i}.mp4" for i in range(1, 61)],
        "add_captions": True,
        "caption_mode": "phrase",
        "style_id": "phrase_gold_orange",
        "quality": "480p",
    }

    editor = AIVideoEditorV2()
    report = editor.plan_only(context)

    out = Path("outputs/phase2_story_brain_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    story = report["brains"]["story_brain"]["data"]

    print("PHASE 2 STORY BRAIN TEST")
    print("ok:", report["ok"])
    print("render_executed:", report["render_executed"])
    print("final_video_created:", report["final_video_created"])
    print("story_version:", story.get("version"))
    print("sentence_count:", story.get("sentence_count"))
    print("dominant_emotion:", story.get("dominant_emotion"))
    print("chapters:", len(story.get("chapters", [])))
    print("pattern_interrupts:", len(story.get("pattern_interrupts", [])))
    print("report:", out)

    assert report["ok"] is True
    assert report["render_executed"] is False
    assert report["final_video_created"] is False
    assert story["version"] == "story_brain_v2_phase2"
    assert story["sentence_count"] >= 5
    assert len(story["sentences"]) == story["sentence_count"]
    assert len(story["chapters"]) >= 2
    assert "editing_handoff" in story


if __name__ == "__main__":
    main()
