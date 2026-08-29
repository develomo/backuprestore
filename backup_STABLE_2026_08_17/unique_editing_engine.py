# unique_editing_engine.py
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
    # Exact match aliases
    if n == "interior": return "home_design"
    if n == "luxury": return "luxury"
    if n == "finance": return "finance"
    if n in known: return n
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
        for k in keys:
            pool.extend([k] * 3)
    if not pool:
        name = keys[0] if keys else "center_push"
        filt = MOTION_CANVAS.get(name, MOTION_CANVAS.get("center_push","zoompan=z='1.04':d=1"))
        return name, filt
    rng = random.Random(clip_idx * 17 + hash(niche) % 10000)
    name = rng.choice(pool)
    filt = MOTION_CANVAS.get(name, MOTION_CANVAS.get("center_push","zoompan=z='1.04':d=1"))
    return name, filt

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
