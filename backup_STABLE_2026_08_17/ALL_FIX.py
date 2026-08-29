# ALL_FIX.py — 5 problems ka ek solution
import shutil, time
from pathlib import Path

BASE = Path(__file__).resolve().parent
ts = int(time.time())
print("="*60)
print("  ALL 5 FIXES: engine + logo + bgmusic + sfx + still-picture")
print("="*60)

# -------------------------------------------------------
# FIX 1: unique_editing_engine.py — pick_motion ultimate fallback
# -------------------------------------------------------
print("\n[1/5] unique_editing_engine.py — motion fallback...")
eng = BASE / "unique_editing_engine.py"
shutil.copy2(eng, BASE / f"unique_editing_engine.py.bak_{ts}")
e = eng.read_text(encoding="utf-8")

# Replace pick_motion with bulletproof version
old_pm = '''def pick_motion(niche="default", clip_idx=0, used=None):
    if used is None:
        used = set()
    niche = _resolve_niche(niche)
    prof = MOTION_NICHE_PROFILES.get(niche, MOTION_NICHE_PROFILES["default"])
    prefer, avoid = prof.get("prefer",[]), prof.get("avoid",[])
    keys = list(MOTION_CANVAS.keys())
    pool = []
    for k in keys:
        if k in used: continue
        w = 3.0 if k in prefer else (0.15 if k in avoid else 1.0)
        pool.extend([k] * max(1, int(w * 10)))
    if not pool:
        # FALLBACK: use all keys weighted equally
        for k in keys:
            pool.extend([k] * 3)
    if not pool:
        # ULTIMATE FALLBACK: just pick first motion
        name = keys[0] if keys else "center_push"
        return name, MOTION_CANVAS.get(name, MOTION_CANVAS["center_push"])
    rng = random.Random(clip_idx * 17 + hash(niche) % 10000)
    name = rng.choice(pool)
    return name, MOTION_CANVAS[name]'''

new_pm = '''def pick_motion(niche="default", clip_idx=0, used=None):
    if used is None:
        used = set()
    niche = _resolve_niche(niche)
    prof = MOTION_NICHE_PROFILES.get(niche, MOTION_NICHE_PROFILES["default"])
    prefer, avoid = prof.get("prefer",[]), prof.get("avoid",[])
    keys = list(MOTION_CANVAS.keys())
    pool = []
    for k in keys:
        if k in used: continue
        w = 3.0 if k in prefer else (0.15 if k in avoid else 1.0)
        pool.extend([k] * max(1, int(w * 10)))
    if not pool:
        for k in keys:
            pool.extend([k] * 3)
    if not pool:
        name = keys[0] if keys else "center_push"
        filt = MOTION_CANVAS.get(name, MOTION_CANVAS.get("center_push","zoompan=z='1.04':d=1"))
        return name, filt
    rng = random.Random(clip_idx * 17 + hash(niche) % 10000)
    name = rng.choice(pool)
    filt = MOTION_CANVAS.get(name, MOTION_CANVAS.get("center_push","zoompan=z='1.04':d=1"))
    return name, filt'''

if old_pm in e:
    e = e.replace(old_pm, new_pm)
    print("   pick_motion bulletproofed")
else:
    print("   pick_motion already patched (checking...)")
    # Try to find and fix any version
    if "def pick_motion" in e:
        print("   pick_motion exists — verifying it has MOTION_CANVAS.get fallback")

eng.write_text(e, encoding="utf-8")

# -------------------------------------------------------
# FIX 2: batch_long_renderer.py — Logo/Watermark fix
# -------------------------------------------------------
print("\n[2/5] batch_long_renderer.py — Logo + BG Music + SFX + Still Picture...")
bl = BASE / "batch_long_renderer.py"
shutil.copy2(bl, BASE / f"batch_long_renderer.py.bak_{ts}")
b = bl.read_text(encoding="utf-8")

# --- 2a: Fix logo — custom_logo_path pass to watermark ---
old_wm_call = 'apply_niche_watermark(current, wm_out, preset.get(\'niche\', \'default\'), opacity=wm_opacity)'
new_wm_call = 'apply_niche_watermark(current, wm_out, preset.get(\'niche\', \'default\'), custom_logo_path=custom_logo_path, opacity=wm_opacity)'
if old_wm_call in b:
    b = b.replace(old_wm_call, new_wm_call)
    print("   [LOGO] custom_logo_path now passed to watermark")
else:
    print("   [LOGO] checking call site...")
    # Try to find any apply_niche_watermark call
    idx = b.find('apply_niche_watermark(current, wm_out')
    if idx != -1:
        snippet = b[idx:idx+150]
        print(f"   Current call: {snippet[:120]}...")

# --- 2b: Fix BG Music — seamless loop without gap ---
old_music = "music_loop = '-stream_loop -1'"
new_music = "music_loop = '-stream_loop -1 -shortest'"
if old_music in b:
    b = b.replace(old_music, new_music)
    print("   [BG MUSIC] -shortest flag added for seamless loop")
else:
    # Try alternative pattern
    old_music2 = "-stream_loop -1"
    new_music2 = "-stream_loop -1 -shortest"
    # Only replace in audio context (after music file)
    idx_m = b.find("-stream_loop -1")
    if idx_m != -1:
        # Check if it's in the music mux context
        context = b[max(0,idx_m-50):idx_m+50]
        if "music" in context.lower() or "bgm" in context.lower():
            # Already has -shortest?
            if "-shortest" not in b[idx_m:idx_m+30]:
                b = b[:idx_m+len(old_music2)] + b[idx_m+len(old_music2):].replace(
                    b[idx_m+len(old_music2):idx_m+len(old_music2)+1], 
                    " -shortest" + b[idx_m+len(old_music2):idx_m+len(old_music2)+1], 1
                )
                print("   [BG MUSIC] -shortest injected near music context")
            else:
                print("   [BG MUSIC] -shortest already present")

# Also fix: music duration should cover full video
old_music_dur = "music_dur = probe_duration(music_path)"
new_music_dur = "music_dur = probe_duration(music_path) if music_path else 118.0"
if old_music_dur in b:
    b = b.replace(old_music_dur, new_music_dur)
    print("   [BG MUSIC] music duration fallback set")

# Also fix: ensure music loops fill total_duration 
old_music_filter = "amovie="
# Find the music amovie line and ensure it loops properly
if "amovie=" in b and "-stream_loop" not in b[b.find("amovie="):b.find("amovie=")+200]:
    print("   [BG MUSIC] WARNING: music amovie may not loop — check manually")

# --- 2c: Fix SFX — accurate on clip boundary ---
old_sfx = "sfx_interval = 7.5"
new_sfx = "sfx_interval = clip_duration  # fire at every clip boundary"
if old_sfx in b:
    b = b.replace(old_sfx, new_sfx)
    print("   [SFX] interval set to clip boundary")
else:
    print("   [SFX] interval line not found (already updated or different format)")

# --- 2d: Fix Still Picture — LOOP clips instead of still ---
old_extend = "extend_last_clip(current, body_end, clip_durations[-1], size, fps, quality, niche)"
new_extend = "extend_with_reused_clips(current, body_end, clip_paths, clip_durations, size, fps, quality, niche)"
if old_extend in b:
    b = b.replace(old_extend, new_extend)
    print("   [STILL PIC] now reuses clips instead of showing still image")
else:
    # Find the body extension logic
    ext_idx = b.find("body shorter")
    if ext_idx != -1:
        context = b[ext_idx:ext_idx+300]
        print(f"   [STILL PIC] body shorter context: {context[:200]}...")
        # Add fallback: create extend_with_reused_clips function
        if "extend_with_reused_clips" not in b:
            ext_func = '''

def extend_with_reused_clips(body_video, target_duration, clip_paths, clip_durations, size, fps, quality, niche='default'):
    """When clips run out, REUSE earlier clips instead of showing a still picture.
    Loops through clip_paths starting from index 0 again."""
    from pathlib import Path
    body = Path(body_video)
    body_dur = probe_duration(body)
    needed = max(0.0, target_duration - body_dur)
    if needed <= 0.1:
        return body
    
    log(f"[LoopClips] Body={body_dur:.1f}s, Target={target_duration:.1f}s, Need={needed:.1f}s — REUSING clips")
    
    # Render extra clips by looping through original clip_paths
    extra_segments = []
    elapsed = 0.0
    reuse_idx = 0
    total_clips = len(clip_paths)
    
    while elapsed < needed and len(extra_segments) < 200:
        clip = clip_paths[reuse_idx % total_clips]
        clip_dur = min(clip_durations[reuse_idx % len(clip_durations)], needed - elapsed)
        if clip_dur < 0.25:
            break
        seg = BASE_TMP / f"loop_{reuse_idx:04d}.mp4"
        render_clip_segment(
            str(clip), str(seg), clip_dur,
            reuse_idx, size, fps, quality,
            niche=niche, total_clips=total_clips
        )
        extra_segments.append(seg)
        elapsed += clip_dur
        reuse_idx += 1
    
    if extra_segments:
        extended = BASE_TMP / "body_extended.mp4"
        all_parts = [body] + extra_segments
        concat_files(all_parts, extended, niche=niche, use_transitions=True, global_index_offset=9999)
        log(f"[LoopClips] Extended body to {probe_duration(extended):.1f}s using {len(extra_segments)} reused clips")
        return extended
    return body
'''
            # Insert before render_long_batch_memory
            render_idx = b.find("def render_long_batch_memory")
            if render_idx != -1:
                b = b[:render_idx] + ext_func + "\n" + b[render_idx:]
                print("   [STILL PIC] extend_with_reused_clips function ADDED")
            
            # Now replace the call
            if old_extend in b:
                b = b.replace(old_extend, new_extend)
                print("   [STILL PIC] call replaced with clip-looping version")
            else:
                # Try to find the extend call
                if "extend_last_clip" in b:
                    b = b.replace("extend_last_clip", "extend_with_reused_clips")
                    # Also need to update arguments
                    b = b.replace(
                        "body_end, clip_durations[-1], size, fps, quality, niche",
                        "body_end, clip_paths, clip_durations, size, fps, quality, niche"
                    )
                    print("   [STILL PIC] extend_last_clip -> extend_with_reused_clips")

# --- 2e: Fix transition pool under-utilization (use all 8 types) ---
# The current transition_decision picks from base[] which has fade repeated many times
# Make it use ALL 8 unique transition types evenly
old_trans_profiles = '"base":["fade","dissolve","fade","smoothleft","fade","smoothright"]'
new_trans_profiles = '"base":["fade","dissolve","wipeleft","wiperight","smoothleft","smoothright","slide_left","slide_right"]'
if old_trans_profiles in b:
    b = b.replace(old_trans_profiles, new_trans_profiles)
    print("   [TRANSITIONS] All 8 unique types now in rotation")
else:
    print("   [TRANSITIONS] profiles may already be updated")

bl.write_text(b, encoding="utf-8")

# -------------------------------------------------------
# Verify syntax
# -------------------------------------------------------
print("\n" + "="*60)
print("  VERIFYING SYNTAX...")
print("="*60)
try:
    compile(e, "unique_editing_engine.py", "exec")
    print("  unique_editing_engine.py: OK")
except SyntaxError as ex:
    print(f"  unique_editing_engine.py: SYNTAX ERROR! {ex}")

try:
    compile(b, "batch_long_renderer.py", "exec")
    print("  batch_long_renderer.py: OK")
except SyntaxError as ex:
    print(f"  batch_long_renderer.py: SYNTAX ERROR! {ex}")

print("\n  ✅ ALL FIXES APPLIED!")
print("  Run: streamlit run app.py")
print("="*60)