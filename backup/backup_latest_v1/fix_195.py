fn = 'safe_long_video_polished.py'
lines = open(fn, encoding='utf-8', errors='ignore').readlines()
fixed = False

for i in range(len(lines)):
    stripped = lines[i].lstrip()
    # Line 195 aur 196 ko dhoond kar unhe exactly 4 spaces par set karna
    if stripped.startswith('voice_duration = _get_audio_duration') or stripped.startswith('clip_list = _distribute_clips'):
        if not lines[i].startswith('    ' + stripped):
            lines[i] = '    ' + stripped
            fixed = True
            
if fixed:
    open(fn, 'w', encoding='utf-8').writelines(lines)
    print("SUCCESS: Lines 195 & 196 fixed to exactly 4 spaces indentation!")
else:
    print("SKIP: Lines not found or already fixed.")