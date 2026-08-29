
import json
from pathlib import Path
from engine.brains.render_brain import RenderBrain

brain=RenderBrain()
res=brain.run({})
Path("outputs").mkdir(exist_ok=True)
report=Path("outputs/phase9_render_brain_report.json")
report.write_text(json.dumps(res.data,indent=2))
print("PHASE 9 RENDER BRAIN TEST")
print("ok:",res.ok)
print("render_executed:",False)
print("final_video_created:",False)
print("render_version:",res.data["version"])
print("report:",report)
