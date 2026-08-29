PHASE 12 - LONG PIPELINE INTEGRATION V2

Purpose:
This phase connects AI brain outputs to the long video pipeline call shape.
It does NOT render final video yet.

What it tests:
- Unified plan -> safe_long_video_polished kwargs
- Captions pass through
- UI temp assets pass through
- 16:9 target aspect pass through
- Batch size pass through
- Hidden upscale remains OFF
- Render remains OFF

Install:
Extract this zip inside:
D:\My Creation Video Generator\backup

Run:
venv\Scripts\activate
python phase12_test.py

Expected:
PHASE 12 LONG PIPELINE INTEGRATION TEST
ok: True
dry_run: True
render_executed: False
final_video_created: False

Report:
outputs\phase12_long_pipeline_integration_report.json

Next:
Phase 13 will create Safe Renderer Execution Mode.
That will call the real long renderer only when explicitly enabled,
starting with a tiny 2-clip sample test before full render.
