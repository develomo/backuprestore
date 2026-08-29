import os
import gc
import shutil
import subprocess
import tempfile
from pathlib import Path

from hardware_safe_config import (
    EDIT_FPS,
    EDIT_LONG_SIZE,
    EDIT_SHORT_SIZE,
    ENABLE_4K_FINAL,
    FINAL_LONG_SIZE,
    FINAL_SHORT_SIZE,
    FFMPEG_CRF,
    FFMPEG_PRESET,
    RENDER_THREADS,
    apply_thread_limits,
    ram_temp_dir,
)

apply_thread_limits()

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs"
FINAL_DIR = OUTPUT_DIR / "final"
RAM_TEMP_DIR = ram_temp_dir(BASE_DIR)

FINAL_DIR.mkdir(parents=True, exist_ok=True)
RAM_TEMP_DIR.mkdir(parents=True, exist_ok=True)

SAFE_FPS = EDIT_FPS
SAFE_THREADS = RENDER_THREADS
SHORT_STAGE_SIZE = EDIT_SHORT_SIZE
LONG_STAGE_SIZE = EDIT_LONG_SIZE
SHORT_FINAL_SIZE = FINAL_SHORT_SIZE
LONG_FINAL_SIZE = FINAL_LONG_SIZE


def safe_print(message):
    try:
        print(str(message), flush=True)
    except Exception:
        pass


def cleanup_ram_temp():
    RAM_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    for item in list(RAM_TEMP_DIR.iterdir()):
        try:
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception:
            pass
    gc.collect()


def cleanup_specific_temp(path):
    try:
        p = Path(path)
        if p.exists() and RAM_TEMP_DIR in p.parents:
            p.unlink()
    except Exception:
        pass
    gc.collect()


def is_short_mode(mode="SHORT", clip=None):
    if str(mode or "").upper().startswith("SHORT"):
        return True
    if str(mode or "").upper().startswith("LONG"):
        return False
    try:
        w, h = clip.size
        return h >= w
    except Exception:
        return True


def stage_size(mode="SHORT", clip=None):
    return SHORT_STAGE_SIZE if is_short_mode(mode, clip) else LONG_STAGE_SIZE


def final_size(mode="SHORT", clip=None):
    return SHORT_FINAL_SIZE if is_short_mode(mode, clip) else LONG_FINAL_SIZE


def time_stamp():
    import datetime
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def make_temp_path(prefix="stage", suffix=".mp4"):
    RAM_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    return RAM_TEMP_DIR / f"{prefix}_{os.getpid()}_{next(tempfile._get_candidate_names())}{suffix}"


def final_output_path(mode="SHORT", name=None):
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    if name:
        return FINAL_DIR / name
    if is_short_mode(mode):
        return FINAL_DIR / f"FINAL_SHORT_480P_{time_stamp()}.mp4"
    return FINAL_DIR / f"FINAL_LONG_480P_{time_stamp()}.mp4"


def close_clip_tree(clip):
    try:
        if clip is None:
            return
        try:
            if getattr(clip, "audio", None):
                clip.audio.close()
        except Exception:
            pass
        try:
            if getattr(clip, "mask", None):
                clip.mask.close()
        except Exception:
            pass
        try:
            for child in list(getattr(clip, "clips", []) or []):
                close_clip_tree(child)
        except Exception:
            pass
        try:
            clip.close()
        except Exception:
            pass
    finally:
        gc.collect()


def resize_clip_safely(clip, mode="SHORT"):
    target_w, target_h = stage_size(mode, clip)
    try:
        w, h = clip.size
    except Exception:
        return clip
    try:
        scale = max(target_w / max(1, w), target_h / max(1, h))
        clip2 = clip.resize(scale)
        rw, rh = clip2.size
        x1 = max(0, int((rw - target_w) / 2))
        y1 = max(0, int((rh - target_h) / 2))
        return clip2.crop(x1=x1, y1=y1, x2=x1 + target_w, y2=y1 + target_h)
    except Exception:
        try:
            return clip.resize(newsize=(target_w, target_h))
        except Exception:
            return clip


def safe_write_stage_video(clip, output_path=None, fps=SAFE_FPS, mode="SHORT", audio=False):
    cleanup_ram_temp()
    output_path = Path(output_path) if output_path else make_temp_path("stage1", ".mp4")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    safe_fps = min(int(fps or SAFE_FPS), SAFE_FPS)
    stage_clip = resize_clip_safely(clip, mode=mode)
    safe_print(f"[RAM-SAFE] Stage 1/3: low-RAM render -> {output_path.name} | {stage_size(mode, clip)} @ {safe_fps}fps")
    stage_clip.write_videofile(
        str(output_path),
        fps=safe_fps,
        codec="libx264",
        audio=audio,
        preset="ultrafast",
        threads=SAFE_THREADS,
        bitrate="2500k",
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
        logger=None,
    )
    if stage_clip is not clip:
        try:
            stage_clip.close()
        except Exception:
            pass
    gc.collect()
    return output_path


def ffmpeg_available():
    return shutil.which("ffmpeg") is not None


def mux_audio_video(video_path, audio_path=None, output_path=None, mode="SHORT", keep_inputs=False):
    video_path = Path(video_path)
    if not audio_path:
        return video_path
    audio_path = Path(audio_path)
    output_path = Path(output_path) if output_path else make_temp_path("stage2_audio", ".mp4")
    if not ffmpeg_available() or not audio_path.exists():
        shutil.copy2(video_path, output_path)
        return output_path
    safe_print(f"[RAM-SAFE] Stage 2/3: audio mux (no re-encode) -> {output_path.name}")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "160k",
        "-shortest",
        "-movflags", "+faststart",
        "-threads", str(SAFE_THREADS),
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    if result.returncode != 0:
        safe_print(result.stderr[-300:] if result.stderr else "mux failed")
        shutil.copy2(video_path, output_path)
    if not keep_inputs:
        cleanup_specific_temp(video_path)
    gc.collect()
    return output_path


def ffmpeg_final_upscale(input_path, output_path=None, mode="SHORT", keep_input=False):
    """No upscale — copy 480p file to final path (enhance disabled)."""
    input_path = Path(input_path)
    output_path = Path(output_path) if output_path else final_output_path(mode=mode)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    safe_print(f"[RAM-SAFE] Final copy (480p, no enhance) -> {output_path.name}")
    shutil.copy2(input_path, output_path)
    if not keep_input:
        cleanup_specific_temp(input_path)
        cleanup_ram_temp()
    gc.collect()
    return output_path


# Backward-compatible alias
ffmpeg_4k_upscale = ffmpeg_final_upscale


def safe_three_stage_export(clip, output_path=None, mode="SHORT", fps=SAFE_FPS, audio_path=None):
    """
    Sequential export at 480p — NO upscale/enhance:
      Step 1: render video at 480p
      Step 2: mux audio (ffmpeg copy)
      Step 3: copy to final (no quality enhance)
    """
    cleanup_ram_temp()
    safe_print("[RAM-SAFE] 480p export — all editing steps preserved, no enhance")
    stage1 = safe_write_stage_video(clip, fps=fps, mode=mode, audio=False)
    close_clip_tree(clip)
    gc.collect()
    if audio_path:
        final_path = mux_audio_video(stage1, audio_path=audio_path, output_path=output_path, mode=mode, keep_inputs=False)
    else:
        final_path = ffmpeg_final_upscale(stage1, output_path=output_path, mode=mode, keep_input=False)
    cleanup_ram_temp()
    safe_print(f"[RAM-SAFE] Export complete: {final_path}")
    return final_path
