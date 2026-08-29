fn = 'audio_engine.py'
c = open(fn, encoding='utf-8', errors='ignore').read()

start_marker = "def build_full_audio_mix(*args, **kwargs) -> str:"
end_marker = "def build_integrated_audio_for_pipeline(*args, **kwargs) -> str:"

if start_marker in c and end_marker in c:
    start_idx = c.find(start_marker)
    end_idx = c.find(end_marker)
    
    # Naya 100% error-free function
    new_func = '''def build_full_audio_mix(*args, **kwargs) -> str:
        """Backward compatible full audio mix builder.

        Supported common calls:
        - build_full_audio_mix(voice_path, output_path, music_path=..., sfx_files=...)
        - build_full_audio_mix(voice_path=..., output_path=..., ...)
        - build_full_audio_mix(video_path=..., voice_path=..., output_path=...) -> mux
        """
        kwargs = _normalize_legacy_kwargs(kwargs)

        # CRITICAL FIX: Pop all named arguments from kwargs so they are NEVER passed twice via **kwargs
        video_path = kwargs.pop("video_path", None) or kwargs.pop("video", None)
        voice_path = kwargs.pop("voice_path", None) or kwargs.pop("voice", None) or _extract_arg(args, 0)
        output_path = kwargs.pop("output_path", None) or kwargs.pop("out", None) or kwargs.pop("final_audio_path", None) or _extract_arg(args, 1)
        music_path = kwargs.pop("music_path", None) or kwargs.pop("bg_music", None) or kwargs.pop("background_music", None)
        sfx_files = kwargs.pop("sfx_files", None) or kwargs.pop("sfx", None)
        duration = kwargs.pop("duration", None) or kwargs.pop("dur", None) or kwargs.pop("target_duration", None)
        niche = kwargs.pop("niche", None)
        audio_plan = kwargs.pop("audio_plan", None)
        if not audio_plan and isinstance(kwargs.get("preset_overrides"), dict):
            audio_plan = kwargs.get("preset_overrides", {}).get("audio_plan")
        clean_silence = bool(kwargs.pop("clean_silence", False))

        # Safely remove any other conflicting legacy keys
        for key in ["voice", "video", "out", "final_audio_path", "dur", "target_duration", "bg_music", "background_music", "sfx", "audio_mix_path", "preset_overrides"]:
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
        )

    '''

    c_new = c[:start_idx] + new_func + c[end_idx:]
    
    # Fix master_audio and clean_voice_audio as well just in case
    c_new = c_new.replace(
        '''def master_audio(*args, **kwargs) -> str:
        voice_path = kwargs.get("voice_path") or kwargs.get("voice") or _extract_arg(args, 0)
        output_path = kwargs.get("output_path") or kwargs.get("out") or _extract_arg(args, 1)
        return master_voice_audio(voice_path, output_path=output_path, **kwargs)''',
        '''def master_audio(*args, **kwargs) -> str:
        voice_path = kwargs.pop("voice_path", None) or kwargs.pop("voice", None) or _extract_arg(args, 0)
        output_path = kwargs.pop("output_path", None) or kwargs.pop("out", None) or _extract_arg(args, 1)
        return master_voice_audio(voice_path, output_path=output_path, **kwargs)'''
    )
    c_new = c_new.replace(
        '''def clean_voice_audio(*args, **kwargs) -> str:
        voice_path = kwargs.get("voice_path") or kwargs.get("voice") or _extract_arg(args, 0)
        output_path = kwargs.get("output_path") or kwargs.get("out") or _extract_arg(args, 1)
        return trim_silence_light(voice_path, output_path=output_path, **kwargs)''',
        '''def clean_voice_audio(*args, **kwargs) -> str:
        voice_path = kwargs.pop("voice_path", None) or kwargs.pop("voice", None) or _extract_arg(args, 0)
        output_path = kwargs.pop("output_path", None) or kwargs.pop("out", None) or _extract_arg(args, 1)
        return trim_silence_light(voice_path, output_path=output_path, **kwargs)'''
    )

    if c_new != c:
        open(fn, 'w', encoding='utf-8').write(c_new)
        print("SUCCESS: audio_engine.py duplicate kwargs error fixed permanently!")
    else:
        print("SKIP: No changes made.")
else:
    print("ERROR: Could not find the function boundaries to replace.")