PHASE 14 - VALIDATION & BENCHMARK SUITE

Purpose:
This phase does not render final video.
It checks whether Phase 13 files are installed correctly.

Install:
Extract this zip inside:
D:\My Creation Video Generator\backup

Run:
venv\Scripts\activate
python phase14_validate.py

Expected:
PHASE 14 VALIDATION TEST
ok: True
render_executed: False
final_video_created: False

Report:
outputs\phase14_validation_report.json

After you render a real video, probe it:
python phase14_probe_output.py outputs\your_final_video.mp4

This checks:
- width
- height
- display aspect ratio
- fps string
