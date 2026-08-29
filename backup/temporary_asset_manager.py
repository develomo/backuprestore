# temporary_asset_manager.py
# ==========================================================
# MY CREATION VIDEO GENERATOR
# TEMPORARY ASSET MANAGER v1.0
# ==========================================================
# Purpose:
# - UI uploaded assets ko permanent assets folders mein clutter
#   banne se bachana.
# - Render ke liye temporary hidden working folders banana.
# - Voice, clips, music, SFX, overlays ko safe copy karna.
# - Render complete hone ke baad temp files auto-clean karna.
# - Final output sirf outputs/ ya engine/final mein rahe.
#
# User requirement:
# - D drive ke assets folders mein uploaded data save na rahe.
# - Sirf final rendered video visible/save ho.
# ==========================================================

import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).parent

TEMP_ROOT = BASE_DIR / ".render_temp"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ENGINE_FINAL_DIR = BASE_DIR / "engine" / "final"
ENGINE_FINAL_DIR.mkdir(parents=True, exist_ok=True)


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def safe_print(message):
    try:
        print(str(message), flush=True)
    except Exception:
        pass


def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_name(name):
    name = str(name or "asset").strip()
    for ch in '<>:"/\\|?*':
        name = name.replace(ch, "_")
    return name[:120] or "asset"


def _ensure_dir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_video_file(path):
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS


def is_audio_file(path):
    return Path(path).suffix.lower() in AUDIO_EXTENSIONS


def is_image_file(path):
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


def create_render_workspace(mode="short", niche_key="auto"):
    """
    Creates one isolated temp workspace for a render.

    Structure:
        .render_temp/
            short_auto_20260621_...
                clips/
                voices/
                music/
                sfx/
                overlays/
                hook/
                output/
    """
    mode = str(mode or "short").lower().strip()
    niche_key = _safe_name(niche_key or "auto")

    workspace = TEMP_ROOT / f"{mode}_{niche_key}_{_timestamp()}"

    subdirs = {
        "root": workspace,
        "clips": workspace / "clips",
        "voices": workspace / "voices",
        "music": workspace / "music",
        "sfx": workspace / "sfx",
        "overlays": workspace / "overlays",
        "hook": workspace / "hook",
        "output": workspace / "output",
        "logs": workspace / "logs",
    }

    for path in subdirs.values():
        _ensure_dir(path)

    safe_print(f"[TempAssetManager] Workspace created: {workspace}")
    return subdirs


def copy_file_to_folder(src_path, dst_folder, prefix=None):
    """
    Copies a file to temp folder safely.
    """
    src = Path(src_path)

    if not src.exists() or not src.is_file():
        return None

    dst_folder = _ensure_dir(dst_folder)

    name = _safe_name(src.name)
    if prefix:
        name = f"{_safe_name(prefix)}_{name}"

    dst = dst_folder / name

    counter = 1
    while dst.exists():
        dst = dst_folder / f"{dst.stem}_{counter}{dst.suffix}"
        counter += 1

    shutil.copy2(str(src), str(dst))
    return dst


def copy_many_files(file_paths, dst_folder, allowed_exts=None, prefix=None):
    copied = []

    for index, file_path in enumerate(file_paths or []):
        try:
            p = Path(file_path)
            if not p.exists():
                continue

            if allowed_exts and p.suffix.lower() not in allowed_exts:
                continue

            out = copy_file_to_folder(
                p,
                dst_folder,
                prefix=f"{prefix or 'asset'}_{index + 1:03d}"
            )

            if out:
                copied.append(out)

        except Exception as e:
            safe_print(f"[TempAssetManager] Copy skipped: {file_path} | {e}")

    return copied


def prepare_assets_for_render(
    mode="short",
    niche_key="auto",
    clip_paths=None,
    voice_paths=None,
    music_paths=None,
    sfx_paths=None,
    overlay_paths=None,
    hook_paths=None,
):
    """
    Main public function.

    Use this from app.py before calling pipeline.

    Returns:
        dict with temp workspace paths and copied asset lists.
    """
    ws = create_render_workspace(mode=mode, niche_key=niche_key)

    clips = copy_many_files(
        clip_paths or [],
        ws["clips"],
        allowed_exts=VIDEO_EXTENSIONS,
        prefix="clip",
    )

    voices = copy_many_files(
        voice_paths or [],
        ws["voices"],
        allowed_exts=AUDIO_EXTENSIONS,
        prefix="voice",
    )

    music = copy_many_files(
        music_paths or [],
        ws["music"],
        allowed_exts=AUDIO_EXTENSIONS,
        prefix="music",
    )

    sfx = copy_many_files(
        sfx_paths or [],
        ws["sfx"],
        allowed_exts=AUDIO_EXTENSIONS,
        prefix="sfx",
    )

    overlays = copy_many_files(
        overlay_paths or [],
        ws["overlays"],
        allowed_exts=IMAGE_EXTENSIONS,
        prefix="overlay",
    )

    hook = copy_many_files(
        hook_paths or [],
        ws["hook"],
        allowed_exts=VIDEO_EXTENSIONS,
        prefix="hook",
    )

    result = {
        "workspace": ws["root"],
        "clips_dir": ws["clips"],
        "voices_dir": ws["voices"],
        "music_dir": ws["music"],
        "sfx_dir": ws["sfx"],
        "overlays_dir": ws["overlays"],
        "hook_dir": ws["hook"],
        "temp_output_dir": ws["output"],
        "logs_dir": ws["logs"],
        "clips": clips,
        "voices": voices,
        "music": music,
        "sfx": sfx,
        "overlays": overlays,
        "hook": hook,
    }

    safe_print(
        "[TempAssetManager] Assets prepared | "
        f"clips={len(clips)} voices={len(voices)} "
        f"music={len(music)} sfx={len(sfx)} "
        f"overlays={len(overlays)} hook={len(hook)}"
    )

    return result


def cleanup_workspace(workspace_path, keep_logs=False):
    """
    Deletes one render temp workspace.
    """
    workspace = Path(workspace_path)

    if not workspace.exists():
        return True

    try:
        if keep_logs:
            logs = workspace / "logs"
            backup_logs = TEMP_ROOT / "kept_logs" / workspace.name
            if logs.exists():
                backup_logs.parent.mkdir(parents=True, exist_ok=True)
                if backup_logs.exists():
                    shutil.rmtree(str(backup_logs), ignore_errors=True)
                shutil.copytree(str(logs), str(backup_logs))

        shutil.rmtree(str(workspace), ignore_errors=True)
        safe_print(f"[TempAssetManager] Workspace cleaned: {workspace}")
        return True

    except Exception as e:
        safe_print(f"[TempAssetManager] Cleanup failed: {e}")
        return False


def cleanup_old_temp_workspaces(max_age_hours=24):
    """
    Cleans old temp folders.
    Useful when app.py starts.
    """
    now = datetime.now().timestamp()
    max_age_seconds = float(max_age_hours) * 3600.0

    cleaned = 0

    for item in TEMP_ROOT.iterdir():
        try:
            if not item.is_dir():
                continue

            if item.name == "kept_logs":
                continue

            age = now - item.stat().st_mtime

            if age > max_age_seconds:
                shutil.rmtree(str(item), ignore_errors=True)
                cleaned += 1

        except Exception:
            pass

    if cleaned:
        safe_print(f"[TempAssetManager] Old temp folders cleaned: {cleaned}")

    return cleaned


def move_final_output(temp_output_path, final_name=None, mode="short"):
    """
    Moves rendered file from temp output to final output folder.

    Final video remains visible.
    Temp assets can then be deleted.
    """
    src = Path(temp_output_path)

    if not src.exists():
        raise FileNotFoundError(f"Final temp output not found: {src}")

    if not final_name:
        final_name = f"FINAL_{str(mode).upper()}_{_timestamp()}.mp4"

    final_name = _safe_name(final_name)
    if not final_name.lower().endswith(".mp4"):
        final_name += ".mp4"

    dst = ENGINE_FINAL_DIR / final_name

    counter = 1
    while dst.exists():
        dst = ENGINE_FINAL_DIR / f"{dst.stem}_{counter}{dst.suffix}"
        counter += 1

    shutil.move(str(src), str(dst))

    safe_print(f"[TempAssetManager] Final output saved: {dst}")
    return dst


def get_latest_final_video():
    """
    Returns latest final video from engine/final.
    Useful for UI preview.
    """
    videos = list(ENGINE_FINAL_DIR.glob("*.mp4"))

    if not videos:
        return None

    return max(videos, key=lambda p: p.stat().st_mtime)


def validate_asset_bundle(asset_bundle, mode="short"):
    """
    Checks if enough files exist before render.
    """
    errors = []

    clips = asset_bundle.get("clips", [])
    voices = asset_bundle.get("voices", [])

    if not clips:
        errors.append("No video clips found.")

    if not voices:
        errors.append("No voice file found.")

    if mode == "long":
        # Long can work without overlays/hook, so no hard error.
        pass

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


if __name__ == "__main__":
    cleanup_old_temp_workspaces()
    print("Temporary Asset Manager ready.")