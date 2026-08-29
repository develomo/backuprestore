# Fix truncated batch_long_renderer.py

c = open('batch_long_renderer.py', 'r', encoding='utf-8').readlines()

# Fix line 2617 (incomplete)
if c[2616].strip().endswith('PTS-STARTP'):
    c[2616] = '                       f"trim=0:{body_target:.3f},setpts=PTS-STARTPTS")\n'

# Add missing code after line 2617
missing = '''        else:
            # Trim to exact duration
            log(f"[Body Fit] Trimming by {body_actual - body_target:.1f}s")
            body_fixed = batch_dir / "body_fixed.mp4"
            run_cmd([
                FFMPEG, "-y",
                "-i", str(body_raw),
                "-vf", f"trim=0:{body_target:.3f},setpts=PTS-STARTPTS",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "26",
                "-pix_fmt", "yuv420p",
                "-an",
                str(body_fixed),
            ])
    else:
        body_fixed = body_raw
    
    # BUG 1 FIX: Append outro as SEPARATE segment (no audio bleed)
    if outro_out:
        body_and_outro = batch_dir / "body_with_outro.mp4"
        concat_files_hard([body_fixed, outro_out], body_and_outro)
        body_final = body_and_outro
    else:
        body_final = body_fixed
    
    # ================================================================
    # STAGE 4: POST-PRODUCTION
    # ================================================================
    log("=" * 60)
    log("STAGE 4: POST-PRODUCTION - Subscribe overlay, watermark, B-roll")
    log("=" * 60)
    
    post_video = body_final
    
    # Subscribe overlay (BUG 3 FIX: correct mid position)
    if subscribe_overlay:
        post_sub = batch_dir / "post_sub.mp4"
        apply_subscribe_overlay_mid(
            post_video, subscribe_overlay, post_sub,
            intro_sec=intro_sec,
            voice_duration=voice_duration,
            total_duration=total_duration,
        )
        post_video = post_sub
    
    # Watermark (BUG 2 FIX: custom logo + opacity)
    post_wm = batch_dir / "post_wm.mp4"
    apply_niche_watermark(
        post_video, post_wm, niche,
        custom_logo_path=custom_logo_path,
        opacity=wm_opacity,
    )
    post_video = post_wm
    
    # B-roll overlay
    post_broll = batch_dir / "post_broll.mp4"
    apply_broll_overlay(post_video, post_broll, total_duration, niche)
    post_video = post_broll
    
    # ================================================================
    # STAGE 5: CAPTIONS
    # ================================================================
    log("=" * 60)
    log("STAGE 5: CAPTIONS - Burning captions")
    log("=" * 60)
    
    if add_captions:
        post_captions = batch_dir / "post_captions.mp4"
        burn_captions(
            post_video, post_captions,
            voice_path=str(voice_path),
            words=words,
            words_path=words_path,
            transcript_text=transcript_text,
            caption_mode=caption_mode,
            size=size,
            caption_offset=intro_sec,
            niche=niche,
        )
        post_video = post_captions
    else:
        log("[Caption] DISABLED per config")
    
    # ================================================================
    # STAGE 6: AUDIO MIX
    # ================================================================
    log("=" * 60)
    log("STAGE 6: AUDIO MIX - Voice + Music + SFX (BUG 5: burst mode)")
    log("=" * 60)
    
    final_out = Path(output_path)
    final_out.parent.mkdir(parents=True, exist_ok=True)
    
    mux_audio_timeline(
        post_video, voice_path, final_out,
        music=music_path,
        sfx=sfx_path,
        total_duration=total_duration,
        intro_sec=intro_sec,
        voice_duration=voice_duration,
        niche=niche,
    )
    
    # ================================================================
    # STAGE 7: CLEANUP
    # ================================================================
    log("=" * 60)
    log("STAGE 7: FINALIZE")
    log("=" * 60)
    
    elapsed = time.time() - start_time
    corrupt_count = len(corrupt_clips)
    
    log(f"[COMPLETE] Output: {final_out}")
    log(f"[COMPLETE] Duration: {total_duration:.1f}s | "
        f"Clips: {rendered_count}/{len(clip_paths)} | "
        f"Skipped: {corrupt_count} | "
        f"Time: {elapsed:.0f}s ({elapsed/60:.1f}min)")
    
    if corrupt_clips:
        log(f"[WARNING] {corrupt_count} clip(s) were skipped:")
        for cc in corrupt_clips[:5]:
            log(f"  - Clip #{cc['clip_index']}: {Path(cc['clip_path']).name}: {cc['error']}")
    
    # Cleanup temp files
    if not keep_temp:
        try:
            shutil.rmtree(temp_root, ignore_errors=True)
            log("[Cleanup] Temp directory removed")
        except Exception as e:
            log(f"[Cleanup] Could not remove temp: {e}")
    
    return str(final_out)
'''

# Insert missing code
c[2617:2617] = [missing]

# Write back
open('batch_long_renderer.py', 'w', encoding='utf-8').writelines(c)
print('DONE - File fixed!')
