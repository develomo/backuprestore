from pathlib import Path
p = Path("batch_long_renderer.py")
c = p.read_text(encoding="utf-8")

add = '''# ============================================================
# PHASE 7: Engine 2 - Creative Variation (DNA-driven, anti-repeat)
# ============================================================
DNA_ENGINE_AVAILABLE = False
try:
    from video_content_analyzer import ContentDNAAnalyzer, DNAtoCreativeMapping, ProjectDNAAggregator
    DNA_ENGINE_AVAILABLE = True
except Exception:
    ContentDNAAnalyzer = None; DNAtoCreativeMapping = None; ProjectDNAAggregator = None

_CREATIVE_STATE = {
    "render_seed": 0, "motion_history": [], "cut_history": [],
    "color_history": [], "voice_history": [],
    "anti_repeat_window": 5, "creative_fatigue": 0.0,
}

def reset_creative_state(seed=None):
    import random, time
    _CREATIVE_STATE["render_seed"] = seed or int(time.time() * 1000) % 99999
    _CREATIVE_STATE["motion_history"] = []
    _CREATIVE_STATE["cut_history"] = []
    _CREATIVE_STATE["color_history"] = []
    _CREATIVE_STATE["voice_history"] = []
    _CREATIVE_STATE["creative_fatigue"] = 0.0

def get_creative_variation(clip_index, clip_path=None, dna_profile=None, niche=None, preset_number=1):
    import random, hashlib
    rng = random.Random(_CREATIVE_STATE["render_seed"] + clip_index * 7 + preset_number * 13)
    if DNA_ENGINE_AVAILABLE and dna_profile:
        mapper = DNAtoCreativeMapping(seed=_CREATIVE_STATE["render_seed"] + clip_index)
        creative = mapper.full_profile(dna_profile)
    else:
        motion_pool = ["ken_burns_slow","gentle_float_up","gentle_float_down",
                        "zoom_in_fast","pan_right","pan_left",
                        "top_right_diag","bottom_left_diag","center_push","static_hold"]
        zoom_base = 1.01 + rng.uniform(0.005, 0.04)
        direction = rng.choice(motion_pool)
        creative = {
            "motion": {"direction": direction, "zoom": round(zoom_base, 4)},
            "cuts": {"duration": round(rng.uniform(2.5, 7.0), 2),
                     "transition": rng.choice(["hard_cut","soft_dissolve","crossfade"])},
            "color": {"saturation_boost": round(1.0+rng.uniform(-0.05,0.1),3),
                      "contrast_boost": round(1.0+rng.uniform(-0.03,0.06),3)},
            "voice": {"compression_ratio": round(1.5+rng.uniform(-0.1,0.2),2),
                      "lra_target": round(6.0+rng.uniform(-1.0,1.0),1)},
        }
        h = hashlib.md5
        creative["dna_hash"] = h(f"seed{_CREATIVE_STATE['render_seed']}_clip{clip_index}".encode()).hexdigest()[:8]
        creative["creative_sig"] = h(f"var{_CREATIVE_STATE['render_seed']}_{clip_index}_{rng.random()}".encode()).hexdigest()[:8]
    aw = _CREATIVE_STATE["anti_repeat_window"]
    md = creative["motion"]["direction"]
    recent = _CREATIVE_STATE["motion_history"][-aw:]
    if md in recent:
        alts = ["gentle_float_up","gentle_float_down","zoom_in_fast",
                "pan_right","pan_left","ken_burns_slow","center_push","static_hold"]
        for a in alts:
            if a not in recent:
                creative["motion"]["direction"] = a
                break
    _CREATIVE_STATE["motion_history"].append(creative["motion"]["direction"])
    _CREATIVE_STATE["cut_history"].append(creative["cuts"]["duration"])
    _CREATIVE_STATE["color_history"].append(creative["color"])
    _CREATIVE_STATE["voice_history"].append(creative["voice"])
    _CREATIVE_STATE["creative_fatigue"] = min(0.3, _CREATIVE_STATE["creative_fatigue"] + 0.01)
    return creative
# ============================================================
'''

mk = "def get_preset_by_number(niche, num): return None"
if mk in c:
    c = c.replace(mk, add + mk)
    p.write_text(c, encoding="utf-8")
    print("DONE: Engine 2 -> batch_long_renderer.py")
else:
    print("ERROR: marker")