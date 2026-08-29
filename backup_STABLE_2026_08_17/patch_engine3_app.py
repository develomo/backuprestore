from pathlib import Path
p = Path("app.py")
c = p.read_text(encoding="utf-8")

add = '''# ============================================================
# PHASE 7: Engine 3 - Auto-Decision Pipeline (AI decides everything)
# ============================================================
DNA_DECISION_AVAILABLE = False
try:
    from video_content_analyzer import ContentDNAAnalyzer, DNAtoCreativeMapping, ProjectDNAAggregator
    DNA_DECISION_AVAILABLE = True
except Exception:
    pass

def full_auto_decision_engine(script_text=None, clip_paths=None, mode=None):
    import random, time
    clip_paths = clip_paths or []
    result = {
        "niche": "default", "preset_number": 1, "confidence": 0.5,
        "reasoning": "Auto", "creative_profile": {}, "project_dna": {},
        "render_seed": int(time.time() * 1000) % 999999,
    }
    if DNA_DECISION_AVAILABLE and clip_paths:
        try:
            ana = ContentDNAAnalyzer()
            dnas = ana.analyze_multiple(clip_paths)
            if dnas:
                agg = ProjectDNAAggregator(seed=result["render_seed"])
                pdna = agg.aggregate(dnas)
                result["project_dna"] = pdna
                dt = pdna.get("dominant_type", "mixed")
                ae = pdna.get("avg_energy", 0.5)
                nmap = {
                    "talking_head": "stoic_wisdom",
                    "action": "quantum_future" if ae > 0.6 else "mystery",
                    "b_roll": "luxury_lifestyle",
                    "landscape": "interior_design",
                    "product": "finance_simulation",
                    "text_graphic": "quantum_future",
                }
                result["niche"] = nmap.get(dt, "default")
                if ae > 0.8: result["preset_number"] = 7 + (result["render_seed"] % 2)
                elif ae > 0.6: result["preset_number"] = 5 + (result["render_seed"] % 3)
                elif ae > 0.4: result["preset_number"] = 3 + (result["render_seed"] % 3)
                else: result["preset_number"] = 1 + (result["render_seed"] % 3)
                mapr = DNAtoCreativeMapping(seed=result["render_seed"])
                profs = []
                for i, dna in enumerate(dnas):
                    prof = mapr.full_profile(dna)
                    prof["clip_index"] = i
                    profs.append(prof)
                result["creative_profile"] = {
                    "per_clip": profs,
                    "project_direction": pdna.get("creative_direction","balanced"),
                    "project_variant": pdna.get("creative_variant","smooth"),
                }
                result["confidence"] = 0.5 + len(dnas) * 0.06
                result["reasoning"] = dt + "/" + str(round(ae,2))
        except Exception as e:
            result["reasoning"] = str(e)[:80]
    if not result["creative_profile"]:
        x = auto_detect_niche_and_preset(script_text, clip_paths)
        result["niche"] = x[0]
        result["preset_number"] = x[1]
        result["confidence"] = x[2]
        result["reasoning"] = x[3]
    return result

def get_auto_decision_for_ui(script_text=None, clip_paths=None, mode=None):
    d = full_auto_decision_engine(script_text, clip_paths, mode)
    return {
        "niche": d["niche"],
        "preset_number": d["preset_number"],
        "confidence": round(d["confidence"]*100,1),
        "reasoning": d["reasoning"],
        "creative_direction": d.get("creative_profile",{}).get("project_direction","auto"),
        "clip_count": d.get("project_dna",{}).get("clip_count",0),
        "render_seed": d["render_seed"],
    }
# ============================================================
'''

mk = "def get_all_presets(): return {}"
if mk in c:
    c = c.replace(mk, add + mk)
    p.write_text(c, encoding="utf-8")
    print("DONE: Engine 3 -> app.py")
else:
    print("ERROR: marker")