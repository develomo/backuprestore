PHASE 10 - INTEGRATION ENGINE V2

Purpose:
This phase connects all brain outputs into one unified project plan.
It does NOT render final video.

What it validates:
- all brains exist
- brain outputs pass into integration engine
- unified render contract is created
- target aspect/size is ready
- batch size is ready
- captions/audio/effects/memory handoff is ready

Install:
Extract this zip inside:
D:\My Creation Video Generator\backup

Run:
venv\Scripts\activate
python phase10_test.py

Expected:
PHASE 10 INTEGRATION ENGINE TEST
ok: True
render_executed: False
final_video_created: False
integration_version: integration_engine_v2_phase10

Report:
outputs\phase10_integration_engine_report.json

Next:
Phase 11 will be Practical Renderer Adapter.
It will connect the unified project plan to your existing batch_long_renderer.py,
but still in safe test mode first.
