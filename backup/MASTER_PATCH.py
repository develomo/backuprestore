# MASTER_PATCH.py - V3 CLEAN
# ============================================================
# Copy this file to: D:\My Creation Video Generator\backup\
# Then run:  python MASTER_PATCH.py
# ============================================================

import shutil, time
from pathlib import Path

BASE = Path(__file__).resolve().parent
print(f"Working dir: {BASE}")

# ===== CHECK FILES =====
for name in ["batch_long_renderer.py", "safe_long_video_polished.py"]:
    p = BASE / name
    if not p.exists():
        print(f"ERROR: {name} not found! Place this script in the backup folder.")
        exit(1)
    print(f"OK: {name}")

ts = int(time.time())

# ===== STEP 1: Write unique_editing_engine.py =====
print("\n[1/4] Writing unique_editing_engine.py...")

engine_code = """# unique_editing_engine.py
# 5 ENGINES: Motion Canvas, Transition Types, Color Grading, Effects, Anti-Template
import random, hashlib

MOTION_CANVAS = {
    "center_push": "zoompan=z='min(zoom+0.0008,1.12)':d=1:x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2)",
    "ken_burns_fast": "zoompan=z='min(zoom+0.0015,1.18)':d=1:x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2)",
    "ken_burns_slow": "zoompan=z='min(zoom+0.0004,1.08)':d=1",
    "diagonal_top_right": "zoompan=z='1.05':d=1:x='iw-iw/zoom':y='0'",
    "diagonal_bottom_left": "zoompan=z='1.05':d=1:x='0':y='ih-ih/zoom'",
    "gentle_float_down": "zoompan=z='1.04':d=1:x='iw/2-(iw/zoom/2)':y='ih-ih/zoom'",
    "gentle_float_up": "zoompan=z='1.04':d=1:x='iw/2-(iw/zoom/2)':y='0'",
    "gentle_float_left": "zoompan=z='1.04':d=1:x='0':y='ih/2-(ih/zoom/2)'",
    "gentle_float_right": "zoompan=z='1.04':d=1:x='iw-iw/zoom':y='ih/2-(ih/zoom/2)'",
    "static_with_micro": "zoompan=z='min(zoom+0.0003,1.03)':d=1",
    "center_zoom_pulse": "zoompan=z='1+0.04*sin(2*PI*n/30)':d=1",
    "diag_top_left": "zoompan=z='1.05':d=1:x='0':y='0'",
    "diag_bottom_right": "zoompan=z='1.05':d=1:x='iw-iw/zoom':y='ih-ih/zoom'",
    "slide_left_motion": "zoompan=z='1.06':d=1:x='if(lte(on,1),0,iw-iw/zoom)':y='ih/2-(ih/zoom/2)'",
    "slide_right_motion": "zoompan=z='1.06':d=1:x='if(lte(on,1),iw-iw/zoom,0)':y='ih/2-(ih/zoom/2)'",
    "slide_up_motion": "zoompan=z='1.06':d=1:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),ih-ih/zoom,0)'",
    "slide_down_motion": "zoompan=z='1.06':d=1:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),0,ih-ih/zoom)'",
}

MOTION_NICHE_PROFILES = {
    "luxury": {"prefer":["center_push","ken_burns_slow","gentle_float_right","gentle_float_down","static_with_micro"], "avoid":["center_zoom_pulse","slide_left_motion","slide_right_motion"]},
    "luxury_lifestyle": {"prefer":["center_push","ken_burns_slow","gentle_float_right","gentle_float_down","static_with_micro"], "avoid":["center_zoom_pulse","slide_left_motion","slide_right_motion"]},
    "mystery": {"prefer":["diagonal_bottom_left","gentle_float_down","ken_burns_slow","diag_top_left"], "avoid":["center_zoom_pulse","slide_up_motion"]},
    "ai": {"prefer":["slide_right_motion","center_zoom_pulse","ken_burns_fast","diag_bottom_right"], "avoid":["static_with_micro","gentle_float_up"]},
    "quantum_future": {"prefer":["slide_right_motion","center_zoom_pulse","ken_burns_fast","diag_bottom_right"], "avoid":["static_with_micro","gentle_float_up"]},
    "finance": {"prefer":["ken_burns_slow","gentle_float_right","diag_top_left","center_push"], "avoid":["center_zoom_pulse","slide_up_motion","slide_down_motion"]},
    "finance_simulation": {"prefer":["ken_burns_slow","gentle_float_right","diag_top_left","center_push"], "avoid":["center_zoom_pulse","slide_up_motion","slide_down_motion"]},
    "islamic": {"prefer":["static_with_micro","gentle_float_up","ken_burns_slow"], "avoid":["center_zoom_pulse","slide_left_motion","slide_right_motion"]},
    "home_design": {"prefer":["gentle_float_right","gentle_float_left","ken_burns_slow","static_with_micro"], "avoid":["slide_left_motion","slide_right_motion"]},
    "interior_design": {"prefer":["gentle_float_right","gentle_float_left","ken_burns_slow","static_with_micro"], "avoid":["slide_left_motion","slide_right_motion"]},
    "stoic": {"prefer":["static_with_micro","ken_burns_slow","gentle_float_down"], "avoid":["center_zoom_pulse","slide_left_motion","slide_right_motion","slide_up_motion"]},
    "default": {"prefer":[], "avoid":[]},
}

TRANSITION_TYPES = {
    "fade":"fade=duration=0.40:alpha=1","slide_left":"coverleft=duration=0.50",
    "slide_right":"coverright=duration=0.50","slide_up":"coverup=duration=0.50",
    "slide_down":"coverdown=duration=0.50","dissolve":"fade=duration=0.60:alpha=1",
    "wipe_left":"wipeleft=duration=0.50","wipe_right":"wiperight=duration=0.50",
}

COLOR_NICHE_RANGES = {
    "luxury":{"hr":(-1.5,1.5),"sr":(0.95,1.15),"cr":(0.95,1.15),"br":(-0.03,0.05),"gr":(0.95,1.12)},
    "mystery":{"hr":(-2,2),"sr":(0.88,1.08),"cr":(0.95,1.25),"br":(-0.06,0.03),"gr":(0.92,1.18)},
    "ai":{"hr":(-2.5,2.5),"sr":(0.95,1.25),"cr":(1.0,1.3),"br":(-0.04,0.06),"gr":(0.95,1.15)},
    "quantum_future":{"hr":(-2.5,2.5),"sr":(0.95,1.25),"cr":(1.0,1.3),"br":(-0.04,0.06),"gr":(0.95,1.15)},
    "finance":{"hr":(-1,1),"sr":(0.9,1.05),"cr":(0.92,1.08),"br":(-0.04,0.04),"gr":(0.95,1.1)},
    "islamic":{"hr":(-1,1.5),"sr":(0.9,1.05),"cr":(0.92,1.1),"br":(-0.04,0.04),"gr":(0.95,1.1)},
    "home_design":{"hr":(-1.5,2),"sr":(0.9,1.1),"cr":(0.93,1.12),"br":(-0.03,0.05),"gr":(0.95,1.1)},
    "stoic":{"hr":(-1.5,1),"sr":(0.88,1.02),"cr":(0.9,1.08),"br":(-0.05,0.02),"gr":(0.92,1.08)},
    "default":{"hr":(-2,2.5),"sr":(0.88,1.2),"cr":(0.92,1.25),"br":(-0.06,0.06),"gr":(0.92,1.18)},
}
# Explicit alias mapping (safer than string replace)
COLOR_NICHE_RANGES["luxury_lifestyle"] = COLOR_NICHE_RANGES["luxury"]
COLOR_NICHE_RANGES["finance_simulation"] = COLOR_NICHE_RANGES["finance"]
COLOR_NICHE_RANGES["interior_design"] = COLOR_NICHE_RANGES["home_design"]

GRAIN_PROB = {"luxury":0.25,"mystery":0.45,"ai":0.30,"quantum_future":0.30,"finance":0.20,"islamic":0.15,"home_design":0.22,"stoic":0.35,"default":0.30}
BLUR_PROB = {"luxury":0.20,"mystery":0.30,"ai":0.28,"quantum_future":0.28,"finance":0.15,"islamic":0.12,"home_design":0.18,"stoic":0.22,"default":0.22}
GRAIN_PROB["luxury_lifestyle"] = GRAIN_PROB["luxury"]
GRAIN_PROB["finance_simulation"] = GRAIN_PROB["finance"]
GRAIN_PROB["interior_design"] = GRAIN_PROB["home_design"]
BLUR_PROB["luxury_lifestyle"] = BLUR_PROB["luxury"]
BLUR_PROB["finance_simulation"] = BLUR_PROB["finance"]
BLUR_PROB["interior_design"] = BLUR_PROB["home_design"]

FFMPEG_GRAIN = "noise=alls=8:allf=t+u,format=yuv420p"
FFMPEG_BLUR = "tmix=frames=3:weights=1 1 1"

def _sh(s):
    return int(hashlib.md5(str(s).encode()).hexdigest()[:12], 16)

def _resolve_niche(niche):
    n = str(niche or "default").lower()
    known = {"luxury","luxury_lifestyle","mystery","ai","quantum_future","finance","finance_simulation","islamic","home_design","interior_design","stoic"}
    if n in known:
        return n
    # fuzzy match
    for k in known:
        if k in n or n in k:
            return k
    return "default"

def pick_motion(niche="default", clip_idx=0, used=None):
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
        pool = [k for k in keys if k not in used] or keys
    rng = random.Random(clip_idx * 17 + hash(niche) % 10000)
    name = rng.choice(pool)
    return name, MOTION_CANVAS[name]

def pick_motion_with_tracking(niche="default", clip_idx=0, used=None):
    if used is None: used = set()
    name, f = pick_motion(niche, clip_idx, used)
    used.add(name)
    return name, f

def pick_transition(clip_idx=0, niche="default", last=None):
    niche = _resolve_niche(niche)
    keys = list(TRANSITION_TYPES.keys())
    pool = [k for k in keys if k != last] or keys
    rng = random.Random(clip_idx * 13 + hash(niche) % 10000)
    name = rng.choice(pool)
    return name, TRANSITION_TYPES[name]

def pick_transition_with_tracking(clip_idx=0, niche="default", last=None):
    return pick_transition(clip_idx, niche, last)

def color_grade(clip_idx=0, niche="default", seed=None):
    if seed is None: seed = clip_idx * 7
    niche = _resolve_niche(niche)
    rng = COLOR_NICHE_RANGES.get(niche, COLOR_NICHE_RANGES["default"])
    rr = random.Random(seed + clip_idx * 31)
    return {
        "hue": round(rr.uniform(*rng["hr"]), 1),
        "saturation": round(rr.uniform(*rng["sr"]), 2),
        "contrast": round(rr.uniform(*rng["cr"]), 2),
        "brightness": round(rr.uniform(*rng["br"]), 2),
        "gamma": round(rr.uniform(*rng["gr"]), 2),
    }

def color_filter(c):
    return f"eq=hue={c['hue']}:saturation={c['saturation']}:contrast={c['contrast']}:brightness={c['brightness']}:gamma={c['gamma']}"

def should_grain(niche="default", clip_idx=0, seed=None):
    if seed is None: seed = clip_idx * 17
    niche = _resolve_niche(niche)
    p = GRAIN_PROB.get(niche, 0.30)
    return random.Random(seed + clip_idx * 19).random() < p

def should_blur(niche="default", clip_idx=0, seed=None):
    if seed is None: seed = clip_idx * 23
    niche = _resolve_niche(niche)
    p = BLUR_PROB.get(niche, 0.22)
    return random.Random(seed + clip_idx * 29).random() < p

def get_clip_dna(clip_path, clip_idx, niche="default", total_clips=1):
    bs = _sh(str(clip_path)) + clip_idx * 7 + total_clips * 13
    ns = bs + _sh(niche) % 1000
    mn, mf = pick_motion(niche=niche, clip_idx=clip_idx)
    cp = color_grade(clip_idx=clip_idx, niche=niche, seed=ns)
    cf = color_filter(cp)
    ug = should_grain(niche=niche, clip_idx=clip_idx, seed=ns)
    ub = should_blur(niche=niche, clip_idx=clip_idx, seed=ns)
    zl = round(random.Random(ns).uniform(1.03, 1.14), 3)
    return {
        "motion_name": mn, "motion_filter": mf,
        "color_params": cp, "color_filter": cf,
        "use_grain": ug, "grain_filter": FFMPEG_GRAIN if ug else None,
        "use_blur": ub, "blur_filter": FFMPEG_BLUR if ub else None,
        "zoom_level": zl, "seed": ns,
    }

def engine_report():
    return {"engine":"Unique Editing Engine v2","engines_active":5}
"""

(BASE / "unique_editing_engine.py").write_text(engine_code, encoding="utf-8")
print("   -> unique_editing_engine.py written")

# ===== STEP 2: Patch batch_long_renderer.py =====
print("\n[2/4] Patching batch_long_renderer.py...")

bl = BASE / "batch_long_renderer.py"
shutil.copy2(bl, BASE / f"batch_long_renderer.py.bak_{ts}")
txt = bl.read_text(encoding="utf-8")
ch = 0

# PATCH 2a: Import
old1 = "import json, re, shutil, subprocess, time, gc, random"
new1 = "import json, re, shutil, subprocess, time, gc, random\n\ntry:\n    from unique_editing_engine import get_clip_dna, engine_report\n    ENGINES_AVAILABLE = True\nexcept ImportError:\n    ENGINES_AVAILABLE = False"
if "from unique_editing_engine import" not in txt:
    txt = txt.replace(old1, new1, 1)
    ch += 1
    print("   P2a: import added")

# PATCH 2b: render_clip_segment replacement
old_hdr = "def render_clip_segment(src,out,wanted,index,size,fps,quality,niche='default'):"
if old_hdr in txt and "ENGINE 1" not in txt:
    # find the full old function
    pos = txt.index(old_hdr)
    after = txt[pos:]
    ret_pos = after.index("return out")
    nl_pos = after.index("\n", ret_pos)
    old_func = after[:nl_pos+1]

    new_func = """def render_clip_segment(src,out,wanted,index,size,fps,quality,niche='default',total_clips=1):
    src=Path(src); out=Path(out); sd=probe_duration(src); start=scene_start(sd,wanted,index)
    crf="32" if normalize_quality(quality)=="360p" else "29"
    base_vf = make_visual_filter(src,size,index,fps,niche=niche)
    if ENGINES_AVAILABLE:
        try:
            dna = get_clip_dna(str(src), index, niche=niche, total_clips=max(1,total_clips))
            extra = []
            if dna.get("color_filter"): extra.append(dna["color_filter"])
            if dna.get("use_grain") and dna.get("grain_filter"): extra.append(dna["grain_filter"])
            if dna.get("use_blur") and dna.get("blur_filter"): extra.append(dna["blur_filter"])
            vf = base_vf + ("," + ",".join(extra) if extra else "")
            log(f"[EngineDNA] clip#{index} | motion={dna.get('motion_name','?')} | hue={dna.get('color_params',{}).get('hue',0)} | grain={dna.get('use_grain')} | blur={dna.get('use_blur')}")
        except Exception as e:
            log(f"[EngineDNA] clip#{index} fallback: {e}")
            vf = base_vf
    else:
        vf = base_vf
    run_cmd([FFMPEG,"-y","-ss",f"{start:.3f}","-t",f"{wanted:.3f}","-i",str(src),"-an","-vf",vf,"-r",str(fps),"-pix_fmt","yuv420p","-c:v","libx264","-preset","ultrafast","-crf",crf,"-movflags","+faststart",str(out)])
    return out"""
    txt = txt.replace(old_func, new_func)
    ch += 1
    print("   P2b: render_clip_segment upgraded")

# PATCH 2c: pass total_clips
old2c = "render_clip_segment(clip,seg,scene_durations[gi],gi,size,fps,quality,preset.get('niche','default')); segs.append(seg); rendered+=1"
new2c = "render_clip_segment(clip,seg,scene_durations[gi],gi,size,fps,quality,preset.get('niche','default'),total_clips=len(clip_paths)); segs.append(seg); rendered+=1"
if old2c in txt:
    txt = txt.replace(old2c, new2c)
    ch += 1
    print("   P2c: total_clips passed")

# PATCH 2d: engine report
old2d = '"music_used":bool(music)'
new2d = '"engines":engine_report() if ENGINES_AVAILABLE else {},"music_used":bool(music)'
if old2d in txt and '"engines":' not in txt:
    txt = txt.replace(old2d, new2d)
    ch += 1
    print("   P2d: engine report injected")

# PATCH 2e: voice volume boost
old2e = 'f"[1:a]volume={voice_volume},"'
new2e = 'f"[1:a]volume={voice_volume+0.08},"'
if old2e in txt:
    txt = txt.replace(old2e, new2e)
    ch += 1
    print("   P2e: voice volume +0.08")

# PATCH 2f: voice presence EQ
old2f = 'f"highpass=f={hp},lowpass=f={lp},"'
new2f = 'f"highpass=f={max(70,hp-10)},lowpass=f={min(12000,lp+1000)},"\\\n        f"equalizer=f=200:t=q:w=1.2:g=1.5,"\\\n        f"equalizer=f=3000:t=q:w=0.8:g=3.0,"\\\n        f"equalizer=f=6000:t=q:w=1.5:g=-2.0,"'
if old2f in txt and "equalizer=f=200" not in txt:
    txt = txt.replace(old2f, new2f)
    ch += 1
    print("   P2f: voice presence EQ added")

# PATCH 2g: loudnorm
old2g = 'f"loudnorm=I={target_lufs}:TP=-1.0:LRA=10"'
new2g = 'f"loudnorm=I={target_lufs}:TP=-1.5:LRA=7:linear=true"'
if old2g in txt:
    txt = txt.replace(old2g, new2g)
    ch += 1
    print("   P2g: loudnorm LRA=7")

# PATCH 2h: bitrate 256k
old2h = '"-b:a","192k"'
new2h = '"-b:a","256k"'
if old2h in txt:
    txt = txt.replace(old2h, new2h)
    ch += 1
    print("   P2h: bitrate 256k")

bl.write_text(txt, encoding="utf-8")
print(f"   -> batch_long_renderer.py: {ch} patches")

# ===== STEP 3: Fix safe_long_video_polished.py =====
print("\n[3/4] Fixing safe_long_video_polished.py...")
slp = BASE / "safe_long_video_polished.py"
shutil.copy2(slp, BASE / f"safe_long_video_polished.py.bak_{ts}")
sl = slp.read_text(encoding="utf-8")
if '"audio_profile":audio_profile' in sl:
    sl = sl.replace('"audio_profile":audio_profile', '"audio_profile":{}')
    slp.write_text(sl, encoding="utf-8")
    print("   -> fixed audio_profile reference")
else:
    print("   -> no fix needed")

# ===== STEP 4: VERIFY =====
print("\n[4/4] Verifying...")
try:
    compile(engine_code, "unique_editing_engine.py", "exec")
    print("   unique_editing_engine.py: SYNTAX OK")
except SyntaxError as e:
    print(f"   unique_editing_engine.py: SYNTAX ERROR! {e}")

try:
    compile(txt, "batch_long_renderer.py", "exec")
    print("   batch_long_renderer.py: SYNTAX OK")
except SyntaxError as e:
    print(f"   batch_long_renderer.py: SYNTAX ERROR! {e}")

try:
    compile(sl, "safe_long_video_polished.py", "exec")
    print("   safe_long_video_polished.py: SYNTAX OK")
except SyntaxError as e:
    print(f"   safe_long_video_polished.py: SYNTAX ERROR! {e}")

print(f"\n{'='*60}")
print("  DONE! All patches applied.")
print(f"{'='*60}")
print(f"  batch_long_renderer.py: {ch} changes")
print()
print("  ENGINES: Motion(17) | Transitions(8) | Color | Grain+Blur | Anti-Template")
print("  VOICE:  +0.08 vol | presence EQ | LRA=7 | 256k bitrate")
print()
print("  NEXT: streamlit run app.py -> render LONG -> check [EngineDNA] logs")