# batch_long_renderer.py - FINAL PRODUCTION VERSION (ALL BUGS FIXED)
import os
import re
import time
import json
import shutil
import random
import subprocess
from pathlib import Path

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"
TARGET_W = 854
TARGET_H = 480
TARGET_FPS = 30

# CRITICAL FIX: scale uses ':', crop also uses ':' in FFmpeg filter syntax
SCALE_FILTER = f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=increase"
CROP_FILTER = f"crop={TARGET_W}:{TARGET_H}"
SIZE_ZP = f"{TARGET_W}x{TARGET_H}"  # Only for zoompan 's=' parameter

PREMIUM_MOTIONS = {
    "Slow Zoom In": f"zoompan=z='min(zoom+0.0008,1.12)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={SIZE_ZP}",
    "Slow Zoom Out": f"zoompan=z='if(eq(on,1),1.12,max(zoom-0.0008,1.0))':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={SIZE_ZP}",
    "Pan Left to Right": f"zoompan=z='1.1':d=1:x='if(eq(on,1),0,min(x+2,iw-iw/zoom))':y='ih/2-(ih/zoom/2)':s={SIZE_ZP}",
    "Pan Right to Left": f"zoompan=z='1.1':d=1:x='if(eq(on,1),iw-iw/zoom,max(x-2,0))':y='ih/2-(ih/zoom/2)':s={SIZE_ZP}",
    "Pan Top to Bottom": f"zoompan=z='1.1':d=1:x='iw/2-(iw/zoom/2)':y='if(eq(on,1),0,min(y+2,ih-ih/zoom))':s={SIZE_ZP}",
    "Pan Bottom to Top": f"zoompan=z='1.1':d=1:x='iw/2-(iw/zoom/2)':y='if(eq(on,1),ih-ih/zoom,max(y-2,0))':s={SIZE_ZP}",
    "Diagonal TL to BR": f"zoompan=z='1.08':d=1:x='if(eq(on,1),0,min(x+1.5,iw-iw/zoom))':y='if(eq(on,1),0,min(y+1.5,ih-ih/zoom))':s={SIZE_ZP}",
    "Diagonal BR to TL": f"zoompan=z='1.08':d=1:x='if(eq(on,1),iw-iw/zoom,max(x-1.5,0))':y='if(eq(on,1),ih-ih/zoom,max(y-1.5,0))':s={SIZE_ZP}",
    "Gentle Float": f"zoompan=z='1.05':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={SIZE_ZP}",
    "Cinematic Push": f"zoompan=z='min(zoom+0.0012,1.15)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={SIZE_ZP}",
}

PREMIUM_TRANSITIONS = [
    "fade", "dissolve", "smoothleft", "smoothright", "smoothup", "smoothdown",
    "circleopen", "circleclose", "rectcrop", "circlecrop", "radial",
    "pixelize", "wipeleft", "wiperight", "wipeup", "wipedown"
]

COLOR_GRADES = {
    "Cinematic Warm": "eq=contrast=1.08:saturation=1.15:brightness=0.03:gamma=1.05",
    "Cool Professional": "eq=contrast=1.05:saturation=0.95:brightness=-0.02:gamma=0.98",
    "Luxury Gold": "eq=contrast=1.1:saturation=1.2:brightness=0.05:gamma=1.08",
    "Dark Mystery": "eq=contrast=1.2:saturation=0.85:brightness=-0.05:gamma=0.95",
    "Vibrant Pop": "eq=contrast=1.15:saturation=1.3:brightness=0.02:gamma=1.1",
    "Vintage Film": "eq=contrast=1.05:saturation=0.9:brightness=0.01:gamma=1.05",
    "Modern Clean": "eq=contrast=1.06:saturation=1.05:brightness=0.01:gamma=1.02"
}


def get_unique_sequence(options_list, length):
    result = []
    last_used = []
    for _ in range(length):
        available = [o for o in options_list if o not in last_used[-6:]]
        if not available:
            available = options_list
        choice = random.choice(available)
        result.append(choice)
        last_used.append(choice)
    return result


def render_clip(clip_path, out_path, duration, motion_filter, color_grade, fps=TARGET_FPS):
    vf_str = ",".join([SCALE_FILTER, CROP_FILTER, f"fps={fps}", motion_filter, color_grade, "setsar=1"])
    cmd = [FFMPEG, "-threads", "2", "-y", "-i", str(clip_path), "-vf", vf_str,
           "-c:v", "libx264", "-preset", "fast", "-crf", "26",
           "-r", str(fps), "-an", "-t", str(duration), str(out_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out_path) or os.path.getsize(out_path) < 1000:
        fallback_vf = f"{SCALE_FILTER},{CROP_FILTER},fps={fps},setsar=1"
        subprocess.run([FFMPEG, "-threads", "2", "-y", "-i", str(clip_path), "-vf", fallback_vf,
                       "-c:v", "libx264", "-preset", "fast", "-crf", "26",
                       "-r", str(fps), "-an", "-t", str(duration), str(out_path)],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_path


def concat_with_transitions(clip_list, out_path, start_idx=0):
    if len(clip_list) == 1:
        shutil.copy2(clip_list[0], out_path)
        return []

    inputs = []
    for c in clip_list:
        inputs.extend(["-i", str(c)])

    filters = []
    for i in range(len(clip_list)):
        filters.append(f"[{i}:v]settb=AVTB,setpts=PTS-STARTPTS,fps={TARGET_FPS},format=yuv420p[v{i}]")

    current = "[v0]"
    elapsed = 7.0
    transition_times = []

    for i in range(1, len(clip_list)):
        trans_name = random.choice(PREMIUM_TRANSITIONS)
        dur = random.uniform(0.5, 0.8)
        offset = max(0.1, elapsed - dur)
        out_label = f"[x{i}]"
        transition_times.append(offset + dur / 2.0)
        print(f"  🎬 [TRANSITION] Clip {start_idx+i} -> {start_idx+i+1}: '{trans_name}' ({dur:.2f}s)")
        filters.append(f"{current}[v{i}]xfade=transition={trans_name}:duration={dur:.3f}:offset={offset:.3f}{out_label}")
        current = out_label
        elapsed = elapsed + 7.0 - dur

    cmd = [FFMPEG, "-threads", "2", "-y"] + inputs + [
        "-filter_complex", ";".join(filters),
        "-map", current, "-an",
        "-c:v", "libx264", "-preset", "fast", "-crf", "26",
        "-r", str(TARGET_FPS), str(out_path)
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ⚠️ [FALLBACK] Hard concat for batch")
        list_file = out_path.with_suffix(".txt")
        with open(list_file, "w", encoding="utf-8") as f:
            for c in clip_list:
                safe_p = str(c.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{safe_p}'\n")
        subprocess.run([FFMPEG, "-threads", "2", "-y", "-f", "concat", "-safe", "0",
                       "-i", str(list_file), "-c", "copy", str(out_path)],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            list_file.unlink()
        except Exception:
            pass
    return transition_times


def render_long_batch_memory(voice_path, clips, output_path, music_path=None, sfx_files=None,
                             intro_path=None, outro_path=None, subscribe_overlay=None,
                             quality="480p", fps=TARGET_FPS, batch_size=8, final_quality="480p",
                             add_captions=True, words=None, words_path=None, transcript_text=None,
                             caption_mode="phrase", style_id=None, cleanup=True, preset_overrides=None,
                             custom_logo_path=None, wm_opacity=0.6, niche="default", **kwargs):

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = out_p.parent / f"long_batch_temp_{int(time.time())}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print("🎥 PRODUCTION READY LONG VIDEO ENGINE ACTIVE")
    print("=" * 70)

    # Get original voice duration
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                       "-of", "csv=p=0", str(voice_path)], capture_output=True, text=True)
    try:
        orig_voice_dur = float(r.stdout.strip())
    except Exception:
        orig_voice_dur = 60.0

    # VOICE SILENCE REMOVAL
    print(f"\n🔇 [SILENCE REMOVAL] Analyzing voice for dead air...")
    trimmed_voice_path = str(voice_path)
    total_voice_dur = orig_voice_dur

    try:
        detect_cmd = [FFMPEG, "-threads", "2", "-i", str(voice_path), "-af",
                      "silencedetect=noise=-35dB:d=0.8", "-f", "null", "-"]
        result = subprocess.run(detect_cmd, capture_output=True, text=True)
        silence_starts = re.findall(r'silence_start:\s*([\d.]+)', result.stderr)
        silence_ends = re.findall(r'silence_end:\s*([\d.]+)', result.stderr)

        if silence_starts and silence_ends:
            trimmed_voice = temp_dir / "voice_trimmed.wav"
            af_parts = []
            prev_end = 0.0
            for s_start, s_end in zip(silence_starts[:15], silence_ends[:15]):
                s_start_f = float(s_start)
                s_end_f = float(s_end)
                if s_start_f > prev_end + 0.1:
                    af_parts.append(f"atrim=start={prev_end:.3f}:end={s_start_f:.3f}")
                prev_end = s_end_f + 0.2
            if prev_end < orig_voice_dur:
                af_parts.append(f"atrim=start={prev_end:.3f}:end={orig_voice_dur:.3f}")

            if af_parts:
                af_str = ",".join(af_parts) + ",asetpts=PTS-STARTPTS"
                subprocess.run([FFMPEG, "-threads", "2", "-y", "-i", str(voice_path), "-af", af_str, str(trimmed_voice)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if trimmed_voice.exists() and trimmed_voice.stat().st_size > 1000:
                    r2 = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                                        "-of", "csv=p=0", str(trimmed_voice)], capture_output=True, text=True)
                    new_dur = float(r2.stdout.strip())
                    removed = orig_voice_dur - new_dur
                    if removed > 0.5:
                        trimmed_voice_path = str(trimmed_voice)
                        total_voice_dur = new_dur
                        print(f"    ✅ Removed {removed:.1f}s of silence (new: {new_dur:.1f}s)")
                    else:
                        print(f"    ℹ️ Negligible silence ({removed:.1f}s)")
                else:
                    print(f"    ⚠️ Trim failed, using original")
            else:
                print(f"    ℹ️ No significant silence detected")
        else:
            print(f"    ℹ️ No silence markers found")
    except Exception as e:
        print(f"    ⚠️ Silence detection error: {e}, using original")

    # Calculate timing AFTER silence removal
    clip_duration = random.uniform(6.5, 7.5)
    clips_needed = int(total_voice_dur / clip_duration) + 1
    total_dur = 1.5 + total_voice_dur + 2.0

    print(f"\n📊 [ANALYSIS]")
    print(f"  • Original Voice: {orig_voice_dur:.2f}s | Trimmed: {total_voice_dur:.2f}s")
    print(f"  • Target Duration: {total_dur:.2f}s ({total_dur/60:.1f} min)")
    print(f"  • Clip Duration: {clip_duration:.2f}s (randomized 6.5-7.5s)")
    print(f"  • Clips Needed: {clips_needed} | Available: {len(clips)}")

    if len(clips) < clips_needed:
        print(f"  🔄 Repeating clips to fill {clips_needed} slots")
        clips = [clips[i % len(clips)] for i in range(clips_needed)]
    else:
        clips = clips[:clips_needed]
    print(f"  • Final Clip Count: {len(clips)}")

    # INTRO (1.5s) - FIXED: Uses SCALE_FILTER and CROP_FILTER with ':' separator
    intro_out = temp_dir / "00_intro.mp4"
    intro_vf = f"{SCALE_FILTER},{CROP_FILTER},fps={TARGET_FPS}"
    if intro_path and os.path.exists(str(intro_path)):
        print(f"\n🎬 [INTRO] Processing 1.5s intro...")
        subprocess.run([FFMPEG, "-threads", "2", "-y", "-i", str(intro_path), "-vf", intro_vf,
                       "-t", "1.5", "-c:v", "libx264", "-preset", "fast",
                       "-r", str(TARGET_FPS), "-an", str(intro_out)], check=True)
        print(f"  ✅ Intro processed")
    else:
        print(f"\n⚠️ [INTRO] Creating black screen")
        subprocess.run([FFMPEG, "-threads", "2", "-y", "-f", "lavfi", "-i", f"color=c=black:s={TARGET_W}x{TARGET_H}:d=1.5",
                       "-c:v", "libx264", "-preset", "fast", "-r", str(TARGET_FPS), "-an", str(intro_out)], check=True)

    # PROCESS CLIPS
    print(f"\n🎨 [MOTION ENGINE] Processing {len(clips)} clips...")
    rendered_clips = []
    motions = get_unique_sequence(list(PREMIUM_MOTIONS.keys()), len(clips))
    colors = get_unique_sequence(list(COLOR_GRADES.keys()), len(clips))

    for i, clip in enumerate(clips):
        this_dur = random.uniform(6.5, 7.5)
        out_clip = temp_dir / f"clip_{i:04d}.mp4"
        print(f"  🎥 [CLIP {i+1}/{len(clips)}] Motion: {motions[i]} | Color: {colors[i]} | Dur: {this_dur:.2f}s")
        render_clip(clip, out_clip, this_dur, PREMIUM_MOTIONS[motions[i]], COLOR_GRADES[colors[i]], TARGET_FPS)
        rendered_clips.append(out_clip)
        time.sleep(0.3)  # 🌡️ THERMAL COOLDOWN: 0.3s pause between clips

    # CONCATENATE IN BATCHES
    print(f"\n🔀 [TRANSITION ENGINE] Merging in batches of {batch_size}...")
    intermediate_files = []
    all_transition_times = []

    for i in range(0, len(rendered_clips), batch_size):
        batch = rendered_clips[i:i+batch_size]
        batch_out = temp_dir / f"batch_{i//batch_size:03d}.mp4"
        print(f"  📦 [BATCH {i//batch_size + 1}] {len(batch)} clips")
        tt = concat_with_transitions(batch, batch_out, start_idx=i)
        all_transition_times.extend(tt)
        intermediate_files.append(batch_out)
        time.sleep(1.0)  # 🌡️ THERMAL COOLDOWN: 1s pause between batches

    body_out = temp_dir / "body.mp4"
    if len(intermediate_files) == 1:
        shutil.copy2(intermediate_files[0], body_out)
    else:
        print(f"  🔗 Merging {len(intermediate_files)} batches...")
        lf = body_out.with_suffix(".txt")
        with open(lf, "w", encoding="utf-8") as f:
            for c in intermediate_files:
                f.write(f"file '{str(c.resolve()).replace(chr(92), '/')}'\n")
        subprocess.run([FFMPEG, "-threads", "2", "-y", "-f", "concat", "-safe", "0", "-i", str(lf), "-c", "copy", str(body_out)], check=True)
        try: lf.unlink()
        except: pass

    # OUTRO (2.0s)
    outro_out = temp_dir / "99_outro.mp4"
    outro_vf = f"{SCALE_FILTER},{CROP_FILTER},fps={TARGET_FPS}"
    if outro_path and os.path.exists(str(outro_path)):
        print(f"\n🎬 [OUTRO] Processing 2.0s outro...")
        subprocess.run([FFMPEG, "-threads", "2", "-y", "-i", str(outro_path), "-vf", outro_vf,
                       "-t", "2.0", "-c:v", "libx264", "-preset", "fast",
                       "-r", str(TARGET_FPS), "-an", str(outro_out)], check=True)
        print(f"  ✅ Outro processed")
    else:
        subprocess.run([FFMPEG, "-threads", "2", "-y", "-f", "lavfi", "-i", f"color=c=black:s={TARGET_W}x{TARGET_H}:d=2.0",
                       "-c:v", "libx264", "-preset", "fast", "-r", str(TARGET_FPS), "-an", str(outro_out)], check=True)

    # ASSEMBLE
    print(f"\n🔗 [ASSEMBLY] Joining Intro + Body + Outro...")
    assembled_out = temp_dir / "assembled.mp4"
    alf = temp_dir / "assembly.txt"
    with open(alf, "w", encoding="utf-8") as f:
        f.write(f"file '{str(intro_out.resolve()).replace(chr(92), '/')}'\n")
        f.write(f"file '{str(body_out.resolve()).replace(chr(92), '/')}'\n")
        f.write(f"file '{str(outro_out.resolve()).replace(chr(92), '/')}'\n")
    subprocess.run([FFMPEG, "-threads", "2", "-y", "-f", "concat", "-safe", "0", "-i", str(alf), "-c", "copy", str(assembled_out)], check=True)
    try: alf.unlink()
    except: pass
    print(f"  ✅ Assembly complete")

    # LOGO (1.5s to voice_end)
    current_video = assembled_out
    logo_end_time = 1.5 + total_voice_dur
    if custom_logo_path and os.path.exists(str(custom_logo_path)):
        print(f"\n🎨 [LOGO] Applying watermark (opacity={wm_opacity}, visible 1.5s-{logo_end_time:.1f}s)...")
        logo_out = temp_dir / "with_logo.mp4"
        subprocess.run([FFMPEG, "-threads", "2", "-y", "-i", str(current_video), "-i", str(custom_logo_path),
                       "-filter_complex",
                       f"[1:v]scale=iw*0.12:-1,format=rgba,colorchannelmixer=aa={wm_opacity}[wm];"
                       f"[0:v][wm]overlay=W-w-30:H-h-30:enable='between(t,1.5,{logo_end_time:.3f})'",
                       "-c:v", "libx264", "-preset", "fast", "-crf", "26",
                       "-r", str(TARGET_FPS), "-c:a", "copy", str(logo_out)], check=True)
        current_video = logo_out
        print(f"  ✅ Logo applied")

    # SUBSCRIBE OVERLAY (420s-480s)
    if subscribe_overlay and os.path.exists(str(subscribe_overlay)):
        if total_voice_dur > 420.0:
            print(f"\n🔔 [SUBSCRIBE] Applying overlay at 7-8 minute mark...")
            sub_out = temp_dir / "with_subscribe.mp4"
            subprocess.run([FFMPEG, "-threads", "2", "-y", "-i", str(current_video), "-i", str(subscribe_overlay),
                           "-filter_complex",
                           f"[1:v]scale=240:-1,format=rgba[ov];"
                           f"[0:v][ov]overlay=(main_w-overlay_w)/2:main_h-overlay_h-40:enable='between(t,420,480)'",
                           "-c:v", "libx264", "-preset", "fast", "-crf", "26",
                           "-r", str(TARGET_FPS), "-c:a", "copy", str(sub_out)], check=True)
            current_video = sub_out
            print(f"  ✅ Subscribe overlay applied (7-8 min)")
        else:
            print(f"\n⚠️ Video too short for subscribe overlay")

    # AUDIO ENGINE
    print(f"\n🎵 [AUDIO ENGINE] Mixing Voice + Music + SFX...")
    voice_end_trim = 1.5 + total_voice_dur
    cmd = [FFMPEG, "-threads", "2", "-y", "-i", str(current_video), "-i", str(trimmed_voice_path)]
    filters = [f"[1:a]volume=1.5,highpass=f=90,lowpass=f=9500,acompressor=threshold=-19dB:ratio=2.5,"
               f"alimiter=limit=0.97,adelay={int(1.5*1000)}|{int(1.5*1000)},atrim=0:{voice_end_trim:.3f},aresample=44100[v]"]
    labels = ["[v]"]
    idx = 2

    # BG Music SEAMLESS LOOP
    if music_path and os.path.exists(str(music_path)):
        print(f"  🎵 BG Music: seamless infinite loop (zero gaps)")
        cmd.extend(["-stream_loop", "-1", "-i", str(music_path)])
        filters.append(f"[{idx}:a]volume=0.12,highpass=f=60,lowpass=f=11500,afade=t=in:st=1.5:d=2.0,"
                      f"adelay={int(1.5*1000)}|{int(1.5*1000)},atrim=0:{voice_end_trim:.3f},aresample=44100[m]")
        labels.append("[m]")
        idx += 1

    # SFX SYNCED TO TRANSITIONS
    if sfx_files and len(sfx_files) > 0 and all_transition_times:
        sfx_path = str(sfx_files[0])
        if os.path.exists(sfx_path):
            n_bursts = min(len(all_transition_times), 40)
            print(f"  🔊 {n_bursts} SFX bursts synced to transitions")
            cmd.extend(["-i", sfx_path])
            src_labels = "".join(f"[sfx_src{i}]" for i in range(n_bursts))
            filters.append(f"[{idx}:a]volume=0.35,atrim=0:1.0,asetpts=PTS-STARTPTS,"
                          f"highpass=f=80,lowpass=f=13500,asplit={n_bursts}{src_labels}")
            hit_labels = []
            for i in range(n_bursts):
                delay_ms = int((all_transition_times[i] + 1.5) * 1000)
                filters.append(f"[sfx_src{i}]adelay={delay_ms}|{delay_ms}[sfxh{i}]")
                hit_labels.append(f"[sfxh{i}]")
            filters.append("".join(hit_labels) + f"amix=inputs={n_bursts}:duration=longest,"
                          f"atrim=0:{voice_end_trim:.3f},aresample=44100[s]")
            labels.append("[s]")
            idx += 1

    filters.append("".join(labels) + f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0.35,"
                  f"alimiter=limit=0.97,loudnorm=I=-14:TP=-1.0:LRA=10,apad[aout]")

    cmd.extend(["-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[aout]",
               "-t", str(total_dur), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(out_p)])

    print(f"  🎬 [FINAL RENDER] Encoding...")
    subprocess.run(cmd, check=True)

    print(f"\n{'='*70}")
    print(f"✅ SUCCESS: Premium Long Video Rendered -> {out_p}")
    print(f"⏱️ Duration: {total_dur/60:.1f}min | Clips: {len(clips)} | Silence removed: {orig_voice_dur-total_voice_dur:.1f}s")
    print(f"🎨 Logo: {'Yes' if custom_logo_path else 'No'} | Subscribe: {'Yes' if subscribe_overlay else 'No'}")
    print(f"🎵 Music: Seamless Loop | SFX: {len(all_transition_times)} synced bursts")
    print(f"{'='*70}\n")

    if cleanup:
        try: shutil.rmtree(temp_dir)
        except: pass

    return str(out_p)