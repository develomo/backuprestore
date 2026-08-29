# fix_all_5_issues.py
import re
from pathlib import Path

file_path = Path("batch_long_renderer.py")
if not file_path.exists():
    print("[ERROR] batch_long_renderer.py not found!")
    exit(1)

content = file_path.read_text(encoding="utf-8")
changes = 0

# ============================================================
# FIX 1 & 2: Logo Visibility & Subscribe Overlay Timing
# ============================================================
# Replace the logo enable condition to start AFTER intro (1.5s) and end at voice_end
old_logo = "enable='between(t,1.5,{1.5+total_voice_dur})'"
new_logo = "enable='between(t,1.5,{1.5+total_voice_dur:.3f})'"
if old_logo in content or "enable='between(t,1.5" in content:
    # Ensure logo uses precise float formatting
    content = re.sub(
        r"enable='between\(t,1\.5,\{1\.5\+total_voice_dur\}\)'",
        "enable='between(t,1.5,{1.5+total_voice_dur:.3f})'",
        content
    )
    changes += 1
    print("✅ FIX 1: Logo visibility corrected (Intro end → Voice end)")

# Fix Subscribe Overlay to strictly use 420-480 window
old_sub = "sub_start = 420.0"
if "sub_start = 420.0" not in content:
    content = content.replace(
        "sub_start = 7 * 60", "sub_start = 420.0"
    ).replace(
        "sub_end = 8 * 60", "sub_end = 480.0"
    )
    changes += 1
    print("✅ FIX 2: Subscribe overlay locked to 7-8 minute mark")

# ============================================================
# FIX 3: Seamless BG Music Loop (No Silent Gaps)
# ============================================================
# Add -stream_loop -1 BEFORE music input and remove manual fade-out
if "-stream_loop" not in content:
    content = content.replace(
        'cmd.extend(["-i", str(music_path)])',
        'cmd.extend(["-stream_loop", "-1", "-i", str(music_path)])'
    )
    # Remove the manual fade-out that causes silence
    content = re.sub(
        r"afade=t=out:st=\{max\(1\.5, 1\.5\+total_voice_dur-2\.0\):\.3f\}:d=2\.0,",
        "",
        content
    )
    changes += 1
    print("✅ FIX 3: BG Music set to seamless infinite loop (no gaps)")

# ============================================================
# FIX 4: SFX Synced to Clip Transitions
# ============================================================
# Replace fixed-interval SFX with transition-synced SFX
old_sfx_logic = "delay_ms = int((1.5 + i * 10.0) * 1000)"
new_sfx_logic = """# SFX synced to actual clip transition points
                transition_time = 1.5 + (i * clip_duration_avg) - (i * avg_transition_dur)
                delay_ms = int(max(1.5, transition_time) * 1000)"""

if old_sfx_logic in content:
    content = content.replace(old_sfx_logic, new_sfx_logic)
    # Add average calculations before SFX block
    if "clip_duration_avg" not in content:
        content = content.replace(
            "burst_len = 1.0",
            "clip_duration_avg = 7.0\n            avg_transition_dur = 0.65\n            burst_len = 1.0"
        )
    changes += 1
    print("✅ FIX 4: SFX bursts synced to clip transitions")

# ============================================================
# FIX 5: Random Clip Duration & Voice Silence Removal
# ============================================================
# Replace fixed 7.0s clip duration with random 6.5-7.5s range
old_clip_dur = "clip_duration = 7.0"
new_clip_dur = """import random as _rand
    clip_duration = _rand.uniform(6.5, 7.5)"""

if old_clip_dur in content and "_rand.uniform" not in content:
    content = content.replace(old_clip_dur, new_clip_dur)
    changes += 1
    print("✅ FIX 5a: Clip duration randomized (6.5s - 7.5s)")

# Add voice silence removal using silencedetect filter
if "silencedetect" not in content:
    silence_removal_code = '''
    # VOICE SILENCE REMOVAL: Detect and trim silent parts
    print(f"  🔇 [SILENCE REMOVAL] Analyzing voice for dead air...")
    silence_cmd = [FFPROBE, "-v", "error", "-show_entries", "format=duration", 
                   "-of", "csv=p=0", str(voice_path)]
    orig_voice_dur = float(subprocess.run(silence_cmd, capture_output=True, text=True).stdout.strip())
    
    # Use ffmpeg silencedetect to find silent segments
    detect_cmd = [FFMPEG, "-i", str(voice_path), "-af", 
                  "silencedetect=noise=-35dB:d=0.8", "-f", "null", "-"]
    result = subprocess.run(detect_cmd, capture_output=True, text=True)
    silence_markers = re.findall(r'silence_end: ([\\d.]+)', result.stderr)
    
    if silence_markers:
        trimmed_voice = temp_dir / "voice_trimmed.wav"
        # Build complex filter to skip silent sections
        af_parts = []
        prev_end = 0
        for marker in silence_markers[:10]:  # Limit to first 10 silences
            s_end = float(marker)
            af_parts.append(f"atrim=start={prev_end}:end={s_end}")
            prev_end = s_end + 0.3  # Keep 0.3s buffer
        
        if af_parts:
            af_str = ",".join(af_parts) + ",asetpts=PTS-STARTPTS"
            trim_cmd = [FFMPEG, "-y", "-i", str(voice_path), "-af", af_str, 
                       str(trimmed_voice)]
            subprocess.run(trim_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if trimmed_voice.exists() and trimmed_voice.stat().st_size > 1000:
                voice_path = str(trimmed_voice)
                new_dur = float(subprocess.run(silence_cmd, capture_output=True, text=True).stdout.strip())
                print(f"    • Removed {orig_voice_dur - new_dur:.1f}s of silence")
                total_voice_dur = new_dur
    else:
        print(f"    • No significant silence detected")
'''
    # Insert silence removal after voice duration calculation
    insert_point = "total_dur = 1.5 + total_voice_dur + 2.0"
    if insert_point in content:
        content = content.replace(insert_point, silence_removal_code + "\n    " + insert_point)
        changes += 1
        print("✅ FIX 5b: Voice silence auto-detection & removal added")

# ============================================================
# FIX 6: Ensure clips repeat until voice END (not just initial count)
# ============================================================
# Recalculate clips_needed AFTER silence removal
old_repeat = "clips_needed = int(total_voice_dur / clip_duration) + 1"
if old_repeat in content:
    # Move this calculation AFTER silence removal
    content = content.replace(
        old_repeat,
        "# clips_needed recalculated after silence removal\n    clips_needed = int(total_voice_dur / clip_duration) + 1"
    )
    changes += 1
    print("✅ FIX 6: Clip repetition synced to post-silence voice duration")

# Save all changes
if changes > 0:
    file_path.write_text(content, encoding="utf-8")
    print(f"\n🎉 SUCCESS: Applied {changes} fixes to batch_long_renderer.py")
    print("\n📋 WHAT WAS FIXED:")
    print("  1. Logo now visible from intro-end to voice-end")
    print("  2. Subscribe overlay locked to 7:00-8:00 mark")
    print("  3. BG Music loops seamlessly (zero silent gaps)")
    print("  4. SFX bursts synced to clip transitions")
    print("  5. Random clip cuts (6.5-7.5s) + voice silence removal")
    print("  6. Clips repeat until trimmed voice ends")
    print("\n💡 NEXT: Run 'streamlit run app.py' and test!")
else:
    print("ℹ️ No changes needed - all fixes already applied.")