
import json
from pathlib import Path
from engine.brains.effects_brain import EffectsBrain

brain=EffectsBrain()
res=brain.run({"niche":"luxury"})
Path("outputs").mkdir(exist_ok=True)
report=Path("outputs/phase7_effects_brain_report.json")
report.write_text(json.dumps(res.data,indent=2))
print("PHASE 7 EFFECTS BRAIN TEST")
print("ok:",res.ok)
print("render_executed:",False)
print("final_video_created:",False)
print("effects_version:",res.data["version"])
print("report:",report)
