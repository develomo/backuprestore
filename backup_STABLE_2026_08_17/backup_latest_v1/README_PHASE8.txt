PHASE 8 - MEMORY BRAIN V2

Purpose:
This phase upgrades Memory Brain only.
It does NOT render final video.
It creates a memory-safe render strategy and anti-repetition plan.

What it adds:
- memory-safe batch size planning
- avoid full MoviePy timeline policy
- anti-repetition planning for camera/transition choices
- clip reuse memory
- corrupt clip skip policy
- cleanup strategy
- crash recovery plan
- low-RAM resource policy

Install:
Extract this zip inside:
D:\My Creation Video Generator\backup

Run:
venv\Scripts\activate
python phase8_test.py

Expected:
PHASE 8 MEMORY BRAIN TEST
ok: True
render_executed: False
final_video_created: False
memory_version: memory_brain_v2_phase8

Report:
outputs\phase8_memory_brain_report.json
