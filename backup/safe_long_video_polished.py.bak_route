# safe_long_video_polished.py
# STABLE LONG CONTROLLER: UI uploads -> batch_long_renderer.py timing fix
from __future__ import annotations
from pathlib import Path


import subprocess, json, itertools
from pathlib import Path


def _get_audio_duration(audio_path):
    import subprocess, json
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(audio_path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return float(json.loads(r.stdout)["format"]["duration"])
    except:
        return 30.0  # fallback

def _distribute_clips(clips, target_duration, voice_duration=None):
    """
    FIXED: Ab clips ko blindly repeat NAHI karega. 
    Renderer (batch_long_renderer.py) khud sequential parts banayega aur 
    150 clips ko 150 unique parts ke tor pe use karega. 
    Sirf tab wrap-around hoga jab saare clips exhaust ho jayen.
    """
    if not clips:
        return clips
    print(f"[ClipDist] Passing {len(clips)} unique clips to renderer for sequential processing.")
    return list(clips)

import json, time, traceback

VIDEO_EXTS={".mp4",".mov",".mkv",".avi",".webm",".m4v"}
AUDIO_EXTS={".mp3",".wav",".m4a",".aac",".flac",".ogg"}
IMAGE_EXTS={".png",".jpg",".jpeg",".webp"}
ROOT=Path(__file__).resolve().parent; ASSETS=ROOT/"assets"/"long"; OUTPUT_DIR=ROOT/"outputs"; OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
DEFAULT_SETTINGS={"edit_quality":"480p","final_quality":"480p","batch_size":8,"fps":24,"hidden_upscale":False}

def safe_print(x):
    try: print(str(x), flush=True)
    except Exception: pass

def natural_key(path):
    s=Path(path).stem; out=[]; cur=""
    for ch in s:
        if ch.isdigit(): cur+=ch
        else:
            if cur: out.append((0,int(cur))); cur=""
            out.append((1,ch.lower()))
    if cur: out.append((0,int(cur)))
    return out

def existing_files(items,exts=None):
    out=[]
    for item in items or []:
        try:
            p=Path(item)
            if p.exists() and p.is_file() and (exts is None or p.suffix.lower() in exts): out.append(p)
        except Exception: pass
    return sorted(out,key=natural_key)

def first_file(items,exts=None):
    xs=existing_files(items,exts); return xs[0] if xs else None

def folder_files(folder,exts):
    folder=Path(folder)
    if not folder.exists(): return []
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts],key=natural_key)

def list_long_assets():
    return {"voices":folder_files(ASSETS/"voices",AUDIO_EXTS),"clips":folder_files(ASSETS/"clips",VIDEO_EXTS),"music":folder_files(ASSETS/"music",AUDIO_EXTS),"sfx":folder_files(ASSETS/"sfx",AUDIO_EXTS),"intro":folder_files(ASSETS/"intro",VIDEO_EXTS),"hook":folder_files(ASSETS/"hook",VIDEO_EXTS),"outro":folder_files(ASSETS/"outro",VIDEO_EXTS),"subscribe":folder_files(ASSETS/"subscribe",IMAGE_EXTS|VIDEO_EXTS),"subscribe_overlay":folder_files(ASSETS/"subscribe_overlay",IMAGE_EXTS|VIDEO_EXTS),"overlays":folder_files(ASSETS/"overlays",IMAGE_EXTS|VIDEO_EXTS)}

def _flatten(value):
    if value is None: return []
    if isinstance(value,(str,Path)): return [value]
    if isinstance(value,dict):
        out=[]
        for v in value.values(): out.extend(_flatten(v))
        return out
    if isinstance(value,(list,tuple,set)):
        out=[]
        for item in value: out.extend(_flatten(item))
        return out
    return [value]

def choose_voice(voice_path,kwargs,assets):
    items=[]; items+=_flatten(voice_path)
    for name in ("voice","voice_file","long_voice","uploaded_voice","long_assets"): items+=_flatten(kwargs.get(name))
    f=first_file(items,AUDIO_EXTS)
    if f: return f
    if assets["voices"]: return assets["voices"][0]
    raise FileNotFoundError("Long voice missing")

def choose_clips(clips,kwargs,assets):
    items=[]; items+=_flatten(clips)
    for name in ("video_clips","clip_files","long_clips","uploaded_clips","long_assets"): items+=_flatten(kwargs.get(name))
    fs=existing_files(items,VIDEO_EXTS)
    if fs: return fs
    if assets["clips"]: return assets["clips"]
    raise FileNotFoundError("Long clips missing")

def choose_music(music_path,kwargs,assets):
    items=[]; items+=_flatten(music_path)
    for name in ("music","bg_music","background_music","long_music","uploaded_music","long_assets"): items+=_flatten(kwargs.get(name))
    f=first_file(items,AUDIO_EXTS)
    if f: return f
    return assets["music"][0] if assets["music"] else None

def choose_sfx(sfx_files,kwargs,assets):
    items=[]; items+=_flatten(sfx_files)
    for name in ("sfx","sfx_files","long_sfx","uploaded_sfx","long_assets"): items+=_flatten(kwargs.get(name))
    fs=existing_files(items,AUDIO_EXTS)
    return fs if fs else assets["sfx"]

def choose_intro(kwargs,assets):
    items=[]
    for name in ("intro_path","intro","intro_file","hook_path","hook","long_intro","uploaded_intro","long_assets"): items+=_flatten(kwargs.get(name))
    f=first_file(items,VIDEO_EXTS)
    if f: return f
    if assets["intro"]: return assets["intro"][0]
    if assets["hook"]: return assets["hook"][0]
    return None

def choose_outro(kwargs,assets):
    items=[]
    for name in ("outro_path","outro","outro_file","long_outro","uploaded_outro","long_assets"): items+=_flatten(kwargs.get(name))
    f=first_file(items,VIDEO_EXTS)
    if f: return f
    return assets["outro"][0] if assets["outro"] else None

def choose_subscribe_overlay(kwargs,assets):
    items=[]
    for name in ("subscribe_overlay","subscribe_overlay_path","subscribe_path","subscribe","subscribe_file","overlay","overlays","long_subscribe","uploaded_subscribe","long_assets"): items+=_flatten(kwargs.get(name))
    f=first_file(items,IMAGE_EXTS)
    if f: return f
    f=first_file(items,VIDEO_EXTS)
    if f: return f
    for group in ("subscribe","subscribe_overlay","overlays"):
        if assets.get(group):
            f=first_file(assets[group],IMAGE_EXTS) or first_file(assets[group],VIDEO_EXTS)
            if f: return f
    return None

def normalize_quality(value):
    q=str(value or DEFAULT_SETTINGS["edit_quality"]).lower()
    if q in {"high","balanced","edit","fast","max","1080p","4k","2160p"}: return DEFAULT_SETTINGS["edit_quality"]
    if "720" in q: return "720p"
    if "360" in q: return "360p"
    return "480p"

def caption_enabled(add_captions, caption_mode, style_id=None):
    # FIXED: Ab UI ka checkbox respect hoga. Agar False hai toh Whisper/Caption skip hoga.
    return bool(add_captions)

def run_integrated_long_pipeline(voice_path=None,clips=None,words=None,words_path=None,transcript_text=None,output_path=None,niche="default",render_count=0,caption_mode="phrase",style_id=None,music_path=None,sfx_files=None,use_hook=True,hook_text=None,use_overlays=True,final_4k=False,fps=24,quality=None,clean_silence=False,add_captions=True,preset_overrides=None,custom_logo_path=None,wm_opacity=0.6,**kwargs):
    from batch_long_renderer import render_long_batch_memory
    started=time.time(); assets=list_long_assets(); preset=dict(preset_overrides or {})
    q=normalize_quality(preset.get("quality",preset.get("batch_quality",quality or DEFAULT_SETTINGS["edit_quality"]))); fps_val=min(24,max(12,int(preset.get("fps",fps or DEFAULT_SETTINGS["fps"])))); batch_size=min(2, int(preset.get("batch_size", 2) or 2))  # Phase 5: Force batch_size=2 for RAM safety
    caption_profile=get_long_caption_profile(niche=niche,style_id=style_id,caption_mode=caption_mode)
    audio_profile=get_long_audio_profile(niche=niche)
    preset.update({"quality":q,"final_quality":"480p","hidden_upscale":False,"intro_seconds": 1.5,"outro_seconds": 2.0,"voice_start_offset": 1.5,"target_aspect":"16:9","force_clip_aspect_ratio":"16:9","force_final_aspect_ratio":"16:9","module1_motion_engine":True,"module2_transition_engine":True,"module3_caption_engine":True,"module4_audio_engine":True,"audio_profile":{},"module2_transition_engine":True,"module3_caption_engine":True,"module4_audio_engine":True,"audio_profile":{},"subscribe_position":"8min","subscribe_target_second":480.0,"chroma_key_subscribe":True,"caption_style_lock":True,"module3_caption_engine":True,"module4_audio_engine":True,"audio_profile":{},"caption_profile":caption_profile,"audio_profile":{},"module1_motion_engine":True,"module2_transition_engine":True,"module3_caption_engine":True,"module4_audio_engine":True,"audio_profile":{},"module2_transition_engine":True,"module3_caption_engine":True,"module4_audio_engine":True,"audio_profile":{},"niche":niche,"target_aspect":"16:9","force_clip_aspect_ratio":"16:9","force_final_aspect_ratio":"16:9","module1_motion_engine":True,"module2_transition_engine":True,"module3_caption_engine":True,"module4_audio_engine":True,"audio_profile":{},"module2_transition_engine":True,"module3_caption_engine":True,"module4_audio_engine":True,"audio_profile":{},"no_stretch":True,"no_letterbox":True,"transition_engine":"xfade","transition_mix":"80_smooth_20_creative"})
    voice=choose_voice(voice_path,kwargs,assets); # ---- FIXED CLIP DISTRIBUTION ----
    voice_duration = _get_audio_duration(voice)
    clip_list = _distribute_clips(choose_clips(clips, kwargs, assets), target_duration=voice_duration); music=choose_music(music_path,kwargs,assets); sfx=choose_sfx(sfx_files,kwargs,assets); intro=choose_intro(kwargs,assets) if use_hook else None; outro=choose_outro(kwargs,assets); subscribe=choose_subscribe_overlay(kwargs,assets) if use_overlays else None; # Phase 5: Captions OFF by default for long videos to save RAM
    # Only enable if user explicitly checked the box
    if add_captions is False:
        cap_on = False
    else:
        cap_on = caption_enabled(add_captions, caption_mode, style_id)
    out=Path(output_path) if output_path else OUTPUT_DIR/f"final_long_stable_{int(time.time())}.mp4"; out.parent.mkdir(parents=True,exist_ok=True)
    safe_print(f"[SafeLongStable] render | clips={len(clip_list)} | quality={q} | captions={cap_on} | intro={bool(intro)} | outro={bool(outro)} | subscribe_mid={bool(subscribe)}")
    try:
        final=render_long_batch_memory(voice_path=voice,clips=clip_list,output_path=out,music_path=music,sfx_files=sfx,intro_path=intro,outro_path=outro,subscribe_overlay=subscribe,quality=q,fps=fps_val,batch_size=batch_size,final_quality="480p",add_captions=cap_on,words=words,words_path=words_path,transcript_text=transcript_text,caption_mode=caption_mode,style_id=caption_profile.get("selected_style_id",style_id),cleanup=True,preset_overrides=preset,custom_logo_path=custom_logo_path,wm_opacity=wm_opacity)
        meta={"engine":"safe_long_stable_controller","final":str(final),"clips":len(clip_list),"quality":q,"fps":fps_val,"batch_size":batch_size,"captions":cap_on,"caption_mode":caption_mode,"style_id_locked":caption_profile.get("selected_style_id",style_id),"caption_profile":caption_profile,"audio_profile":{},"subscribe_overlay_8min":str(subscribe) if subscribe else None,"intro":str(intro) if intro else None,"outro":str(outro) if outro else None,"music":str(music) if music else None,"sfx_count":len(sfx),"hidden_upscale":False,"intro_seconds": 1.5,"outro_seconds": 2.0,"voice_start_offset": 1.5,"target_aspect":"16:9","force_clip_aspect_ratio":"16:9","force_final_aspect_ratio":"16:9","module1_motion_engine":True,"module2_transition_engine":True,"module3_caption_engine":True,"module4_audio_engine":True,"audio_profile":{},"module2_transition_engine":True,"module3_caption_engine":True,"module4_audio_engine":True,"audio_profile":{},"seconds":round(time.time()-started,2)}
        try: Path(final).with_suffix(".safe_long_stable.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
        except Exception: pass
        return final
    except Exception:
        try: (OUTPUT_DIR/f"safe_long_stable_error_{int(time.time())}.json").write_text(json.dumps({"engine":"safe_long_stable_controller","error":traceback.format_exc(),"seconds":round(time.time()-started,2)},indent=2),encoding="utf-8")
        except Exception: pass
        raise

def generate_long(**kwargs): return run_integrated_long_pipeline(**kwargs)
def run_pipeline(**kwargs): return run_integrated_long_pipeline(**kwargs)
def run_long_pipeline(**kwargs): return run_integrated_long_pipeline(**kwargs)
def safe_long_rewrite_report():
    return {"controller":"safe_long_stable_controller","captions_supported":True,"caption_style_locked_to_ui":True,"subscribe_overlay_8min":True,"subscribe_green_screen_chroma_key":True,"intro_seconds": 1.5,"outro_seconds": 2.0,"voice_starts_after_intro":True,"outro_silent":True,"fixed_output_aspect_ratio":"16:9","module3_caption_engine":True,"module4_audio_engine":True,"audio_profile":{},"auto_caption_profiles":True,"every_clip_aspect_ratio":"16:9","module2_transition_engine":True,"module3_caption_engine":True,"module4_audio_engine":True,"audio_profile":{},"transition_engine":"xfade","final_video_aspect_ratio":"16:9","hidden_upscale":False}
if __name__=="__main__": print(json.dumps(safe_long_rewrite_report(),indent=2))


# ============================================================
# MODULE 3 - LONG PIPELINE CAPTION PROFILE MANAGER
# ============================================================

CAPTION_PROFILES_MODULE3 = {
    "luxury": {
        "auto_style_id": "luxury_gold",
        "caption_mode": "phrase",
        "font_family": "Segoe UI Semibold",
        "color": "gold_orange",
        "max_words": 4,
        "max_chars": 42,
    },
    "mystery": {
        "auto_style_id": "mystery_white",
        "caption_mode": "phrase",
        "font_family": "Segoe UI Semibold",
        "color": "white_black_stroke",
        "max_words": 3,
        "max_chars": 36,
    },
    "ai": {
        "auto_style_id": "ai_cyan",
        "caption_mode": "phrase",
        "font_family": "Segoe UI Semibold",
        "color": "cyan_white",
        "max_words": 4,
        "max_chars": 40,
    },
    "quantum_future": {
        "auto_style_id": "ai_cyan",
        "caption_mode": "phrase",
        "font_family": "Segoe UI Semibold",
        "color": "cyan_white",
        "max_words": 4,
        "max_chars": 40,
    },
    "finance": {
        "auto_style_id": "finance_blue",
        "caption_mode": "phrase",
        "font_family": "Segoe UI Semibold",
        "color": "clean_blue",
        "max_words": 5,
        "max_chars": 48,
    },
    "finance_simulation": {
        "auto_style_id": "finance_blue",
        "caption_mode": "phrase",
        "font_family": "Segoe UI Semibold",
        "color": "clean_blue",
        "max_words": 5,
        "max_chars": 48,
    },
    "islamic": {
        "auto_style_id": "islamic_soft_white",
        "caption_mode": "phrase",
        "font_family": "Segoe UI Semibold",
        "color": "soft_white",
        "max_words": 4,
        "max_chars": 44,
    },
    "home_design": {
        "auto_style_id": "home_warm",
        "caption_mode": "phrase",
        "font_family": "Segoe UI Semibold",
        "color": "warm_white",
        "max_words": 4,
        "max_chars": 44,
    },
    "interior_design": {
        "auto_style_id": "home_warm",
        "caption_mode": "phrase",
        "font_family": "Segoe UI Semibold",
        "color": "warm_white",
        "max_words": 4,
        "max_chars": 44,
    },
    "stoic": {
        "auto_style_id": "stoic_minimal",
        "caption_mode": "phrase",
        "font_family": "Georgia",
        "color": "minimal_white",
        "max_words": 4,
        "max_chars": 44,
    },
    "default": {
        "auto_style_id": "clean_white",
        "caption_mode": "phrase",
        "font_family": "Segoe UI Semibold",
        "color": "white_black_stroke",
        "max_words": 4,
        "max_chars": 42,
    },
}

def is_auto_caption_style_long(style_id=None):
    return str(style_id or "").strip().lower() in {"", "auto", "automatic", "default_auto", "niche_auto", "auto_caption", "caption_auto"}

def get_long_caption_profile(niche="default", style_id=None, caption_mode="phrase"):
    key = str(niche or "default").lower()
    profile = dict(CAPTION_PROFILES_MODULE3.get(key, CAPTION_PROFILES_MODULE3["default"]))
    if is_auto_caption_style_long(style_id):
        profile["selected_style_id"] = profile["auto_style_id"]
        profile["style_source"] = "AUTO_NICHE_PROFILE"
    else:
        profile["selected_style_id"] = style_id
        profile["style_source"] = "UI_STYLE_LOCKED"
    profile["selected_caption_mode"] = caption_mode or profile.get("caption_mode", "phrase")
    return profile

def module3_long_caption_report():
    return {
        "module": "Module 3 - Caption Intelligence Engine",
        "safe_long_profile_manager": True,
        "ui_style_lock": True,
        "auto_niche_style": True,
        "profiles": sorted(CAPTION_PROFILES_MODULE3.keys()),
    }


# ============================================================
# MODULE 4 - LONG PIPELINE AUDIO PROFILE MANAGER
# ============================================================

AUDIO_PROFILES_MODULE4 = {
    "luxury": {"voice_volume": 1.55, "music_volume": 0.165, "sfx_volume": 0.075, "target_lufs": -14, "profile": "luxury_cinematic"},
    "luxury_lifestyle": {"voice_volume": 1.55, "music_volume": 0.165, "sfx_volume": 0.075, "target_lufs": -14, "profile": "luxury_cinematic"},
    "mystery": {"voice_volume": 1.58, "music_volume": 0.145, "sfx_volume": 0.085, "target_lufs": -14, "profile": "mystery_dark"},
    "ai": {"voice_volume": 1.52, "music_volume": 0.155, "sfx_volume": 0.085, "target_lufs": -14, "profile": "future_tech"},
    "quantum_future": {"voice_volume": 1.52, "music_volume": 0.155, "sfx_volume": 0.085, "target_lufs": -14, "profile": "future_tech"},
    "finance": {"voice_volume": 1.60, "music_volume": 0.115, "sfx_volume": 0.045, "target_lufs": -14, "profile": "finance_clean"},
    "finance_simulation": {"voice_volume": 1.60, "music_volume": 0.115, "sfx_volume": 0.045, "target_lufs": -14, "profile": "finance_clean"},
    "islamic": {"voice_volume": 1.50, "music_volume": 0.085, "sfx_volume": 0.035, "target_lufs": -14, "profile": "islamic_soft"},
    "home_design": {"voice_volume": 1.52, "music_volume": 0.135, "sfx_volume": 0.055, "target_lufs": -14, "profile": "home_warm"},
    "interior_design": {"voice_volume": 1.52, "music_volume": 0.135, "sfx_volume": 0.055, "target_lufs": -14, "profile": "home_warm"},
    "stoic": {"voice_volume": 1.50, "music_volume": 0.105, "sfx_volume": 0.035, "target_lufs": -14, "profile": "stoic_calm"},
    "default": {"voice_volume": 1.55, "music_volume": 0.135, "sfx_volume": 0.060, "target_lufs": -14, "profile": "default_balanced"},
}

def get_long_audio_profile(niche="default"):
    key = str(niche or "default").lower()
    return dict(AUDIO_PROFILES_MODULE4.get(key, AUDIO_PROFILES_MODULE4["default"]))

def module4_long_audio_report():
    return {
        "module": "Module 4 - Audio Master Engine",
        "safe_long_audio_profile_manager": True,
        "profiles": sorted(AUDIO_PROFILES_MODULE4.keys()),
        "target_lufs": -14,
        "voice_music_sfx_profiles": True,
    }