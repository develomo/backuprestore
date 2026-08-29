import shutil, time
from pathlib import Path

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

mp = BASE / "master_pipeline.py"
shutil.copy2(mp, BASE / f"master_pipeline.py.bak_sfx_{ts}")
text = mp.read_text(encoding="utf-8")

# Find apply_integrated_visual_layers and add SFX burst logic
old_sfx = '''def apply_integrated_visual_layers(video, plan, add_captions=True, add_keyword_zoom=True, add_beat=True, add_story=True):
    words = plan.get("caption_setup", {}).get("words") or []
    niche = plan.get("niche", "default")
    mode = plan.get("mode", "SHORT")
    render_count = plan.get("render_count", 0)
    caption_setup = plan.get("caption_setup", {})'''

new_sfx = '''def apply_integrated_visual_layers(video, plan, add_captions=True, add_keyword_zoom=True, add_beat=True, add_story=True, add_sfx_burst=True):
    words = plan.get("caption_setup", {}).get("words") or []
    niche = plan.get("niche", "default")
    mode = plan.get("mode", "SHORT")
    render_count = plan.get("render_count", 0)
    caption_setup = plan.get("caption_setup", {})
    
    # SFX burst on clip change boundaries
    if add_sfx_burst and video is not None:
        try:
            from sfx_engine import apply_sfx_burst_on_clip_change
            video = apply_sfx_burst_on_clip_change(video, mode=mode, niche=niche)
            safe_print("[MasterPipeline] SFX burst applied on clip boundaries")
        except Exception as e:
            safe_print(f"[MasterPipeline] SFX burst skipped: {e}")'''

if old_sfx in text:
    text = text.replace(old_sfx, new_sfx)
    print("SFX burst added to visual layers")
else:
    print("SFX pattern not found, checking...")
    idx = text.find('def apply_integrated_visual_layers(video, plan, add_captions')
    if idx != -1:
        snippet = text[idx:idx+500]
        print(f"Preview: {snippet[:200]}...")
    else:
        print("apply_integrated_visual_layers not found")

mp.write_text(text, encoding="utf-8")

try:
    compile(text, "master_pipeline.py", "exec")
    print("SYNTAX OK")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")

print(f"Backup: master_pipeline.py.bak_sfx_{ts}")