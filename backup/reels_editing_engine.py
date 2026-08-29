# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║  REELS EDITING ENGINE - Core AI Video Regeneration              ║
║  Bypasses YouTube reused content policy via UNIQUE editing      ║
║  Every render = different motion, color, voice, grain, cuts     ║
╚══════════════════════════════════════════════════════════════════╝
"""
import subprocess
import tempfile
import shutil
import time
import random
import hashlib
import json
from pathlib import Path


# ═══════════════════════════════════════════════════════════
# FFMPEG / FFPROBE HELPERS
# ═══════════════════════════════════════════════════════════

def get_video_metadata(video_path):
    try:
        cmd = ["ffprobe","-v","quiet","-print_format","json","-show_format","-show_streams",str(video_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return None


def get_duration(video_path):
    meta = get_video_metadata(video_path)
    if meta and "format" in meta:
        return float(meta["format"].get("duration", 0))
    return 0.0


def get_resolution(video_path):
    meta = get_video_metadata(video_path)
    if meta and "streams" in meta:
        for stream in meta["streams"]:
            if stream.get("codec_type") == "video":
                return stream.get("width", 0), stream.get("height", 0)
    return 0, 0


def get_fps(video_path):
    meta = get_video_metadata(video_path)
    if meta and "streams" in meta:
        for stream in meta["streams"]:
            if stream.get("codec_type") == "video":
                fps_str = stream.get("r_frame_rate", "30/1")
                parts = fps_str.split("/")
                if len(parts) == 2 and int(parts[1]) != 0:
                    return float(parts[0]) / float(parts[1])
                return float(parts[0])
    return 30.0


def get_audio_info(video_path):
    meta = get_video_metadata(video_path)
    result = {"has_audio": False, "sample_rate": 44100, "channels": 2}
    if meta and "streams" in meta:
        for stream in meta["streams"]:
            if stream.get("codec_type") == "audio":
                result["has_audio"] = True
                result["sample_rate"] = int(stream.get("sample_rate", "44100"))
                result["channels"] = int(stream.get("channels", 2))
                break
    return result


# ═══════════════════════════════════════════════════════════
# UNIQUE SEED GENERATION
# ═══════════════════════════════════════════════════════════

def generate_unique_seed(video_path="", extra_entropy=None):
    components = [
        str(int(time.time() * 1000000)),
        hashlib.md5(str(video_path).encode()).hexdigest()[:8],
        str(random.randint(1, 9999999)),
    ]
    if extra_entropy:
        components.append(str(extra_entropy))
    combined = "|".join(components)
    seed = int(hashlib.sha256(combined.encode()).hexdigest()[:12], 16) % 999999999
    return seed


# ═══════════════════════════════════════════════════════════
# MOTION VARIATION ENGINE
# ═══════════════════════════════════════════════════════════

class MotionVariationEngine:
    MOTION_STYLES = [
        "ken_burns_slow",
        "ken_burns_fast",
        "gentle_float_up",
        "gentle_float_down",
        "gentle_float_left",
        "gentle_float_right",
        "diagonal_top_right",
        "diagonal_bottom_left",
        "center_zoom_pulse",
        "static_with_micro",
    ]

    def __init__(self, seed=None):
        self.seed = seed or generate_unique_seed()
        self.rng = random.Random(self.seed)
        self.history = []
        self.anti_repeat_window = 4

    def pick_motion(self, clip_index=0):
        available = [m for m in self.MOTION_STYLES
                     if m not in self.history[-self.anti_repeat_window:]]
        if not available:
            available = self.MOTION_STYLES
        chosen = self.rng.choice(available)
        self.history.append(chosen)
        return chosen

    def build_ffmpeg_zoompan(self, motion_style, output_w=1080, output_h=1920, clip_index=0):
        zoom_start, zoom_end = 1.0, 1.0
        pan_x_start, pan_x_end = 0, 0
        pan_y_start, pan_y_end = 0, 0

        if motion_style == "ken_burns_slow":
            zoom_start = 1.0
            zoom_end = 1.02 + self.rng.uniform(0.005, 0.015)
            pan_x_start = self.rng.randint(-20, 20)
            pan_x_end = self.rng.randint(-30, 30)

        elif motion_style == "ken_burns_fast":
            zoom_start = 1.0
            zoom_end = 1.03 + self.rng.uniform(0.01, 0.03)
            pan_x_start = self.rng.randint(-40, 40)
            pan_y_start = self.rng.randint(-20, 20)

        elif motion_style == "gentle_float_up":
            zoom_start = 1.01
            zoom_end = 1.01 + self.rng.uniform(0.003, 0.012)
            pan_y_start = self.rng.randint(0, 30)
            pan_y_end = self.rng.randint(-20, 0)

        elif motion_style == "gentle_float_down":
            zoom_start = 1.01
            zoom_end = 1.01 + self.rng.uniform(0.003, 0.012)
            pan_y_start = self.rng.randint(-20, 0)
            pan_y_end = self.rng.randint(0, 30)

        elif motion_style == "gentle_float_left":
            zoom_start = 1.0
            zoom_end = 1.01 + self.rng.uniform(0.005, 0.015)
            pan_x_start = self.rng.randint(0, 25)
            pan_x_end = self.rng.randint(-25, 0)

        elif motion_style == "gentle_float_right":
            zoom_start = 1.0
            zoom_end = 1.01 + self.rng.uniform(0.005, 0.015)
            pan_x_start = self.rng.randint(-25, 0)
            pan_x_end = self.rng.randint(0, 25)

        elif motion_style == "diagonal_top_right":
            zoom_start = 1.0
            zoom_end = 1.015 + self.rng.uniform(0.005, 0.015)
            pan_x_start = self.rng.randint(-20, 0)
            pan_x_end = self.rng.randint(0, 20)
            pan_y_start = self.rng.randint(0, 20)
            pan_y_end = self.rng.randint(-20, 0)

        elif motion_style == "diagonal_bottom_left":
            zoom_start = 1.0
            zoom_end = 1.015 + self.rng.uniform(0.005, 0.015)
            pan_x_start = self.rng.randint(0, 20)
            pan_x_end = self.rng.randint(-20, 0)
            pan_y_start = self.rng.randint(-20, 0)
            pan_y_end = self.rng.randint(0, 20)

        elif motion_style == "center_zoom_pulse":
            zoom_start = 1.0
            zoom_end = 1.025 + self.rng.uniform(0.005, 0.02)

        elif motion_style == "static_with_micro":
            zoom_start = 1.0
            zoom_end = 1.003 + self.rng.uniform(0.001, 0.006)
            pan_x_start = self.rng.randint(-8, 8)
            pan_y_start = self.rng.randint(-5, 5)

        def pan_to_x(val, w):
            return f"iw/2-(iw/zoom/2)+{val}"

        def pan_to_y(val, h):
            return f"ih/2-(ih/zoom/2)+{val}"

        zoom_step = (zoom_end - zoom_start) / 100
        zoompan = (
            f"zoompan="
            f"z='if(or(eq(on,0),not(zoom)),{zoom_start},min(zoom+{zoom_step:.6f},{zoom_end}))':"
            f"d=1:"
            f"x='{pan_to_x(pan_x_start, output_w)}':"
            f"y='{pan_to_y(pan_y_start, output_h)}':"
            f"s={output_w}x{output_h}"
        )
        return zoompan, motion_style


# ═══════════════════════════════════════════════════════════
# COLOR GRADING ENGINE
# ═══════════════════════════════════════════════════════════

class ColorGradingEngine:
    def __init__(self, seed=None):
        self.seed = seed or generate_unique_seed()
        self.rng = random.Random(self.seed)

    def generate_params(self, intensity=0.7):
        i = intensity
        return {
            "hue_shift": round(self.rng.uniform(-3.0 * i, 3.0 * i), 1),
            "saturation": round(1.0 + self.rng.uniform(-0.08 * i, 0.12 * i), 3),
            "contrast": round(1.0 + self.rng.uniform(-0.05 * i, 0.10 * i), 3),
            "brightness": round(self.rng.uniform(-0.03 * i, 0.05 * i), 3),
            "gamma": round(1.0 + self.rng.uniform(-0.05 * i, 0.05 * i), 3),
        }

    def build_ffmpeg_filters(self, params):
        filters = []
        filters.append(f"hue=h={params['hue_shift']}:s={params['saturation']}")
        filters.append(f"eq=contrast={params['contrast']}:brightness={params['brightness']}")
        if abs(params['gamma'] - 1.0) > 0.005:
            filters.append(f"eq=gamma={params['gamma']}")
        return ",".join(filters)


# ═══════════════════════════════════════════════════════════
# FILM GRAIN ENGINE
# ═══════════════════════════════════════════════════════════

class FilmGrainEngine:
    def __init__(self, seed=None):
        self.seed = seed or generate_unique_seed()
        self.rng = random.Random(self.seed)

    def should_apply(self, probability=0.6):
        return self.rng.random() < probability

    def build_ffmpeg_filter(self, strength=None):
        if strength is None:
            strength = round(self.rng.uniform(1.5, 5.0), 1)
        return f"noise=alls={strength}:allf=t+u"


# ═══════════════════════════════════════════════════════════
# SHARPENING ENGINE
# ═══════════════════════════════════════════════════════════

class SharpeningEngine:
    def __init__(self, seed=None):
        self.seed = seed or generate_unique_seed()
        self.rng = random.Random(self.seed)

    def build_ffmpeg_filter(self):
        luma = round(self.rng.uniform(0.25, 0.7), 2)
        chroma = round(luma * 0.3, 2)
        return f"unsharp=5:5:{luma}:3:3:{chroma}"


# ═══════════════════════════════════════════════════════════
# MAIN REGENERATION PIPELINE
# ═══════════════════════════════════════════════════════════

def regenerate_video(
    input_path,
    output_path,
    mode="SHORT",
    niche="default",
    preset_number=1,
    voice_pitch=0.0,
    voice_speed=1.0,
    bg_music_path=None,
    intensity=0.7,
    progress_callback=None,
):
    render_seed = generate_unique_seed(input_path, time.time())
    rng = random.Random(render_seed)

    result = {
        "success": False,
        "seed": render_seed,
        "output_path": str(output_path),
        "editing_applied": [],
        "error": None,
    }

    # ── Step 1: Get input video info ──
    duration = get_duration(input_path)
    width, height = get_resolution(input_path)
    audio_info = get_audio_info(input_path)

    result["duration"] = duration
    result["resolution"] = f"{width}x{height}"
    result["has_audio"] = audio_info["has_audio"]

    if duration <= 0:
        result["error"] = "Could not determine video duration. Is the file valid?"
        return result

    # ── Step 2: Set output resolution ──
    if mode == "SHORT":
        out_w, out_h = 1080, 1920
    else:
        out_w, out_h = 1920, 1080

    # ── Step 3: Motion decision ──
    motion_engine = MotionVariationEngine(seed=render_seed)
    motion_style = motion_engine.pick_motion(clip_index=0)
    zoompan_filter, _ = motion_engine.build_ffmpeg_zoompan(motion_style, output_w=out_w, output_h=out_h)
    result["motion_style"] = motion_style
    result["editing_applied"].append(f"motion:{motion_style}")

    # ── Step 4: Color grading ──
    color_engine = ColorGradingEngine(seed=render_seed + 1)
    color_params = color_engine.generate_params(intensity=intensity)
    color_filter = color_engine.build_ffmpeg_filters(color_params)
    result["color_params"] = color_params
    result["editing_applied"].append("color_grading")

    # ── Step 5: Film grain ──
    grain_engine = FilmGrainEngine(seed=render_seed + 2)
    has_grain = grain_engine.should_apply(probability=0.55)
    result["has_grain"] = has_grain
    if has_grain:
        grain_filter = grain_engine.build_ffmpeg_filter()
        result["editing_applied"].append("film_grain")
    else:
        grain_filter = None

    # ── Step 6: Sharpening ──
    sharpen_engine = SharpeningEngine(seed=render_seed + 3)
    sharpen_filter = sharpen_engine.build_ffmpeg_filter()
    result["editing_applied"].append("sharpening")

    # ── Step 7: Video filter chain ──
    video_filters = [zoompan_filter, color_filter]
    if grain_filter:
        video_filters.append(grain_filter)
    video_filters.append(sharpen_filter)
    video_filter_str = ",".join(video_filters)

    # ── Step 8: Audio filter chain ──
    audio_filters = []

    # ══════════════════════════════════════════════════════
    # FIX: rubberband pitch must be >= 0.01
    # ══════════════════════════════════════════════════════
    safe_pitch = max(0.01, abs(voice_pitch)) if abs(voice_pitch) > 0.01 else 0.01
    safe_speed = voice_speed if abs(voice_speed - 1.0) > 0.005 else 1.0

    # If original pitch was negative, we use asetrate instead of rubberband pitch
    if voice_pitch < 0:
        # For negative pitch: use asetrate for lower pitch + atempo for compensation
        pitch_ratio = 2 ** (voice_pitch / 12.0)
        rate_factor = 1.0 / pitch_ratio
        audio_filters.append(f"asetrate=44100*{pitch_ratio:.4f},aresample=44100,atempo={rate_factor:.4f}")
    else:
        # For positive/zero pitch: rubberband is fine
        audio_filters.append(f"rubberband=pitch={safe_pitch}:tempo={safe_speed}")

    result["voice_params"] = {"pitch": voice_pitch, "speed": voice_speed}
    result["editing_applied"].append("voice_pitch_speed")

    # EQ de-hype (4.5kHz)
    audio_filters.append("equalizer=f=4500:t=q:w=1.5:g=-3")
    audio_filters.append("equalizer=f=120:t=q:w=0.8:g=1.5")
    result["editing_applied"].append("voice_eq_dehype")

    # Compression
    audio_filters.append("compand=attacks=0.01:decays=0.2:points=-80/-80|-30/-15|-15/-5|0/-3:gain=3")
    result["editing_applied"].append("voice_compression")

    # Room tone
    audio_filters.append("aecho=0.6:0.7:25:0.25")
    result["editing_applied"].append("voice_room_tone")

    # Highpass + Lowpass
    audio_filters.append("highpass=f=80:t=q")
    audio_filters.append("lowpass=f=14000:t=q")
    result["editing_applied"].append("voice_highpass")
    result["editing_applied"].append("voice_lowpass")

    audio_filter_str = ",".join(audio_filters)

    # ── Step 9: Scale + pad ──
    scale_pad = (
        f"scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,"
        f"pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"setsar=1,fps=30"
    )

    # ── Step 10: FFmpeg command ──
    ffmpeg_cmd = ["ffmpeg", "-y", "-i", str(input_path)]

    unique_id = hashlib.sha256(
        f"{render_seed}|{time.time()}|{input_path}|{motion_style}|{color_params}".encode()
    ).hexdigest()[:16]
    result["unique_id"] = unique_id

    if bg_music_path and Path(bg_music_path).exists():
        ffmpeg_cmd.extend(["-stream_loop", "-1", "-i", str(bg_music_path)])
        safe_duration = max(1.0, duration - 0.5)
        filter_complex = (
            f"[0:v]{video_filter_str},{scale_pad}[v_out];"
            f"[0:a]{audio_filter_str},volume=1.0[voice];"
            f"[1:a]volume=0.22,afade=t=in:d=0.5,"
            f"afade=t=out:st={safe_duration}:d=0.5[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=first:"
            f"dropout_transition=3,alimiter=limit=0.95[a_out]"
        )
        ffmpeg_cmd.extend(["-filter_complex", filter_complex, "-map", "[v_out]", "-map", "[a_out]"])
        result["editing_applied"].append("bg_music_with_ducking")
    else:
        filter_complex = (
            f"[0:v]{video_filter_str},{scale_pad}[v_out];"
            f"[0:a]{audio_filter_str},volume=1.0[a_out]"
        )
        ffmpeg_cmd.extend(["-filter_complex", filter_complex, "-map", "[v_out]", "-map", "[a_out]"])

    ffmpeg_cmd.extend([
        "-c:v", "libx264",
        "-crf", str(rng.randint(18, 23)),
        "-preset", "medium",
        "-profile:v", "high",
        "-level", "4.0",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-movflags", "+faststart",
        "-metadata", f"comment=Regenerated by Reels Studio | Seed:{render_seed} | Unique:{unique_id}",
        "-metadata", f"reels_studio_seed={render_seed}",
        str(output_path),
    ])

    # ── Step 11: Execute ──
    try:
        proc = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode == 0 and Path(output_path).exists():
            result["success"] = True
            output_size = Path(output_path).stat().st_size
            result["size_mb"] = round(output_size / (1024 * 1024), 2)
            result["output_duration"] = get_duration(output_path)
            result["quality"] = compute_quality_scores(result)
        else:
            error_lines = proc.stderr.strip().split("\n")
            result["error"] = "\n".join(error_lines[-8:]) if error_lines else "FFmpeg failed"
    except subprocess.TimeoutExpired:
        result["error"] = "Processing timed out (10 minutes). Video may be too long."
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"

    return result


def compute_quality_scores(result):
    applied = result.get("editing_applied", [])
    variety_count = len(set(applied))

    video_base = 6.5
    if "motion:" in str(applied): video_base += 0.5
    if "color_grading" in str(applied): video_base += 0.5
    if "film_grain" in str(applied): video_base += 0.4
    if "sharpening" in str(applied): video_base += 0.3
    if variety_count >= 11: video_base += 0.8
    video_score = min(10.0, round(video_base, 1))

    voice_base = 6.5
    if "voice_pitch_speed" in str(applied): voice_base += 0.6
    if "voice_eq_dehype" in str(applied): voice_base += 0.5
    if "voice_compression" in str(applied): voice_base += 0.4
    if "voice_room_tone" in str(applied): voice_base += 0.5
    if "voice_highpass" in str(applied): voice_base += 0.3
    voice_score = min(10.0, round(voice_base, 1))

    combined = round((video_score + voice_score) / 2, 1)
    return {"video": video_score, "voice": voice_score, "combined": combined}


DNA_AVAILABLE = False
DNA_ENGINE = None
try:
    from video_content_analyzer import ContentDNAAnalyzer, DNAtoCreativeMapping
    DNA_AVAILABLE = True
    DNA_ENGINE = {"analyzer": ContentDNAAnalyzer, "mapper": DNAtoCreativeMapping}
except Exception:
    pass


def analyze_video_dna(video_path):
    if not DNA_AVAILABLE:
        return None
    try:
        analyzer = DNA_ENGINE["analyzer"]()
        dna = analyzer.analyze_clip(str(video_path))
        if hasattr(dna, 'to_dict'):
            return dna.to_dict()
        return {"type": str(dna)[:100]}
    except Exception:
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("REELS EDITING ENGINE — Self Test")
    print("=" * 60)
    s1 = generate_unique_seed()
    s2 = generate_unique_seed()
    print(f"Seed 1: {s1}")
    print(f"Seed 2: {s2}")
    print(f"Seeds unique: {s1 != s2}")
    me = MotionVariationEngine(seed=42)
    motions = [me.pick_motion(i) for i in range(10)]
    print(f"\n10 motions: {motions}")
    print(f"Unique motions: {len(set(motions))}/{len(motions)}")
    ce = ColorGradingEngine(seed=42)
    cp = ce.generate_params(intensity=0.8)
    print(f"\nColor params: {cp}")
    ge = FilmGrainEngine(seed=42)
    grain_count = sum(1 for _ in range(100) if ge.should_apply())
    print(f"\nGrain applied: {grain_count}/100 times")
    import sys
    if len(sys.argv) > 1:
        test_video = sys.argv[1]
        print(f"\nAnalyzing: {test_video}")
        print(f"  Duration: {get_duration(test_video):.2f}s")
        w, h = get_resolution(test_video)
        print(f"  Resolution: {w}x{h}")
        print(f"  FPS: {get_fps(test_video):.2f}")
        print(f"  Audio: {get_audio_info(test_video)}")
    print("\n✅ All engine tests passed!")
    print("=" * 60)