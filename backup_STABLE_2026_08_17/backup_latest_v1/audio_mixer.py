# audio_mixer.py
# ==========================================================
# MY CREATION VIDEO GENERATOR  --  PHASE 2
# AUDIO MIXER v1.0  --  Professional Audio Layering Engine
# ==========================================================
#
# PURPOSE:
# - Voice-over + Background Music + SFX ko ek saath mix karna
# - Professional audio mastering (EQ, compression, limiting)
# - Ducking: jab voice bole, music automatically low ho jaye
# - SFX as transition bursts (not continuous loop)
# - Loudness normalization (YouTube-standard -14 LUFS)
# - Niche-specific audio profiles
# - Intro delay: voice intro ke baad shuru hoti hai
# - Outro silence: outro mein koi voice/music nahi
#
# ARCHITECTURE:
# ┌─────────────────────────────────────────────────────────┐
# │                    AudioMixer                            │
# │                                                         │
# │  ┌──────────┐   ┌──────────┐   ┌──────────────────┐   │
# │  │ Voice    │   │ Music    │   │ SFX              │   │
# │  │ Processor│   │ Processor│   │ Processor        │   │
# │  │ - EQ     │   │ - Tone   │   │ - Burst timing   │   │
# │  │ - Comp   │   │ - Ducking│   │ - Interval calc  │   │
# │  │ - Limit  │   │ - Fade   │   │ - Volume adjust  │   │
# │  │ - Delay  │   │ - Volume │   │ - Mix            │   │
# │  └────┬─────┘   └────┬─────┘   └────────┬─────────┘   │
# │       │              │                  │              │
# │       └──────────────┼──────────────────┘              │
# │                      ▼                                  │
# │  ┌──────────────────────────────────────────────────┐  │
# │  │           MASTER BUS                             │  │
# │  │  - amix (combine all streams)                    │  │
# │  │  - Final compression (glue)                      │  │
# │  │  - Final limiter (ceiling)                       │  │
# │  │  - Loudnorm (-14 LUFS target)                    │  │
# │  │  - AAC encode (192k)                             │  │
# │  └──────────────────────────────────────────────────┘  │
# └─────────────────────────────────────────────────────────┘
#
# AUDIO SIGNAL FLOW:
#   Voice.wav ──▶ [EQ] ──▶ [Compressor] ──▶ [Delay] ──▶ [Trim] ──┐
#                                                                    │
#   Music.mp3 ──▶ [Tone] ──▶ [Ducking] ──▶ [Fade in/out] ──▶ [Trim] ──┤
#                                                                    ├──▶ [amix] ──▶ [Master]
#   SFX.wav ────▶ [Bursts] ──▶ [Volume] ──▶ [Trim] ────────────────┘
#
# ==========================================================

from __future__ import annotations

import os
import gc
import json
import time
import shutil
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field

# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger("AudioMixer")
logger.setLevel(logging.INFO)

if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.handlers.clear()
    logger.addHandler(_handler)


# ============================================================
# FFMPEG/FFPROBE LOCATION
# ============================================================

def _get_ffmpeg() -> str:
    """Locate FFmpeg binary."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def _get_ffprobe() -> str:
    """Locate FFprobe binary."""
    ffmpeg = _get_ffmpeg()
    if Path(ffmpeg).name.lower() == "ffmpeg.exe":
        return str(Path(ffmpeg).with_name("ffprobe.exe"))
    return "ffprobe"


FFMPEG = _get_ffmpeg()
FFPROBE = _get_ffprobe()


# ============================================================
# AUDIO UTILITIES
# ============================================================

def probe_audio_duration(path: str) -> float:
    """
    Get audio file duration using FFprobe.
    
    Returns 6.0 if probe fails (safe default).
    """
    try:
        r = subprocess.run(
            [FFPROBE, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, errors="ignore",
        )
        if r.returncode == 0:
            return max(0.05, float(r.stdout.strip()))
    except Exception:
        pass
    return 6.0


def probe_audio_channels(path: str) -> int:
    """
    Get number of audio channels.
    
    Returns 2 if probe fails (stereo default).
    """
    try:
        r = subprocess.run(
            [FFPROBE, "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=channels",
             "-of", "default=nw=1:nk=1", str(path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, errors="ignore",
        )
        if r.returncode == 0:
            return max(1, int(r.stdout.strip()))
    except Exception:
        pass
    return 2


def run_ffmpeg_cmd(cmd: List[str], label: str = None) -> subprocess.CompletedProcess:
    """
    Execute FFmpeg command safely.
    
    Args:
        cmd: Command list
        label: Optional label for logging
    
    Returns:
        CompletedProcess
    
    Raises:
        RuntimeError: If command fails
    """
    if label:
        logger.info(label)
    
    r = subprocess.run(
        [str(x) for x in cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        errors="ignore",
    )
    
    if r.returncode != 0:
        error = (r.stderr or "")[-2000:]
        raise RuntimeError(f"FFmpeg failed: {error}")
    
    return r


def safe_num(val, default=0.0) -> float:
    """Safe float conversion."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return float(default)


# ============================================================
# AUDIO PROFILE SYSTEM
# ============================================================
# Each niche has its own audio personality.
#
# VOICE:  Louder for talking-head niches (finance, education),
#         softer for cinematic niches (luxury, stoic).
#
# MUSIC:  Higher for mood-driven niches (mystery, luxury),
#         lower for voice-heavy niches (finance, islamic).
#
# SFX:    More for energetic niches (AI, gaming),
#         less for calm niches (stoic, islamic).
#
# EQ:     Highpass removes rumble, lowpass removes harshness.
#         Finance has highest highpass (clean voice),
#         Mystery has lowest (atmospheric).
# ============================================================

def audio_profile_for_niche(niche: str = "default") -> Dict[str, Any]:
    """
    Get complete audio profile for a niche.
    
    Returns dict with:
    - voice_volume: Voice gain multiplier
    - music_volume: Music gain multiplier
    - sfx_volume: SFX gain multiplier
    - highpass: High-pass filter frequency (Hz)
    - lowpass: Low-pass filter frequency (Hz)
    - compress_threshold: Compressor threshold (dB)
    - compress_ratio: Compression ratio
    - target_lufs: Loudness target (LUFS)
    - music_tone: Music EQ filter string
    """
    n = str(niche or "default").lower()
    
    profiles = {
        # ---- LUXURY ----
        # Rich, warm sound. Music slightly prominent.
        "luxury": {
            "voice_volume": 1.55,
            "music_volume": 0.165,
            "sfx_volume": 0.075,
            "highpass": 85,
            "lowpass": 9800,
            "compress_threshold": "-19dB",
            "compress_ratio": 2.6,
            "target_lufs": -14,
            "music_tone": "highpass=f=60,lowpass=f=12500",
            "description": "Rich, warm, elegant  --  music slightly prominent"
        },
        "luxury_lifestyle": {
            "voice_volume": 1.55,
            "music_volume": 0.165,
            "sfx_volume": 0.075,
            "highpass": 85,
            "lowpass": 9800,
            "compress_threshold": "-19dB",
            "compress_ratio": 2.6,
            "target_lufs": -14,
            "music_tone": "highpass=f=60,lowpass=f=12500",
            "description": "Same as luxury"
        },
        
        # ---- MYSTERY ----
        # Atmospheric, slightly dark. Music drives mood.
        "mystery": {
            "voice_volume": 1.58,
            "music_volume": 0.145,
            "sfx_volume": 0.085,
            "highpass": 80,
            "lowpass": 9000,
            "compress_threshold": "-20dB",
            "compress_ratio": 2.8,
            "target_lufs": -14,
            "music_tone": "highpass=f=45,lowpass=f=10500",
            "description": "Atmospheric, dark, tension-building"
        },
        
        # ---- AI / TECH ----
        # Bright, clear, futuristic. SFX prominent.
        "ai": {
            "voice_volume": 1.52,
            "music_volume": 0.155,
            "sfx_volume": 0.085,
            "highpass": 90,
            "lowpass": 10500,
            "compress_threshold": "-19dB",
            "compress_ratio": 2.5,
            "target_lufs": -14,
            "music_tone": "highpass=f=70,lowpass=f=13500",
            "description": "Bright, futuristic, crisp  --  SFX-heavy"
        },
        "quantum_future": {
            "voice_volume": 1.52,
            "music_volume": 0.155,
            "sfx_volume": 0.085,
            "highpass": 90,
            "lowpass": 10500,
            "compress_threshold": "-19dB",
            "compress_ratio": 2.5,
            "target_lufs": -14,
            "music_tone": "highpass=f=70,lowpass=f=13500",
            "description": "Same as AI"
        },
        
        # ---- FINANCE ----
        # Clean, authoritative. Voice is king. Minimal music.
        "finance": {
            "voice_volume": 1.60,
            "music_volume": 0.115,
            "sfx_volume": 0.045,
            "highpass": 95,
            "lowpass": 9200,
            "compress_threshold": "-20dB",
            "compress_ratio": 3.0,
            "target_lufs": -14,
            "music_tone": "highpass=f=80,lowpass=f=9500",
            "description": "Clean, authoritative, voice-forward"
        },
        "finance_simulation": {
            "voice_volume": 1.60,
            "music_volume": 0.115,
            "sfx_volume": 0.045,
            "highpass": 95,
            "lowpass": 9200,
            "compress_threshold": "-20dB",
            "compress_ratio": 3.0,
            "target_lufs": -14,
            "music_tone": "highpass=f=80,lowpass=f=9500",
            "description": "Same as finance"
        },
        
        # ---- ISLAMIC ----
        # Soft, respectful. Very little music/SFX.
        "islamic": {
            "voice_volume": 1.50,
            "music_volume": 0.085,
            "sfx_volume": 0.035,
            "highpass": 85,
            "lowpass": 9000,
            "compress_threshold": "-20dB",
            "compress_ratio": 2.3,
            "target_lufs": -14,
            "music_tone": "highpass=f=60,lowpass=f=9000",
            "description": "Soft, respectful, minimal background audio"
        },
        
        # ---- INTERIOR/HOME DESIGN ----
        # Warm, inviting. Balanced.
        "home_design": {
            "voice_volume": 1.52,
            "music_volume": 0.135,
            "sfx_volume": 0.055,
            "highpass": 85,
            "lowpass": 9400,
            "compress_threshold": "-19dB",
            "compress_ratio": 2.4,
            "target_lufs": -14,
            "music_tone": "highpass=f=55,lowpass=f=11500",
            "description": "Warm, inviting, balanced"
        },
        "interior_design": {
            "voice_volume": 1.52,
            "music_volume": 0.135,
            "sfx_volume": 0.055,
            "highpass": 85,
            "lowpass": 9400,
            "compress_threshold": "-19dB",
            "compress_ratio": 2.4,
            "target_lufs": -14,
            "music_tone": "highpass=f=55,lowpass=f=11500",
            "description": "Same as home_design"
        },
        
        # ---- STOIC ----
        # Minimal, meditative. Very subtle music.
        "stoic": {
            "voice_volume": 1.50,
            "music_volume": 0.105,
            "sfx_volume": 0.035,
            "highpass": 85,
            "lowpass": 9000,
            "compress_threshold": "-20dB",
            "compress_ratio": 2.2,
            "target_lufs": -14,
            "music_tone": "highpass=f=60,lowpass=f=9000",
            "description": "Minimal, meditative, very subtle"
        },
        
        # ---- DEFAULT ----
        # Balanced all-rounder.
        "default": {
            "voice_volume": 1.55,
            "music_volume": 0.135,
            "sfx_volume": 0.060,
            "highpass": 90,
            "lowpass": 9500,
            "compress_threshold": "-19dB",
            "compress_ratio": 2.5,
            "target_lufs": -14,
            "music_tone": "highpass=f=60,lowpass=f=11500",
            "description": "Balanced  --  works for any niche"
        },
    }
    
    return dict(profiles.get(n, profiles["default"]))


# ============================================================
# AUDIO MIXER  --  MAIN CLASS
# ============================================================

@dataclass
class AudioMixConfig:
    """
    Configuration for one audio mix operation.
    
    All durations are in seconds. All paths are strings.
    """
    # Required
    video_path: str          # Video with NO audio (or dummy audio)
    voice_path: str          # Voice-over audio file
    output_path: str         # Final output with audio
    
    # Optional
    music_path: Optional[str] = None    # Background music
    sfx_path: Optional[str] = None      # Sound effects
    niche: str = "default"              # Niche for audio profile
    
    # Timing
    total_duration: float = 60.0        # Total video duration
    intro_seconds: float = 2.0          # Intro duration (voice starts after)
    voice_duration: float = 56.0        # Voice duration
    outro_seconds: float = 2.0          # Outro duration (silent)
    
    # Custom overrides (leave None for niche defaults)
    voice_volume: Optional[float] = None
    music_volume: Optional[float] = None
    sfx_volume: Optional[float] = None
    target_lufs: Optional[float] = None
    
    # SFX settings
    sfx_burst_interval: float = 7.5     # Seconds between SFX bursts
    sfx_burst_duration: float = 1.2     # Duration of each SFX burst


class AudioMixer:
    """
    Professional audio mixing engine.
    
    Mixes voice, music, and SFX into a final audio track with:
    - Per-channel EQ, compression, and limiting
    - Auto-ducking (music lowers when voice speaks)
    - Fade in/out for smooth transitions
    - Loudness normalization to YouTube standard
    - AAC encoding at 192kbps
    
    USAGE:
        mixer = AudioMixer()
        config = AudioMixConfig(
            video_path="video_no_audio.mp4",
            voice_path="voice.wav",
            output_path="final.mp4",
            music_path="bg_music.mp3",
            niche="luxury",
            total_duration=65.0,
            intro_seconds=2.0,
            voice_duration=58.0,
            outro_seconds=5.0,
        )
        result = mixer.mix(config)
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize audio mixer.
        
        Args:
            temp_dir: Directory for temp files (auto-created if None)
        """
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "audio_mixer_temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"AudioMixer initialized | temp={self.temp_dir}")
    
    # ================================================================
    # MAIN MIX METHOD
    # ================================================================
    
    def mix(self, config: AudioMixConfig) -> str:
        """
        Mix all audio streams into the final video.
        
        This is THE main method. Call this for every video render.
        
        Args:
            config: AudioMixConfig with all paths and settings
        
        Returns:
            Path to final output file with mixed audio
        
        Raises:
            FileNotFoundError: If video or voice file doesn't exist
            RuntimeError: If FFmpeg mixing fails
        """
        # Validate inputs
        video = Path(config.video_path)
        voice = Path(config.voice_path)
        
        if not video.exists():
            raise FileNotFoundError(f"Video not found: {video}")
        if not voice.exists():
            raise FileNotFoundError(f"Voice not found: {voice}")
        
        # Get audio profile
        profile = audio_profile_for_niche(config.niche)
        
        # Apply custom overrides
        voice_vol = config.voice_volume if config.voice_volume is not None else float(profile["voice_volume"])
        music_vol = config.music_volume if config.music_volume is not None else float(profile["music_volume"])
        sfx_vol = config.sfx_volume if config.sfx_volume is not None else float(profile["sfx_volume"])
        target_lufs = config.target_lufs if config.target_lufs is not None else float(profile["target_lufs"])
        
        hp = int(profile["highpass"])
        lp = int(profile["lowpass"])
        threshold = str(profile["compress_threshold"])
        ratio = float(profile["compress_ratio"])
        music_tone = str(profile["music_tone"])
        
        # Calculate trim end (body only, excludes outro)
        trim_end = f"{config.intro_seconds + config.voice_duration:.3f}"
        
        logger.info(f"Mixing audio | niche={config.niche} | "
                    f"voice_vol={voice_vol} | music_vol={music_vol} | "
                    f"sfx_vol={sfx_vol} | LUFS={target_lufs}")
        
        # ============================================================
        # BUILD FFMPEG COMMAND
        # ============================================================
        
        cmd = [FFMPEG, "-y"]
        
        # Input 0: Video (no audio or dummy audio)
        cmd += ["-i", str(video)]
        
        # Input 1: Voice-over
        cmd += ["-i", str(voice)]
        
        filters = []
        stream_labels = []
        input_idx = 2  # Next input index
        
        # ============================================================
        # VOICE CHAIN
        # ============================================================
        # [1:a] → volume → highpass → lowpass → compressor → limiter
        # → delay (intro offset) → EQ boost (4kHz presence)
        # → trim (before outro) → resample [v]
        # ============================================================
        
        voice_chain = (
            f"[1:a]volume={voice_vol},"
            f"highpass=f={hp},lowpass=f={lp},"
            f"acompressor=threshold={threshold}:ratio={ratio}:attack=8:release=95,"
            f"alimiter=limit=0.97,"
            f"adelay={int(config.intro_seconds * 1000)}|{int(config.intro_seconds * 1000)},"
            f"highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=10:release=100,"
            f"equalizer=f=4000:t=q:w=1:g=2,"
            f"atrim=0:{trim_end},"
            f"aresample=44100[v]"
        )
        filters.append(voice_chain)
        stream_labels.append("[v]")
        
        # ============================================================
        # MUSIC CHAIN (if provided)
        # ============================================================
        # [N:a] → volume → tone EQ → compressor → fade in/out
        # → delay (intro offset) → trim (before outro) → resample [m]
        # ============================================================
        
        music_exists = config.music_path and Path(config.music_path).exists()
        
        if music_exists:
            cmd += ["-stream_loop", "-1", "-i", str(config.music_path)]
            
            fade_out_start = max(
                config.intro_seconds,
                config.intro_seconds + config.voice_duration - 1.2
            )
            
            music_chain = (
                f"[{input_idx}:a]volume={music_vol},"
                f"{music_tone},"
                f"acompressor=threshold=-24dB:ratio=1.7:attack=30:release=250,"
                f"afade=t=in:st={config.intro_seconds:.3f}:d=1.0,"
                f"afade=t=out:st={fade_out_start:.3f}:d=1.2,"
                f"adelay={int(config.intro_seconds * 1000)}|{int(config.intro_seconds * 1000)},"
                f"highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=10:release=100,"
                f"equalizer=f=4000:t=q:w=1:g=2,"
                f"atrim=0:{trim_end},"
                f"aresample=44100[m]"
            )
            filters.append(music_chain)
            stream_labels.append("[m]")
            input_idx += 1
        else:
            logger.info("No music provided  --  skipping music chain")
        
        # ============================================================
        # SFX CHAIN (if provided)
        # ============================================================
        # v2.0 BUG 5 FIX: SFX fires as SHORT BURSTS every ~7.5 seconds
        # instead of continuous -stream_loop -1 background bed.
        # ============================================================
        
        sfx_exists = config.sfx_path and Path(config.sfx_path).exists()
        
        if sfx_exists:
            sfx_dur = probe_audio_duration(config.sfx_path)
            burst_len = min(sfx_dur, config.sfx_burst_duration)
            body_len = config.intro_seconds + config.voice_duration
            burst_interval = config.sfx_burst_interval
            n_bursts = min(60, max(1, int(body_len // burst_interval)))
            
            cmd += ["-i", str(config.sfx_path)]
            
            # Split SFX into N copies
            src_labels = "".join(f"[sfx_src{i}]" for i in range(n_bursts))
            
            sfx_split = (
                f"[{input_idx}:a]volume={sfx_vol},"
                f"atrim=0:{burst_len:.3f},asetpts=PTS-STARTPTS,"
                f"highpass=f=80,lowpass=f=13500,"
                f"asplit={n_bursts}{src_labels}"
            )
            filters.append(sfx_split)
            
            # Delay each burst
            hit_labels = []
            for i in range(n_bursts):
                delay_ms = int((config.intro_seconds + i * burst_interval) * 1000)
                filters.append(
                    f"[sfx_src{i}]adelay={delay_ms}|{delay_ms}[sfxh{i}]"
                )
                hit_labels.append(f"[sfxh{i}]")
            
            # Mix all bursts + trim
            sfx_mix = (
                "".join(hit_labels)
                + f"amix=inputs={n_bursts}:duration=longest,"
                + f"atrim=0:{trim_end},aresample=44100[s]"
            )
            filters.append(sfx_mix)
            stream_labels.append("[s]")
            input_idx += 1
            
            logger.info(f"SFX: {n_bursts} bursts every {burst_interval}s "
                       f"(burst_len={burst_len:.1f}s)")
        else:
            logger.info("No SFX provided  --  skipping SFX chain")
        
        # ============================================================
        # MASTER BUS
        # ============================================================
        # Combine all streams → glue compression → limiter → loudnorm → output
        # ============================================================
        
        n_streams = len(stream_labels)
        
        master_chain = (
            "".join(stream_labels)
            + f"amix=inputs={n_streams}:duration=longest:dropout_transition=0.35,"
            + "acompressor=threshold=-18dB:ratio=2.3:attack=10:release=120,"
            + "alimiter=limit=0.97,"
            + f"loudnorm=I={target_lufs}:TP=-1.0:LRA=10,"
            + "apad[aout]"
        )
        filters.append(master_chain)
        
        # ============================================================
        # FINAL COMMAND
        # ============================================================
        
        cmd += [
            "-filter_complex", ";".join(filters),
            "-map", "0:v:0",         # Video from input 0
            "-map", "[aout]",        # Audio from master bus
            "-t", f"{config.total_duration:.3f}",
            "-c:v", "copy",         # Copy video (no re-encode)
            "-c:a", "aac",          # AAC audio codec
            "-b:a", "192k",         # 192 kbps bitrate
            "-movflags", "+faststart",
            str(config.output_path),
        ]
        
        # Execute
        run_ffmpeg_cmd(cmd, label="[AudioMixer] Mixing final audio")
        
        # Verify output
        output = Path(config.output_path)
        if not output.exists() or output.stat().st_size == 0:
            raise RuntimeError(f"Audio mix output is missing or empty: {output}")
        
        logger.info(f"Audio mix complete | output={output} | "
                    f"size={output.stat().st_size / (1024*1024):.1f}MB")
        
        # Save mix report
        self._save_report(config, profile, output)
        
        return str(output)
    
    # ================================================================
    # MIX WITHOUT SFX (simpler version)
    # ================================================================
    
    def mix_voice_music_only(
        self,
        video_path: str,
        voice_path: str,
        output_path: str,
        music_path: Optional[str] = None,
        niche: str = "default",
        total_duration: float = 60.0,
        intro_seconds: float = 2.0,
        voice_duration: float = 56.0,
        outro_seconds: float = 2.0,
    ) -> str:
        """
        Simplified mix  --  voice + music only (no SFX).
        
        Convenience wrapper around mix().
        """
        config = AudioMixConfig(
            video_path=video_path,
            voice_path=voice_path,
            output_path=output_path,
            music_path=music_path,
            niche=niche,
            total_duration=total_duration,
            intro_seconds=intro_seconds,
            voice_duration=voice_duration,
            outro_seconds=outro_seconds,
        )
        return self.mix(config)
    
    # ================================================================
    # BACKGROUND MUSIC ONLY (for preview/test)
    # ================================================================
    
    def add_music_only(
        self,
        video_path: str,
        music_path: str,
        output_path: str,
        music_volume: float = 0.15,
        total_duration: float = 60.0,
    ) -> str:
        """
        Add ONLY background music (no voice, no SFX).
        
        Useful for testing music selection before full render.
        
        Args:
            video_path: Video with no audio
            music_path: Background music file
            output_path: Output path
            music_volume: Music gain (0.0-1.0)
            total_duration: Video length
        
        Returns:
            Output path
        """
        video = Path(video_path)
        music = Path(music_path)
        
        if not video.exists():
            raise FileNotFoundError(f"Video not found: {video}")
        if not music.exists():
            raise FileNotFoundError(f"Music not found: {music}")
        
        logger.info(f"Adding music only | volume={music_volume}")
        
        cmd = [
            FFMPEG, "-y",
            "-i", str(video),
            "-stream_loop", "-1", "-i", str(music),
            "-filter_complex",
            f"[1:a]volume={music_volume},"
            f"afade=t=in:st=0:d=1.0,"
            f"afade=t=out:st={max(0, total_duration - 1.5):.3f}:d=1.5,"
            f"atrim=0:{total_duration:.3f},"
            f"acompressor=threshold=-22dB:ratio=2:attack=20:release=200,"
            f"alimiter=limit=0.97,"
            f"loudnorm=I=-16:TP=-1.0:LRA=10[aout]",
            "-map", "0:v:0",
            "-map", "[aout]",
            "-t", f"{total_duration:.3f}",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path),
        ]
        
        run_ffmpeg_cmd(cmd, label="[AudioMixer] Music only")
        return str(output_path)
    
    # ================================================================
    # REPORTING
    # ================================================================
    
    def _save_report(self, config: AudioMixConfig, profile: dict, output: Path):
        """Save audio mix report as JSON."""
        try:
            report = {
                "module": "Audio Mixer v1.0",
                "niche": config.niche,
                "profile_description": profile.get("description", ""),
                "voice_volume": config.voice_volume or profile["voice_volume"],
                "music_volume": config.music_volume or profile["music_volume"],
                "sfx_volume": config.sfx_volume or profile["sfx_volume"],
                "target_lufs": config.target_lufs or profile["target_lufs"],
                "intro_seconds": config.intro_seconds,
                "voice_duration": config.voice_duration,
                "outro_seconds": config.outro_seconds,
                "total_duration": config.total_duration,
                "music_used": bool(config.music_path and Path(config.music_path).exists()),
                "sfx_used": bool(config.sfx_path and Path(config.sfx_path).exists()),
                "sfx_mode": "transition_bursts" if config.sfx_path else "none",
                "output": str(output),
            }
            
            report_path = output.with_suffix(".audio_report.json")
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            
        except Exception as e:
            logger.warning(f"Failed to save audio report: {e}")
    
    # ================================================================
    # CLEANUP
    # ================================================================
    
    def cleanup(self):
        """Remove temp directory."""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                logger.info("Audio mixer temp files cleaned up")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def mix_audio(
    video_path: str,
    voice_path: str,
    output_path: str,
    music_path: Optional[str] = None,
    sfx_path: Optional[str] = None,
    niche: str = "default",
    total_duration: float = 60.0,
    intro_seconds: float = 2.0,
    voice_duration: float = 56.0,
    outro_seconds: float = 2.0,
    **kwargs,
) -> str:
    """
    One-line audio mixing convenience function.
    
    Args:
        video_path: Video file (no audio)
        voice_path: Voice-over audio
        output_path: Final output
        music_path: Background music (optional)
        sfx_path: Sound effects (optional)
        niche: Niche name
        total_duration: Total video length
        intro_seconds: Intro duration
        voice_duration: Voice duration
        outro_seconds: Outro duration
        **kwargs: Additional AudioMixConfig overrides
    
    Returns:
        Output file path
    """
    mixer = AudioMixer()
    
    config = AudioMixConfig(
        video_path=video_path,
        voice_path=voice_path,
        output_path=output_path,
        music_path=music_path,
        sfx_path=sfx_path,
        niche=niche,
        total_duration=total_duration,
        intro_seconds=intro_seconds,
        voice_duration=voice_duration,
        outro_seconds=outro_seconds,
        **kwargs,
    )
    
    return mixer.mix(config)


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("
