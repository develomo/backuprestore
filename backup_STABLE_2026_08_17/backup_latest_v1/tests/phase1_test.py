from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from engine.ai_video_editor_v2 import AIVideoEditorV2, save_phase1_report
def main():
    context={"mode":"LONG","niche":"luxury","transcript_text":"This mansion overlooks the frozen mountains. Inside, every room feels calm and cinematic. As the night begins, the lights reveal a hidden luxury world.","voice_duration":180.0,"clips":[f"scene_{i}.mp4" for i in range(1,31)],"add_captions":True,"caption_mode":"phrase","style_id":"phrase_crystal_cyan","quality":"480p"}
    report=AIVideoEditorV2().plan_only(context)
    out=save_phase1_report(report)
    print("PHASE 1 TEST"); print("ok:",report["ok"]); print("render_executed:",report["render_executed"]); print("final_video_created:",report["final_video_created"]); print("brains:",", ".join(report["brains"].keys())); print("report:",out)
    assert report["ok"] is True and report["render_executed"] is False and report["final_video_created"] is False
if __name__=="__main__": main()
