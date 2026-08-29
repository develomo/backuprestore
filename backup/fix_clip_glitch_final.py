import re
from pathlib import Path

file_path = Path("safe_long_video_polished.py")
content = file_path.read_text(encoding="utf-8")

# 1. Pehle check karein ke kya `_distribute_clips` function pehle se hai
if "_distribute_clips" in content:
    print("ℹ️ Found existing _distribute_clips. Replacing with improved version.")
    # Purane function ko dhundho aur replace karo (Regex se)
    # Function definition se lekar uske end tak capture karo
    pattern = r'(def _distribute_clips\([^)]*\):.*?)(?=\n\S|$)'
    # Naya function
    new_func = '''def _distribute_clips(clips, target_duration, voice_duration=None):
    """
    Clips ko exactly target_duration (voice length) ke hisaab se distribute karega.
    Agar clips ki total duration target se kam hai toh repeat karega, warna original return.
    """
    import subprocess, json, itertools
    from pathlib import Path

    def _get_duration(video_path):
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video_path)]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(json.loads(r.stdout)["format"]["duration"])
        except:
            # Fallback: agar duration nahi milti toh 5 sec assume karo
            return 5.0

    if not clips:
        return clips

    # Har clip ki duration nikaalo
    durations = []
    total_duration = 0.0
    for c in clips:
        d = _get_duration(c)
        durations.append(d)
        total_duration += d

    # Agar target_duration miss ho toh voice_duration use karo, warna target
    if target_duration is None and voice_duration is not None:
        target_duration = voice_duration
    if target_duration is None:
        target_duration = 0.0

    print(f"[ClipDist] Total clips duration: {total_duration:.2f}s | Target: {target_duration:.2f}s")

    # Agar total duration already target se zyada hai, toh original list return karo (no repeat)
    if total_duration >= target_duration:
        print("[ClipDist] Clips are sufficient. No repeat needed.")
        return clips

    # Repeat logic: target duration cover karne ke liye kitne repeats chahiye?
    if total_duration <= 0:
        repeats_needed = 2
    else:
        repeats_needed = int(target_duration // total_duration) + 2

    print(f"[ClipDist] Repeating clips {repeats_needed} times to cover target.")
    extended = list(itertools.islice(itertools.cycle(clips), len(clips) * repeats_needed))
    
    # Final list ka duration calculate karo (optional debug)
    final_duration = sum([_get_duration(c) for c in extended])
    print(f"[ClipDist] Final extended duration: {final_duration:.2f}s (Target: {target_duration:.2f}s)")
    
    return extended'''
    
    content = re.sub(pattern, new_func, content, flags=re.DOTALL)
    print("✅ Updated _distribute_clips function.")
else:
    print("ℹ️ _distribute_clips not found. Adding it to the file.")
    # File ke top mein (imports ke baad) function add karo
    new_func_def = '''
import subprocess, json, itertools
from pathlib import Path

def _distribute_clips(clips, target_duration, voice_duration=None):
    """
    Clips ko exactly target_duration (voice length) ke hisaab se distribute karega.
    Agar clips ki total duration target se kam hai toh repeat karega, warna original return.
    """
    def _get_duration(video_path):
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video_path)]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(json.loads(r.stdout)["format"]["duration"])
        except:
            return 5.0

    if not clips:
        return clips

    durations = []
    total_duration = 0.0
    for c in clips:
        d = _get_duration(c)
        durations.append(d)
        total_duration += d

    if target_duration is None and voice_duration is not None:
        target_duration = voice_duration
    if target_duration is None:
        target_duration = 0.0

    print(f"[ClipDist] Total clips duration: {total_duration:.2f}s | Target: {target_duration:.2f}s")

    if total_duration >= target_duration:
        print("[ClipDist] Clips are sufficient. No repeat needed.")
        return clips

    if total_duration <= 0:
        repeats_needed = 2
    else:
        repeats_needed = int(target_duration // total_duration) + 2

    print(f"[ClipDist] Repeating clips {repeats_needed} times.")
    extended = list(itertools.islice(itertools.cycle(clips), len(clips) * repeats_needed))
    return extended
'''
    # Insert after the last import line
    import_lines = re.finditer(r'^(import|from)\s+', content, re.MULTILINE)
    last_match = None
    for m in import_lines:
        last_match = m
    if last_match:
        insert_pos = last_match.end()
        insert_line = content[:insert_pos].rfind('\n') + 1
        content = content[:insert_line] + "\n" + new_func_def + "\n" + content[insert_line:]
    else:
        content = new_func_def + "\n" + content
    print("✅ Added _distribute_clips function to top of file.")

# 2. Ab usage line update karo: jahan `clip_list = _distribute_clips(clip_list, voice_duration)` call ho rahi hai
# Pehle wali line dhoondo (jo hamne pehle patch ki thi)
old_usage = r'clip_list = _distribute_clips\(clip_list, voice_duration\)'
new_usage = 'clip_list = _distribute_clips(clip_list, target_duration=voice_duration)'

# Agar vo line nahi mili toh check karo agar kuch aur hai
if re.search(old_usage, content):
    content = re.sub(old_usage, new_usage, content)
    print("✅ Updated usage of _distribute_clips to pass voice_duration correctly.")
else:
    # Ho sakta hai pehle se 'target_duration' use ho raha ho
    fallback_pattern = r'clip_list = _distribute_clips\([^)]+\)'
    matches = re.findall(fallback_pattern, content)
    if matches:
        # Replace last occurrence or all
        content = re.sub(fallback_pattern, 'clip_list = _distribute_clips(clip_list, target_duration=voice_duration)', content)
        print("✅ Force updated _distribute_clips call to use voice_duration.")

# 3. Voice duration calculate karne wala block add karein (safety)
# check karein ke voice duration pehle se calculate hai ya nahi
if "voice_duration" not in content or "_get_audio_duration" not in content:
    # Add a helper to get voice duration
    helper_func = '''
def _get_audio_duration(audio_path):
    import subprocess, json
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(audio_path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return float(json.loads(r.stdout)["format"]["duration"])
    except:
        return 30.0  # fallback
'''
    # Insert after imports (if not present)
    if "_get_audio_duration" not in content:
        content = content.replace("def _distribute_clips", helper_func + "\ndef _distribute_clips")
        print("✅ Added _get_audio_duration helper function.")

# 4. Ensure voice_duration is calculated before calling _distribute_clips
# We'll find where voice is chosen and add duration calculation
voice_duration_pattern = r'(voice=choose_voice\([^;]+;)'
if "voice_duration" not in content:
    content = re.sub(voice_duration_pattern, r'\1\nvoice_duration = _get_audio_duration(voice)', content)
    print("✅ Added voice_duration calculation line.")

# Write the file
file_path.write_text(content, encoding="utf-8")
print("\n🎉 All patches applied to safe_long_video_polished.py!")
print("▶️ Restart Streamlit and test your long video.")