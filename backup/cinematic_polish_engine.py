# cinematic_polish_engine.py
# PROFESSIONAL CINEMATIC POLISHING ENGINE
# Auto-scales based on RAM. Never breaks existing pipeline.

import os
import subprocess
import random
from pathlib import Path

try:
    import psutil
    AVAILABLE_RAM_GB = psutil.virtual_memory().available / (1024 ** 3)
    LOW_RAM_MODE = AVAILABLE_RAM_GB < 4.0
except ImportError:
    LOW_RAM_MODE = True # Safe fallback

CINEMATIC_VERSION = "v1.0_premium_docu"

# Niche-specific camera behaviors & color grading
NICHE_PROFILES = {
    "luxury": {"camera": ["push_in", "slow_orbit"], "color": "warm_gold", "emotion": "elegant"},
    "finance": {"camera": ["push_in", "static_confident"], "color": "cool_blue", "emotion": "authoritative"},
    "ai": {"camera": ["floating", "slow_zoom_out"], "color": "cyan_silver", "emotion": "wonder"},
    "stoic_wisdom": {"camera": ["slow_pan", "static_calm"], "color": "muted_earth", "emotion": "calm"},
    "mystery": {"camera": ["slow_push_in", "dark_drift"], "color": "deep_shadow", "emotion": "suspense"},
    "default": {"camera": ["push_in", "slow_pan"], "color": "natural_hdr", "emotion": "neutral"}
}

def get_niche_profile(niche):
    niche = str(niche or "default").lower()
    for key in NICHE_PROFILES:
        if key in niche:
            return NICHE_PROFILES[key]
    return NICHE_PROFILES["default"]

def get_cinematic_camera_move(niche, clip_index, total_clips):
    profile = get_niche_profile(niche)
    moves = profile["camera"]
    # Add variation every 5-8 seconds (approx every 2 clips)
    if clip_index % 2 == 0:
        return random.choice(moves)
    return "micro_variation_" + random.choice(["push_in", "pan_left", "pan_right"])

def apply_cinematic_ffmpeg(input_path, output_path, niche, clip_index, total_clips, duration=5.0):
    """Applies camera move and color grade via FFmpeg (Low RAM safe)."""
    if LOW_RAM_MODE:
        return str(input_path) # Skip heavy processing
        
    profile = get_niche_profile(niche)
    move = get_cinematic_camera_move(niche, clip_index, total_clips)
    
    # 1. Camera Movement (Zoompan)
    if "push_in" in move:
        vf_cam = "zoompan=z='min(zoom+0.001,1.5)':d=125:s=1080x1920:fps=25"
    elif "push_out" in move:
        vf_cam = "zoompan=z='if(lte(zoom,1.0),1.5,max(zoom-0.001,1.0))':d=125:s=1080x1920:fps=25"
    elif "pan_left" in move:
        vf_cam = "zoompan=z=1.2:x='if(gte(x,0),iw-125,iw)':y='ih/2-(ih/2/1)':d=125:s=1080x1920:fps=25"
    elif "pan_right" in move:
        vf_cam = "zoompan=z=1.2:x='if(lte(x,0),0,iw)':y='ih/2-(ih/2/1)':d=125:s=1080x1920:fps=25"
    else:
        vf_cam = "zoompan=z='min(zoom+0.0005,1.2)':d=125:s=1080x1920:fps=25"

    # 2. HDR Color Grading
    color = profile["color"]
    if color == "warm_gold":
        vf_color = "eq=brightness=0.02:contrast=1.1:saturation=1.1,colorbalance=rs=0.05:gs=0.02:bs=-0.02"
    elif color == "cool_blue":
        vf_color = "eq=brightness=0.0:contrast=1.15:saturation=0.9,colorbalance=rs=-0.03:gs=0.0:bs=0.05"
    elif color == "cyan_silver":
        vf_color = "eq=brightness=0.03:contrast=1.2:saturation=0.85,colorbalance=rs=-0.02:gs=0.03:bs=0.04"
    elif color == "muted_earth":
        vf_color = "eq=brightness=-0.02:contrast=1.05:saturation=0.7,colorbalance=rs=0.03:gs=0.01:bs=-0.01"
    else:
        vf_color = "eq=brightness=0.01:contrast=1.08:saturation=1.05"

    vf_combined = f"{vf_cam},{vf_color}"

    try:
        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-vf", vf_combined,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-c:a", "copy",
            str(output_path)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if output_path.exists() and output_path.stat().st_size > 1000:
            return str(output_path)
    except Exception:
        pass
        
    return str(input_path)

def cinematic_audio_polish_ffmpeg(input_audio, output_audio, niche):
    """Applies professional sound stage and emotion EQ."""
    if LOW_RAM_MODE:
        return str(input_audio)
        
    profile = get_niche_profile(niche)
    emotion = profile["emotion"]
    
    # Subtle EQ for voice clarity and sound stage depth
    if emotion in ["elegant", "authoritative"]:
        af = "highpass=f=80,lowpass=f=12000,acompressor=threshold=-20dB:ratio=3.0:attack=10:release=100"
    elif emotion in ["calm", "suspense"]:
        af = "highpass=f=70,lowpass=f=11000,acompressor=threshold=-22dB:ratio=2.5:attack=15:release=120"
    else:
        af = "highpass=f=85,lowpass=f=12500,acompressor=threshold=-18dB:ratio=2.8:attack=12:release=110"

    try:
        cmd = [
            "ffmpeg", "-y", "-i", str(input_audio),
            "-af", af,
            "-c:a", "aac", "-b:a", "192k",
            str(output_audio)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if output_audio.exists() and output_audio.stat().st_size > 1000:
            return str(output_audio)
    except Exception:
        pass
        
    return str(input_audio)

def report_cinematic_status():
    return {
        "version": CINEMATIC_VERSION,
        "low_ram_mode": LOW_RAM_MODE,
        "available_ram_gb": round(AVAILABLE_RAM_GB, 2) if not LOW_RAM_MODE else "<4.0",
        "status": "Active (Safe Mode)" if LOW_RAM_MODE else "Active (Premium Mode)"
    }