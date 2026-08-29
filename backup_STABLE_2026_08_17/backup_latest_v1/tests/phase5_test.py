
import json
from pathlib import Path
from engine.brains.audio_brain import AudioBrain

ctx={"niche":"luxury","voice_duration":1140}
brain=AudioBrain()
res=brain.run(ctx)
out=Path("outputs/phase5_audio_brain_report.json")
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(res.data,indent=2),encoding="utf-8")
print("PHASE 5 AUDIO BRAIN TEST")
print("ok:",res.ok)
print("render_executed:",False)
print("final_video_created:",False)
print("audio_version:",res.data["version"])
print("report:",out)
