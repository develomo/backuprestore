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

    integration = report["integration"]
    plan = integration["unified_project_plan"]
    contract = plan["render_contract"]

    print("PHASE 10 INTEGRATION ENGINE TEST")
    print("ok:", report["ok"])
    print("render_executed:", report["render_executed"])
    print("final_video_created:", report["final_video_created"])
    print("integration_version:", integration.get("version"))
    print("integration_ok:", integration.get("ok"))
    print("render_contract_ready:", plan["data_flow"]["render_contract_ready"])
    print("target:", contract.get("target_width"), "x", contract.get("target_height"), contract.get("target_aspect"))
    print("batch_size:", contract.get("batch_size"))
    print("captions_enabled:", contract.get("captions_enabled"))
    print("report:", out)

    assert report["ok"] is True
    assert report["render_executed"] is False
    assert report["final_video_created"] is False
    assert integration["version"] == "integration_engine_v2_phase10"
    assert integration["ok"] is True
    assert plan["render_now"] is False
    assert plan["final_video_created"] is False
    assert plan["data_flow"]["render_contract_ready"] is True
    assert contract["target_aspect"] == "16:9"
    assert contract["hidden_upscale"] is False


if __name__ == "__main__":
    main()
