from pathlib import Path

file_path = Path("safe_long_video_polished.py")
content = file_path.read_text(encoding="utf-8")

# Target line (exact pattern)
old_line_pattern = "clip_list=choose_clips(clips,kwargs,assets)"

if old_line_pattern not in content:
    print("❌ Line not found! Trying alternative spaces...")
    # Try with spaces
    import re
    pattern = r'clip_list\s*=\s*choose_clips\s*\([^;]+;'
    match = re.search(pattern, content)
    if not match:
        print("❌ Could not find clip_list=choose_clips line. Aborting.")
        exit(1)
    old_line = match.group(0)
else:
    old_line = old_line_pattern

print(f"🔍 Found line: {old_line[:50]}...")

# Naya block
new_block = """# ---- FIXED CLIP DISTRIBUTION ----
voice_duration = _get_audio_duration(voice)
clip_list = _distribute_clips(choose_clips(clips, kwargs, assets), target_duration=voice_duration)"""

# Replace
content = content.replace(old_line, new_block)

# Extra check: agar voice_duration already define hai toh duplicate na ho
if "voice_duration = _get_audio_duration(voice)" in content:
    # Check agar pehle se koi aur voice_duration define hai toh hatao (safety)
    pass

file_path.write_text(content, encoding="utf-8")
print("✅ Successfully injected clip distribution call!")
print("✅ Now _distribute_clips will be called with voice_duration.")