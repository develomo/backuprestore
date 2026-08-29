from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.ai_video_editor_v2 import AIVideoEditorV2
from engine.integration.long_pipeline_integration import LongPipelineIntegrationV2
from engine.adapter import SafeLongAdapterV2


def main():
    context = {
        "mode": "LONG",
        "niche": "luxury",
        "transcript_text": (
            "Imagine a private mansion hidden deep inside the frozen mountains. "
            "Every room feels calm and cinematic. "
            "Then a hidden spa level is revealed beneath the floor."
        ),
        "voice_duration": 1140.0,
        "voice_path": "ui_temp_voice.mp3",
        "clips": [f"ui_temp_scene_{i}.mp4" for i in range(1, 151)],
        "music_path": "ui_temp_music.mp3",
        "sfx_files": ["ui_temp_sfx_1.wav", "ui_temp_sfx_2.wav"],
        "intro_path": "ui_temp_intro.mp4",
        "outro_path": "ui_temp_outro.mp4",
        "subscribe_overlay": "ui_temp_subscribe.png",
        "add_captions": True,
        "caption_mode": "phrase",
        "style_id": "phrase_gold_orange",
        "quality": "480p",
        "use_hook": True,
        "use_overlays": True,
    }

    editor = AIVideoEditorV2()
    brain_report = editor.plan_only(context)

    integration = LongPipelineIntegrationV2()
    phase12 = integration.run_dry(context, brain_report)

    adapter = SafeLongAdapterV2()
    prepared = adapter.prepare_call(phase12["safe_long_kwargs"])

    out = Path("outputs/phase12_long_pipeline_integration_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "phase12": phase12,
        "adapter": prepared,
    }, indent=2), encoding="utf-8")

    print("PHASE 12 LONG PIPELINE INTEGRATION TEST")
    print("ok:", phase12["ok"] and prepared["ok"])
    print("dry_run:", phase12["dry_run"])
    print("render_executed:", phase12["render_executed"])
    print("final_video_created:", phase12["final_video_created"])
    print("version:", phase12["version"])
    print("clip_count:", phase12["validation"]["clip_count"])
    print("captions_enabled:", phase12["validation"]["captions_enabled"])
    print("caption_mode:", phase12["validation"]["caption_mode"])
    print("quality:", phase12["validation"]["quality"])
    print("batch_size:", phase12["validation"]["batch_size"])
    print("report:", out)

    assert phase12["ok"] is True
    assert phase12["dry_run"] is True
    assert phase12["render_executed"] is False
    assert phase12["final_video_created"] is False
    assert prepared["render_executed"] is False
    assert prepared["final_video_created"] is False
    assert phase12["validation"]["clip_count"] == 150
    assert phase12["safe_long_kwargs"]["add_captions"] is True
    assert phase12["safe_long_kwargs"]["final_4k"] is False
    assert phase12["safe_long_kwargs"]["preset_overrides"]["target_aspect"] == "16:9"
    assert phase12["safe_long_kwargs"]["preset_overrides"]["hidden_upscale"] is False


if __name__ == "__main__":
    main()
