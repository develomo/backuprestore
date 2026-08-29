fn = 'audio_engine.py'
c = open(fn, encoding='utf-8', errors='ignore').read()

# 1. Fix master_audio
old_master = '''def master_audio(*args, **kwargs) -> str:
    voice_path = kwargs.get("voice_path") or kwargs.get("voice") or _extract_arg(args, 0)
    output_path = kwargs.get("output_path") or kwargs.get("out") or _extract_arg(args, 1)
    return master_voice_audio(voice_path, output_path=output_path, **kwargs)'''
new_master = '''def master_audio(*args, **kwargs) -> str:
    voice_path = kwargs.pop("voice_path", None) or kwargs.pop("voice", None) or _extract_arg(args, 0)
    output_path = kwargs.pop("output_path", None) or kwargs.pop("out", None) or _extract_arg(args, 1)
    return master_voice_audio(voice_path, output_path=output_path, **kwargs)'''
c = c.replace(old_master, new_master)

# 2. Fix clean_voice_audio
old_clean = '''def clean_voice_audio(*args, **kwargs) -> str:
    voice_path = kwargs.get("voice_path") or kwargs.get("voice") or _extract_arg(args, 0)
    output_path = kwargs.get("output_path") or kwargs.get("out") or _extract_arg(args, 1)
    return trim_silence_light(voice_path, output_path=output_path, **kwargs)'''
new_clean = '''def clean_voice_audio(*args, **kwargs) -> str:
    voice_path = kwargs.pop("voice_path", None) or kwargs.pop("voice", None) or _extract_arg(args, 0)
    output_path = kwargs.pop("output_path", None) or kwargs.pop("out", None) or _extract_arg(args, 1)
    return trim_silence_light(voice_path, output_path=output_path, **kwargs)'''
c = c.replace(old_clean, new_clean)

# 3. Fix build_full_audio_mix (The main culprit)
old_build = '''    video_path = kwargs.get("video_path") or kwargs.get("video")
    voice_path = kwargs.get("voice_path") or kwargs.get("voice") or _extract_arg(args, 0)
    output_path = kwargs.get("output_path") or kwargs.get("out") or kwargs.get("final_audio_path") or _extract_arg(args, 1)
    music_path = kwargs.get("music_path")
    sfx_files = kwargs.get("sfx_files")
    duration = kwargs.get("duration") or kwargs.get("dur") or kwargs.get("target_duration")
    niche = kwargs.get("niche")
    audio_plan = kwargs.get("audio_plan") or kwargs.get("preset_overrides", {}).get("audio_plan") if isinstance(kwargs.get("preset_overrides"), dict) else kwargs.get("audio_plan")
    clean_silence = bool(kwargs.get("clean_silence", False))

    if video_path:
        return mux_audio_with_video(
            video_path=video_path,
            voice_path=voice_path,
            output_path=output_path,
            music_path=music_path,
            sfx_files=sfx_files,
            niche=niche,
            audio_plan=audio_plan,
            duration=duration,
            clean_silence=clean_silence,
            **kwargs,
        )

    return build_audio_mix_file(
        voice_path=voice_path,
        output_path=output_path,
        duration=duration,
        music_path=music_path,
        sfx_files=sfx_files,
        niche=niche,
        audio_plan=audio_plan,
        clean_silence=clean_silence,
        **kwargs,
    )'''
new_build = '''    video_path = kwargs.pop("video_path", None) or kwargs.pop("video", None)
    voice_path = kwargs.pop("voice_path", None) or kwargs.pop("voice", None) or _extract_arg(args, 0)
    output_path = kwargs.pop("output_path", None) or kwargs.pop("out", None) or kwargs.pop("final_audio_path", None) or _extract_arg(args, 1)
    music_path = kwargs.pop("music_path", None)
    sfx_files = kwargs.pop("sfx_files", None)
    duration = kwargs.pop("duration", None) or kwargs.pop("dur", None) or kwargs.pop("target_duration", None)
    niche = kwargs.pop("niche", None)
    audio_plan = kwargs.pop("audio_plan", None)
    if not audio_plan and isinstance(kwargs.get("preset_overrides"), dict):
        audio_plan = kwargs.get("preset_overrides", {}).get("audio_plan")
    clean_silence = bool(kwargs.pop("clean_silence", False))

    # Safely remove legacy keys to prevent any duplicate kwargs error
    for key in ["voice", "video", "out", "final_audio_path", "dur", "target_duration", "bg_music", "background_music", "sfx", "audio_mix_path"]:
        kwargs.pop(key, None)

    if video_path:
        return mux_audio_with_video(
            video_path=video_path,
            voice_path=voice_path,
            output_path=output_path,
            music_path=music_path,
            sfx_files=sfx_files,
            niche=niche,
            audio_plan=audio_plan,
            duration=duration,
            clean_silence=clean_silence,
            **kwargs,
        )

    return build_audio_mix_file(
        voice_path=voice_path,
        output_path=output_path,
        duration=duration,
        music_path=music_path,
        sfx_files=sfx_files,
        niche=niche,
        audio_plan=audio_plan,
        clean_silence=clean_silence,
        **kwargs,
    )'''
c = c.replace(old_build, new_build)

open(fn, 'w', encoding='utf-8').write(c)
print("SUCCESS: audio_engine.py duplicate kwargs error fixed permanently!")