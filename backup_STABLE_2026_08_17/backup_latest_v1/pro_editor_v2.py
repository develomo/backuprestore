def make_video():
    voice_file = os.listdir(VOICE_DIR)[0]
    voice = AudioFileClip(os.path.join(VOICE_DIR, voice_file))
    voice_duration = voice.duration

    clips = []
    clip_files = sorted(os.listdir(CLIPS_DIR))

    per_clip = 1.0 if voice_duration <= 60 else 2.5
    mode = "SHORT" if voice_duration <= 60 else "LONG"

    total = 0

    for f in clip_files:
        if total >= voice_duration:
            break

        clip = VideoFileClip(os.path.join(CLIPS_DIR, f))

        usable = min(per_clip, clip.duration)
        clip = clip.subclip(0, usable)

        clip = clip.fx(vfx.resize, 1.05)
        clip = clip.fx(vfx.colorx, 1.1)

        clips.append(clip)
        total += clip.duration

    video = concatenate_videoclips(clips, method="compose")

    # 🛑 SAFETY FIX (NO BLACK SCREEN)
    if video.duration < voice_duration:
        last = video.to_ImageClip(t=video.duration - 0.05).set_duration(
            voice_duration - video.duration
        )
        video = concatenate_videoclips([video, last])

    video = video.set_duration(voice_duration)

    music_file = os.listdir(MUSIC_DIR)[0]
    music = AudioFileClip(os.path.join(MUSIC_DIR, music_file)) \
        .volumex(0.12) \
        .set_duration(voice_duration)

    audio = CompositeAudioClip([voice, music])
    video = video.set_audio(audio)

    if mode == "SHORT":
        video = video.crop(
            x_center=video.w / 2,
            y_center=video.h / 2,
            width=video.h * 9 / 16,
            height=video.h
        ).resize((1080, 1920))

    out = os.path.join(
        OUT_DIR,
        voice_file.replace(".mp3", "") + f"_{mode}_FINAL_PRO.mp4"
    )

    video.write_videofile(
        out,
        fps=30,
        codec="libx264",
        audio_codec="aac"
    )

    print("🎬 FINAL VIDEO (BLACK SCREEN FIXED):", out)
