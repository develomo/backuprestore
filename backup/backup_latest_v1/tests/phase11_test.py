
import json
from pathlib import Path
from engine.adapter.renderer_adapter import RendererAdapterV2

plan={"render_contract":{"target_aspect":"16:9","quality":"480p","batch_size":8}}
adapter=RendererAdapterV2()
r=adapter.connect(plan)
Path("outputs").mkdir(exist_ok=True)
Path("outputs/phase11_renderer_adapter_report.json").write_text(json.dumps(r.stage_map,indent=2))
print("PHASE 11 RENDERER ADAPTER TEST")
print("ok:",r.ok)
print("render_executed:",r.render_executed)
print("final_video_created:",r.final_video_created)
print("version:",RendererAdapterV2.VERSION)
print("report: outputs/phase11_renderer_adapter_report.json")
