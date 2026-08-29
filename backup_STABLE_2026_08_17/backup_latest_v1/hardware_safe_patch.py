# hardware_safe_patch.py
# ALL editing steps ON at 480p — each effect flushed to disk separately.
# NO 4K enhance, NO upscale. Final = 480p.

import gc
import time
import traceback
from pathlib import Path

from hardware_safe_config import (
    LOW_RAM_RENDER,
    EDIT_SHORT_SIZE,
    EDIT_LONG_SIZE,
    EDIT_FPS,
    SAFE_FEATURES,
    clamp_fps,
    caption_clip_limit,
    force_safe_render_kwargs,
)
from staged_effect_render import (
    run_build_stage,
    run_apply_stage,
    export_final_copy,
    safe_print as staged_print,
)

try:
    from ram_safe_render import resize_clip_safely, close_clip_tree
except Exception:
    resize_clip_safely = None
    close_clip_tree = None


def _safe_print(msg):
    staged_print(msg)


def _resize(video, size):
    if video is None:
        return video
    try:
        if tuple(getattr(video, "size", (0, 0))) == tuple(size):
            return video
    except Exception:
        pass
    try:
        return video.resize(newsize=size)
    except TypeError:
        try:
            return video.resize(size)
        except Exception:
            return video
    except Exception:
        return video


def _hook_fn(mod, plan, hook_text, use_hook, mode="SHORT"):
    if not use_hook or not SAFE_FEATURES.get("enable_hook_overlay"):
        return None
    orig = getattr(mod, "_original_apply_integrated_hook", None)
    if orig is None:
        orig = getattr(mod, "apply_integrated_hook", None)

    def apply_hook(video):
        if orig is None:
            return video
        try:
            return orig(video, plan, hook_text=hook_text, use_hook=True)
        except Exception as e:
            _safe_print(f"[HardwareSafe] Hook skipped: {e}")
            return video
    return apply_hook


def _build_short_base(mod, plan, clips):
    niche = plan.get("niche", "default")
    render_count = int(plan.get("render_count", 0))
    target_duration = float(plan.get("target_duration") or plan.get("voice_duration") or 0.0)
    sequence_paths = [Path(x["clip_path"]) for x in plan.get("clip_sequence", []) if isinstance(x, dict) and x.get("clip_path")]
    source_clips = list(clips or sequence_paths)
    if not source_clips:
        raise FileNotFoundError("No source clips.")
    chunk_size = float(plan.get("preset", {}).get("chunk_size", 8.0))
    formatted = mod.prepare_clip_sequence_for_duration(
        video_paths=source_clips, target_duration=target_duration,
        mode="SHORT", strategy="smart", quality="edit", chunk_size=chunk_size, audio=False,
    )
    if not formatted:
        raise RuntimeError("No formatted clips.")
    processed = []
    for i, clip in enumerate(formatted):
        current = _resize(clip, EDIT_SHORT_SIZE)
        if SAFE_FEATURES.get("enable_motion"):
            try:
                current = mod.apply_human_motion_to_clip(current, mode="SHORT", niche=niche, render_count=render_count + i, clip_index=i)
            except TypeError:
                current = mod.apply_human_motion_to_clip(current, mode="SHORT", niche=niche, render_count=render_count + i)
            except Exception as e:
                _safe_print(f"[HardwareSafe] Motion clip {i}: {e}")
        if SAFE_FEATURES.get("enable_animation"):
            try:
                current = mod.apply_auto_animation(current, niche=niche, mode="SHORT", render_count=render_count + i, clip_index=i)
            except Exception as e:
                _safe_print(f"[HardwareSafe] Animation clip {i}: {e}")
        if SAFE_FEATURES.get("enable_zoom"):
            try:
                current = mod.apply_auto_zoom(current, niche=niche, mode="SHORT", render_count=render_count + i, clip_index=i)
            except Exception as e:
                _safe_print(f"[HardwareSafe] Zoom clip {i}: {e}")
        processed.append(current)
        _safe_print(f"[HardwareSafe] Clip {i+1}/{len(formatted)} @ 480p with motion/anim/zoom")
    mod.progress("Concatenating clips", 2, 12)
    video = mod.concatenate_formatted_clips(processed, target_duration=target_duration)
    if video is None:
        raise RuntimeError("Concatenate failed.")
    return video


def _staged_short_visuals(mod, video_path, plan, add_captions, fps):
    words = plan.get("caption_setup", {}).get("words") or []
    niche = plan.get("niche", "default")
    render_count = int(plan.get("render_count", 0))
    caption_setup = plan.get("caption_setup", {})
    cap_mode = caption_setup.get("mode", "word_by_word")
    path = Path(video_path)

    if SAFE_FEATURES.get("enable_keyword_zoom") and words:
        def fn(v):
            try:
                return mod.apply_keyword_zoom(v, words, niche=niche, mode="SHORT", caption_mode=cap_mode, render_count=render_count)
            except TypeError:
                return mod.apply_keyword_zoom(v, words, niche=niche, mode="SHORT", caption_mode=cap_mode)
        path = run_apply_stage(path, fn, "keyword_zoom", fps, "SHORT")

    if SAFE_FEATURES.get("enable_beat_sync"):
        def fn(v):
            try:
                return mod.apply_beat_sync(v, duration=v.duration, words=words, mode="SHORT", niche=niche, render_count=render_count, use_flash=True, use_pulse=False)
            except Exception:
                return mod.apply_beat_flashes(v, duration=v.duration, mode="SHORT", niche=niche, render_count=render_count)
        path = run_apply_stage(path, fn, "beat_sync", fps, "SHORT")

    if SAFE_FEATURES.get("enable_story_flow"):
        def fn(v):
            try:
                return mod.apply_story_flow(v, words=words, mode="SHORT", niche=niche, render_count=render_count, show_markers=True)
            except TypeError:
                return mod.apply_story_flow(v, mode="SHORT", niche=niche, render_count=render_count)
        path = run_apply_stage(path, fn, "story_flow", fps, "SHORT")

    if add_captions and words and SAFE_FEATURES.get("enable_captions"):
        max_clips = caption_clip_limit(cap_mode)
        def fn(v):
            try:
                return mod.add_captions_to_video(
                    v, words, style_id=caption_setup.get("style_id"), mode=cap_mode, niche=niche,
                    fps=EDIT_FPS, render_scale=1, cache_enabled=False, max_caption_clips=max_clips,
                )
            except TypeError:
                return mod.add_captions_to_video(v, words, style_id=caption_setup.get("style_id"), mode=cap_mode, niche=niche)
        path = run_apply_stage(path, fn, "captions", fps, "SHORT")

    return path


def _build_long_base(mod, plan, clips):
    niche = plan.get("niche", "default")
    render_count = int(plan.get("render_count", 0))
    target_duration = float(plan.get("target_duration") or plan.get("voice_duration") or 0.0)
    sequence_paths = [Path(x["clip_path"]) for x in plan.get("clip_sequence", []) if isinstance(x, dict) and x.get("clip_path")]
    source_clips = list(clips or sequence_paths)
    if not source_clips:
        raise FileNotFoundError("No source clips.")
    chunk_size = float(plan.get("preset", {}).get("chunk_size", 6.0))
    formatted = mod.prepare_clip_sequence_for_duration(
        video_paths=source_clips, target_duration=target_duration,
        mode=mod.LONG_MODE, strategy="smart", quality="edit", chunk_size=chunk_size, audio=False,
    )
    if not formatted:
        raise RuntimeError("No formatted long clips.")
    processed = []
    for i, clip in enumerate(formatted):
        current = _resize(clip, EDIT_LONG_SIZE)
        if SAFE_FEATURES.get("enable_motion"):
            try:
                current = mod.apply_human_motion_to_clip(current, mode=mod.LONG_MODE, niche=niche, render_count=render_count + i, clip_index=i)
            except TypeError:
                current = mod.apply_human_motion_to_clip(current, mode=mod.LONG_MODE, niche=niche, render_count=render_count + i)
            except Exception as e:
                _safe_print(f"[HardwareSafe] Long motion clip {i}: {e}")
        if SAFE_FEATURES.get("enable_animation"):
            try:
                current = mod.apply_auto_animation(current, niche=niche, mode=mod.LONG_MODE, render_count=render_count + i, clip_index=i)
            except Exception as e:
                _safe_print(f"[HardwareSafe] Long animation clip {i}: {e}")
        if SAFE_FEATURES.get("enable_zoom"):
            try:
                current = mod.apply_auto_zoom(current, niche=niche, mode=mod.LONG_MODE, render_count=render_count + i, clip_index=i)
            except Exception as e:
                _safe_print(f"[HardwareSafe] Long zoom clip {i}: {e}")
        processed.append(current)
    video = mod.concatenate_formatted_clips(processed, target_duration=target_duration)
    if video is None:
        raise RuntimeError("Long concatenate failed.")
    return video


def _staged_long_visuals(mod, video_path, plan, add_captions, use_overlays, fps):
    words = plan.get("caption_setup", {}).get("words") or []
    niche = plan.get("niche", "default")
    render_count = int(plan.get("render_count", 0))
    caption_setup = plan.get("caption_setup", {})
    cap_mode = caption_setup.get("mode", "phrase")
    path = Path(video_path)

    if SAFE_FEATURES.get("enable_keyword_zoom") and words:
        def fn(v):
            try:
                return mod.apply_keyword_zoom(v, words, niche=niche, mode=mod.LONG_MODE, caption_mode=cap_mode, render_count=render_count)
            except TypeError:
                return mod.apply_keyword_zoom(v, words, niche=niche, mode=mod.LONG_MODE, caption_mode=cap_mode)
        path = run_apply_stage(path, fn, "keyword_zoom", fps, mod.LONG_MODE)

    if SAFE_FEATURES.get("enable_beat_sync"):
        def fn(v):
            try:
                return mod.apply_beat_sync(v, duration=v.duration, words=words, mode=mod.LONG_MODE, niche=niche, render_count=render_count, use_flash=True, use_pulse=False)
            except Exception:
                return mod.apply_beat_flashes(v, duration=v.duration, mode=mod.LONG_MODE, niche=niche, render_count=render_count)
        path = run_apply_stage(path, fn, "beat_sync", fps, mod.LONG_MODE)

    if use_overlays and SAFE_FEATURES.get("enable_overlays"):
        def fn(v):
            return mod.apply_long_overlays(v, use_overlays=True)
        path = run_apply_stage(path, fn, "overlays", fps, mod.LONG_MODE)

    if SAFE_FEATURES.get("enable_story_flow"):
        def fn(v):
            try:
                return mod.apply_story_flow(v, words=words, mode=mod.LONG_MODE, niche=niche, render_count=render_count, show_markers=True)
            except TypeError:
                return mod.apply_story_flow(v, mode=mod.LONG_MODE, niche=niche, render_count=render_count)
        path = run_apply_stage(path, fn, "story_flow", fps, mod.LONG_MODE)

    if add_captions and words and SAFE_FEATURES.get("enable_captions"):
        max_clips = caption_clip_limit(cap_mode)
        def fn(v):
            try:
                return mod.add_captions_to_video(
                    v, words, style_id=caption_setup.get("style_id"), mode=cap_mode, niche=niche,
                    fps=EDIT_FPS, max_caption_clips=max_clips,
                )
            except TypeError:
                return mod.add_captions_to_video(v, words, style_id=caption_setup.get("style_id"), mode=cap_mode, niche=niche)
        path = run_apply_stage(path, fn, "captions", fps, mod.LONG_MODE)

    return path


def _run_staged_short(mod, voice_path, clips, words, plan, output_path, fps, use_hook, hook_text, add_captions, music_path, sfx_files, clean_silence, assets):
    fps = clamp_fps(fps)
    _safe_print(f"[HardwareSafe] STAGED SHORT | 480p | ALL effects ON | fps={fps} | NO enhance")

    mod.progress("Stage: base clips + motion + zoom", 1, 12)
    path = run_build_stage(lambda: _build_short_base(mod, plan, clips), "base", fps, "SHORT")

    mod.progress("Stage: visual layers one-by-one", 3, 12)
    path = _staged_short_visuals(mod, path, plan, add_captions, fps)

    hook_apply = _hook_fn(mod, plan, hook_text, use_hook, "SHORT")
    if hook_apply:
        mod.progress("Stage: hook overlay", 7, 12)
        path = run_apply_stage(path, hook_apply, "hook", fps, "SHORT")

    mod.progress("Stage: audio mix", 8, 12)
    audio_mix = mod.build_integrated_audio_for_pipeline(
        voice_path, plan,
        music_path=music_path or mod.choose_default_music("SHORT", render_count=plan.get("render_count", 0)),
        sfx_files=sfx_files or assets.get("sfx", []),
        clean_silence=clean_silence,
    )

    mod.progress("Stage: final export (480p, no enhance)", 9, 12)
    default_dir = mod.SHORT_OUTPUT_DIR
    default_dir.mkdir(parents=True, exist_ok=True)
    out = Path(output_path or default_dir / f"FINAL_SHORT_480P_{int(time.time())}.mp4")
    return export_final_copy(path, audio_mix, out, mode="SHORT")


def _run_staged_long(mod, voice_path, clips, plan, output_path, fps, use_hook, hook_text, add_captions, use_overlays, music_path, sfx_files, clean_silence, assets):
    fps = clamp_fps(fps)
    _safe_print(f"[HardwareSafe] STAGED LONG | 480p | ALL effects ON | fps={fps} | NO enhance")

    mod.progress("Stage: base clips + motion + zoom", 1, 12)
    path = run_build_stage(lambda: _build_long_base(mod, plan, clips), "base", fps, mod.LONG_MODE)

    mod.progress("Stage: visual layers one-by-one", 3, 12)
    path = _staged_long_visuals(mod, path, plan, add_captions, use_overlays, fps)

    hook_apply = _hook_fn(mod, plan, hook_text, use_hook, mod.LONG_MODE)
    if hook_apply:
        mod.progress("Stage: hook overlay", 8, 12)
        path = run_apply_stage(path, hook_apply, "hook", fps, mod.LONG_MODE)

    mod.progress("Stage: audio mix", 9, 12)
    audio_mix = mod.build_integrated_long_audio(
        voice_path, plan,
        music_path=music_path or mod.choose_default_music(render_count=plan.get("render_count", 0)),
        sfx_files=sfx_files or assets.get("sfx", []),
        clean_silence=clean_silence,
    )

    mod.progress("Stage: final export (480p, no enhance)", 10, 12)
    mod.LONG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = Path(output_path or mod.LONG_OUTPUT_DIR / f"FINAL_LONG_480P_{int(time.time())}.mp4")
    return export_final_copy(path, audio_mix, out, mode=mod.LONG_MODE)


def apply_short_pipeline_patch(mod):
    if not LOW_RAM_RENDER:
        return
    _safe_print("[HardwareSafe] SHORT: all editing ON @ 480p, staged render, NO enhance")

    def export_integrated_final_video(video_path, audio_path, plan, output_path=None):
        mod.progress("Final mux only (480p, no enhance)", 9, 12)
        default_dir = mod.SHORT_OUTPUT_DIR
        default_dir.mkdir(parents=True, exist_ok=True)
        out = Path(output_path or default_dir / f"FINAL_SHORT_480P_{int(time.time())}.mp4")
        return export_final_copy(video_path, audio_path, out, mode="SHORT")

    mod.export_integrated_final_video = export_integrated_final_video

    def run_integrated_short_pipeline(
        voice_path=None, clips=None, words=None, words_path=None, transcript_text=None,
        output_path=None, niche="default", render_count=0, caption_mode="word_by_word",
        style_id=None, music_path=None, sfx_files=None, use_hook=True, hook_text=None,
        final_4k=True, fps=30, quality="high", clean_silence=False, add_captions=True, preset_overrides=None,
    ):
        started = time.time()
        log = {"started": started, "pipeline": "staged_short_480p_all_effects", "niche": niche}
        try:
            kwargs = force_safe_render_kwargs({
                "fps": fps, "final_4k": False, "use_hook": use_hook, "quality": quality,
            })
            fps = kwargs["fps"]
            mode = "SHORT"
            assets = mod.list_assets(mode)
            voice_path = Path(voice_path) if voice_path else mod.choose_default_voice(mode)
            if voice_path is None:
                raise FileNotFoundError("Voice missing.")
            voice_path = mod._validate_file(voice_path, "voice")
            clips = list(clips or assets["clips"])
            if not clips:
                raise FileNotFoundError("Clips missing.")
            if words_path and not words:
                words = mod.load_words_json(words_path)
            if transcript_text and not words:
                words = mod.transcript_to_fake_words(transcript_text)
            voice_duration = mod.get_voice_duration_float(voice_path)
            if hasattr(mod, "_auto_caption_words_if_missing") and add_captions:
                words = mod._auto_caption_words_if_missing(words, voice_path=voice_path, duration=voice_duration, caption_mode=caption_mode, style_id=style_id)
            overrides = {"final_4k": False, "fps": fps, "quality": "balanced", "clean_silence": clean_silence}
            if preset_overrides:
                overrides.update(preset_overrides)
            overrides["final_4k"] = False
            plan = mod.build_deep_integrated_master_plan(
                voice_path=voice_path, clips=clips, words=words or [], mode=mode,
                niche=niche, render_count=render_count, caption_mode=caption_mode,
                style_id=style_id, preset_overrides=overrides,
            )
            log["plan"] = plan
            final = _run_staged_short(
                mod, voice_path, clips, words, plan, output_path, fps,
                use_hook, hook_text, add_captions, music_path, sfx_files, clean_silence, assets,
            )
            log["final"] = final
            log["duration_seconds"] = round(time.time() - started, 3)
            if hasattr(mod, "save_pipeline_log"):
                mod.save_pipeline_log(log, output_path=mod.LOG_DIR / f"staged_short_{int(time.time())}.json")
            mod.progress("Done", 12, 12)
            return final
        except Exception as e:
            log["error"] = str(e)
            log["traceback"] = traceback.format_exc()
            if hasattr(mod, "save_pipeline_log"):
                mod.save_pipeline_log(log, output_path=mod.LOG_DIR / f"staged_short_error_{int(time.time())}.json")
            raise

    mod.run_integrated_short_pipeline = run_integrated_short_pipeline

    def write_temp_video(video, output_path=None, fps=30):
        from staged_effect_render import flush_clip
        return str(flush_clip(video, "temp", clamp_fps(fps), "SHORT"))

    mod.write_temp_video = write_temp_video


def apply_long_pipeline_patch(mod):
    if not LOW_RAM_RENDER:
        return
    _safe_print("[HardwareSafe] LONG: all editing ON @ 480p, staged render, NO enhance")

    def export_integrated_long_final(video_path, audio_path, plan, output_path=None):
        mod.LONG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out = Path(output_path or mod.LONG_OUTPUT_DIR / f"FINAL_LONG_480P_{int(time.time())}.mp4")
        return export_final_copy(video_path, audio_path, out, mode=mod.LONG_MODE)

    mod.export_integrated_long_final = export_integrated_long_final

    def run_integrated_long_pipeline(
        voice_path=None, clips=None, words=None, words_path=None, transcript_text=None,
        output_path=None, niche="default", render_count=0, caption_mode="phrase",
        style_id=None, music_path=None, sfx_files=None, use_hook=True, hook_text=None,
        use_overlays=True, final_4k=True, fps=30, quality="high", clean_silence=False,
        add_captions=True, preset_overrides=None,
    ):
        started = time.time()
        log = {"started": started, "pipeline": "staged_long_480p_all_effects", "niche": niche}
        try:
            kwargs = force_safe_render_kwargs({"fps": fps, "final_4k": False, "use_hook": use_hook})
            fps = kwargs["fps"]
            assets = mod.list_long_assets()
            voice_path = Path(voice_path) if voice_path else mod.choose_default_voice()
            if voice_path is None:
                raise FileNotFoundError("Long voice missing.")
            voice_path = mod._validate_file(voice_path, "voice")
            clips = list(clips or assets["clips"])
            if not clips:
                raise FileNotFoundError("Long clips missing.")
            if words_path and not words:
                words = mod.load_words_json(words_path)
            if transcript_text and not words:
                words = mod.transcript_to_fake_words(transcript_text)
            voice_duration = mod.get_voice_duration_float(voice_path)
            if hasattr(mod, "_auto_long_caption_words_if_missing") and add_captions:
                words = mod._auto_long_caption_words_if_missing(words, voice_path=voice_path, duration=voice_duration, caption_mode=caption_mode, style_id=style_id)
            overrides = {"final_4k": False, "fps": fps, "quality": "balanced", "use_overlays": use_overlays, "use_hook": use_hook}
            if preset_overrides:
                overrides.update(preset_overrides)
            overrides["final_4k"] = False
            plan = mod.build_deep_integrated_long_plan(
                voice_path=voice_path, clips=clips, words=words or [], niche=niche,
                render_count=render_count, caption_mode=caption_mode, style_id=style_id, preset_overrides=overrides,
            )
            log["plan"] = plan
            final = _run_staged_long(
                mod, voice_path, clips, plan, output_path, fps,
                use_hook, hook_text, add_captions, use_overlays, music_path, sfx_files, clean_silence, assets,
            )
            log["final"] = final
            log["duration_seconds"] = round(time.time() - started, 3)
            if hasattr(mod, "save_pipeline_log"):
                mod.save_pipeline_log(log, output_path=mod.LOG_DIR / f"staged_long_{int(time.time())}.json")
            mod.progress("Done", 12, 12)
            return final
        except Exception as e:
            log["error"] = str(e)
            log["traceback"] = traceback.format_exc()
            if hasattr(mod, "save_pipeline_log"):
                mod.save_pipeline_log(log, output_path=mod.LOG_DIR / f"staged_long_error_{int(time.time())}.json")
            raise

    mod.run_integrated_long_pipeline = run_integrated_long_pipeline

    def write_temp_long_video(video, output_path=None, fps=30):
        from staged_effect_render import flush_clip
        return str(flush_clip(video, "temp_long", clamp_fps(fps), mod.LONG_MODE))

    mod.write_temp_long_video = write_temp_long_video

    def write_temp_video(video, fps=24, output_path=None, mode=None):
        return write_temp_long_video(video, output_path=output_path, fps=fps)

    mod.write_temp_video = write_temp_video
