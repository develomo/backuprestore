# staged_effect_render.py
# Apply ONE editing effect at a time, flush to disk, free RAM, repeat.
# This lets Motion/Zoom/Beat/Story/Hook/Captions all run on 8GB RAM at 480p.

import gc
import os
import shutil
import tempfile
import time
from pathlib import Path

from hardware_safe_config import (
    EDIT_FPS,
    RENDER_THREADS,
    apply_thread_limits,
    clamp_fps,
    ram_temp_dir,
)

apply_thread_limits()

BASE_DIR = Path(__file__).parent
RAM_TEMP = ram_temp_dir(BASE_DIR)
RAM_TEMP.mkdir(parents=True, exist_ok=True)

_step_counter = 0


def safe_print(msg):
    try:
        print(str(msg), flush=True)
    except Exception:
        pass


def _videoclip():
    try:
        from moviepy.editor import VideoFileClip
        return VideoFileClip
    except Exception:
        return None


def make_stage_path(label):
    global _step_counter
    _step_counter += 1
    tag = f"s{_step_counter:02d}_{label}_{int(time.time())}"
    return RAM_TEMP / f"{tag}_{os.getpid()}_{next(tempfile._get_candidate_names())}.mp4"


def close_clip(clip):
    if clip is None:
        return
    try:
        if getattr(clip, "audio", None):
            clip.audio.close()
    except Exception:
        pass
    try:
        for child in list(getattr(clip, "clips", []) or []):
            close_clip(child)
    except Exception:
        pass
    try:
        clip.close()
    except Exception:
        pass
    gc.collect()


def load_from_disk(path):
    VFC = _videoclip()
    if VFC is None:
        raise RuntimeError("MoviePy not available — install moviepy to render.")
    return VFC(str(path), audio=False)


def write_to_disk(clip, path, fps, mode="SHORT"):
    from ram_safe_render import resize_clip_safely
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_fps = clamp_fps(fps)
    stage = resize_clip_safely(clip, mode=mode)
    safe_print(f"[STAGED] Writing {path.name} @ {safe_fps}fps")
    stage.write_videofile(
        str(path),
        fps=safe_fps,
        codec="libx264",
        audio=False,
        preset="ultrafast",
        threads=RENDER_THREADS,
        bitrate="1200k",
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
        logger=None,
    )
    if stage is not clip:
        close_clip(stage)
    gc.collect()
    return path


def flush_clip(clip, label, fps, mode="SHORT"):
    out = make_stage_path(label)
    write_to_disk(clip, out, fps, mode)
    close_clip(clip)
    return out


def delete_stage(path):
    try:
        p = Path(path)
        if p.exists() and RAM_TEMP in p.resolve().parents:
            p.unlink()
    except Exception:
        pass
    gc.collect()


def run_build_stage(build_fn, label, fps, mode="SHORT"):
    """Build clip in memory, immediately flush to disk."""
    safe_print(f"[STAGED] Step: {label} (build)")
    clip = build_fn()
    if clip is None:
        raise RuntimeError(f"Stage '{label}' produced no video.")
    path = flush_clip(clip, label, fps, mode)
    safe_print(f"[STAGED] Step '{label}' done -> {path.name}")
    return path


def run_apply_stage(input_path, apply_fn, label, fps, mode="SHORT", keep_input=False):
    """Load from disk -> apply ONE effect -> flush -> delete input."""
    safe_print(f"[STAGED] Step: {label} (apply)")
    clip = load_from_disk(input_path)
    try:
        result = apply_fn(clip)
        if result is not None:
            clip = result
        out = flush_clip(clip, label, fps, mode)
    except Exception as e:
        close_clip(clip)
        safe_print(f"[STAGED] Step '{label}' failed: {e} — keeping previous file")
        return Path(input_path)
    finally:
        close_clip(clip)
    if not keep_input:
        delete_stage(input_path)
    safe_print(f"[STAGED] Step '{label}' done -> {out.name}")
    return out


def export_final_copy(video_path, audio_path, output_path, mode="SHORT"):
    """Final export: mux audio only. NO upscale, NO enhance."""
    from ram_safe_render import mux_audio_video, cleanup_ram_temp
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    safe_print(f"[STAGED] Final mux (480p, no enhance) -> {output_path.name}")
    if audio_path:
        muxed = mux_audio_video(video_path, audio_path=audio_path, mode=mode, keep_inputs=False)
        shutil.copy2(muxed, output_path)
        delete_stage(muxed)
    else:
        shutil.copy2(video_path, output_path)
        delete_stage(video_path)
    cleanup_ram_temp()
    gc.collect()
    safe_print(f"[STAGED] Final video ready: {output_path}")
    return str(output_path)
