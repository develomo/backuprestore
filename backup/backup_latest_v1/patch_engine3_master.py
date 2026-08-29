from pathlib import Path
p = Path("master_pipeline.py")
c = p.read_text(encoding="utf-8")

add = '''# ============================================================
# PHASE 7: DNA-Driven Render Override
# ============================================================
def apply_content_dna_to_render(dna_profile, render_kwargs, clip_index=0):
    try:
        from video_content_analyzer import DNAtoCreativeMapping
        import time
        seed = render_kwargs.get("render_seed", int(time.time()*1000)%99999)
        mp = DNAtoCreativeMapping(seed=seed+clip_index)
        cr = mp.full_profile(dna_profile)
        render_kwargs["_creative_dna"] = cr
        render_kwargs["_motion_direction"] = cr["motion"]["direction"]
        render_kwargs["_zoom_val"] = cr["motion"]["zoom"]
        render_kwargs["_color_params"] = cr["color"]
        render_kwargs["_voice_params"] = cr["voice"]
        render_kwargs["_cut_params"] = cr["cuts"]
    except Exception:
        pass
    return render_kwargs
# ============================================================
'''

mk = "def build_viral_pacing_plan(total_duration"
if mk in c:
    c = c.replace(mk, add + mk)
    p.write_text(c, encoding="utf-8")
    print("DONE: Engine 3 -> master_pipeline.py")
else:
    print("ERROR: marker")