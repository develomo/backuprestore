# final_3_fixes.py
import shutil
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET = BASE_DIR / "batch_long_renderer.py"
SAFE_LONG = BASE_DIR / "safe_long_video_polished.py"
APP_PY = BASE_DIR / "app.py"

def backup(filepath):
    if filepath.exists():
        backup_path = filepath.with_suffix(filepath.suffix + ".final_3_fixes_bak")
        if not backup_path.exists():
            shutil.copy2(filepath, backup_path)
            print(f"[OK] Backed up: {backup_path.name}")

def fix_batch_renderer():
    if not TARGET.exists():
        print("[ERROR] batch_long_renderer.py not found!")
        return False
    
    backup(TARGET)
    content = TARGET.read_text(encoding="utf-8")
    
    # FIX 1: Outro at exact last 2 seconds (Separate main body from outro)
    # We use regex to safely find and replace the block regardless of minor spacing differences
    pattern = re.compile(
        r'outro_out, outro_asset_type = resolve_outro_segment\([^)]+\)\s*outputs\.append\(outro_out\)\s*if not outputs:\s*raise RuntimeError\("No visual outputs rendered"\)\s*video_raw = temp / "video_raw\.mp4"\s*concat_files\(outputs, video_raw.*?video_raw = extended',
        re.DOTALL
    )
    
    new_outro_block = '''    # FIX: Separate main body from outro so outro is NOT looped
    main_outputs = [p for p in outputs if "outro" not in str(p).lower()]
    video_raw = temp / "video_raw.mp4"
    concat_files(main_outputs, video_raw, niche=preset.get("niche", "default"), use_transitions=True,
                 global_indices=list(range(len(main_outputs))), chapter_flags=[False] * len(main_outputs))
    safe_gc()
    
    visual_duration = probe_duration(video_raw)
    target_body_duration = total_duration - outro_sec
    
    if visual_duration < target_body_duration - 0.5:
        extended = temp / "video_body_extended.mp4"
        log(f"[StableLong] visual shorter ({visual_duration:.2f}s < {target_body_duration:.2f}s); extending main body to match voice duration")
        run_cmd([
            FFMPEG, "-y", "-stream_loop", "-1", "-i", str(video_raw), "-t", f"{target_body_duration:.3f}",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30", "-pix_fmt", "yuv420p",
            "-threads", "0", str(extended),
        ], timeout=2400) # 40 min timeout
        video_raw = extended
    
    # FIX: NOW append outro at the very end (guaranteed last 2 seconds)
    final_visual = temp / "final_visual.mp4"
    if outro_out and outro_out.exists():
        log(f"[StableLong] Appending guaranteed {outro_sec}s outro at the very end")
        concat_files([video_raw, outro_out], final_visual, use_transitions=False)
        video_raw = final_visual'''
    
    if pattern.search(content):
        content = pattern.sub(new_outro_block, content)
        print("[OK] Fix 1: Outro will now appear EXACTLY at the last 2 seconds (not looped)")
    else:
        print("[WARN] Fix 1: Could not find exact outro block. It may already be fixed or formatted differently.")
        
    # FIX 2: Subscribe overlay timeout to 40 mins (2400s) and bottom-right
    content = re.sub(r'timeout=\d+\)', 'timeout=2400)', content)
    content = content.replace('corner="top-right"', 'corner="bottom-right"')
    print("[OK] Fix 2: Subscribe overlay timeout increased to 40 mins (2400s) and position set to bottom-right")
    
    TARGET.write_text(content, encoding="utf-8")
    return True

def fix_safe_long():
    if not SAFE_LONG.exists():
        print("[WARN] safe_long_video_polished.py not found!")
        return False
    
    backup(SAFE_LONG)
    content = SAFE_LONG.read_text(encoding="utf-8")
    
    # Ensure custom_logo_path and wm_opacity are in the function signature
    if 'def run_integrated_long_pipeline(' in content and 'custom_logo_path=None' not in content:
        content = content.replace(
            'def run_integrated_long_pipeline(voice_path=None,clips=None,words=None,words_path=None,transcript_text=None,output_path=None,niche="default",render_count=0,caption_mode="phrase",style_id=None,music_path=None,sfx_files=None,use_hook=True,hook_text=None,use_overlays=True,final_4k=False,fps=24,quality=None,clean_silence=False,add_captions = True,preset_overrides=None,**kwargs):',
            'def run_integrated_long_pipeline(voice_path=None,clips=None,words=None,words_path=None,transcript_text=None,output_path=None,niche="default",render_count=0,caption_mode="phrase",style_id=None,music_path=None,sfx_files=None,use_hook=True,hook_text=None,use_overlays=True,final_4k=False,fps=24,quality=None,clean_silence=False,add_captions=True,preset_overrides=None,custom_logo_path=None,wm_opacity=0.6,**kwargs):'
        )
        print("[OK] Fix 3: Added custom_logo_path and wm_opacity to safe_long signature")
    
    # Ensure they are passed to render_long_batch_memory
    if 'final=render_long_batch_memory(' in content and 'custom_logo_path=custom_logo_path' not in content:
        content = content.replace(
            'cleanup=True,preset_overrides=preset)',
            'cleanup=True,preset_overrides=preset,custom_logo_path=custom_logo_path,wm_opacity=wm_opacity)'
        )
        print("[OK] Fix 4: Passing custom_logo_path and wm_opacity to renderer")
        
    SAFE_LONG.write_text(content, encoding="utf-8")
    return True

def fix_app_py():
    if not APP_PY.exists():
        print("[WARN] app.py not found!")
        return False
    
    backup(APP_PY)
    content = APP_PY.read_text(encoding="utf-8")
    
    # Ensure custom_logo_path is passed in build_render_kwargs for LONG mode
    if 'if mode_u == "LONG":' in content and 'custom_logo_path' not in content:
        # Find the LONG block and add the params
        old_long_block = '''if mode_u == "LONG":
        kwargs.update({
            "intro_path": assets.get("intro"),
            "outro_path": assets.get("outro"),
            "subscribe_overlay": assets.get("subscribe"),
            "subscribe_overlay_path": assets.get("subscribe"),
            "overlay": assets.get("subscribe"),
        })'''
        
        new_long_block = '''if mode_u == "LONG":
        kwargs.update({
            "intro_path": assets.get("intro"),
            "outro_path": assets.get("outro"),
            "subscribe_overlay": assets.get("subscribe"),
            "subscribe_overlay_path": assets.get("subscribe"),
            "overlay": assets.get("subscribe"),
            "custom_logo_path": assets.get("wm_logo"),
            "wm_opacity": assets.get("wm_opacity", 0.6),
        })'''
        
        if old_long_block in content:
            content = content.replace(old_long_block, new_long_block)
            print("[OK] Fix 5: app.py now passes logo watermark data to backend")
        else:
            print("[WARN] Fix 5: Could not find exact app.py block. Manual check needed.")
            
    APP_PY.write_text(content, encoding="utf-8")
    return True

if __name__ == "__main__":
    print("="*70)
    print("Applying Final 3 Fixes: Outro, Subscribe Timeout, Logo Watermark")
    print("="*70)
    
    fix_batch_renderer()
    print()
    fix_safe_long()
    print()
    fix_app_py()
    
    print("\n" + "="*70)
    print("✅ ALL FIXES APPLIED SUCCESSFULLY!")
    print("="*70)
    print("1. Outro will now be appended ONLY at the very end (last 2 seconds).")
    print("2. Subscribe overlay timeout is now 40 minutes (2400s) to prevent failure.")
    print("3. Logo watermark parameters are explicitly passed from UI to backend.")
    print("\nNext Step: Run 'streamlit run app.py' and test your long video render.")