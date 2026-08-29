# fix_audio_mixer_robust.py
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET = BASE_DIR / "batch_long_renderer.py"

if not TARGET.exists():
    print("[ERROR] batch_long_renderer.py not found!")
    exit(1)

content = TARGET.read_text(encoding="utf-8")
changes = 0

# FIX 1: Safeguard music_tone from being empty
old_music_tone = 'music_tone = str(prof.get("music_tone", "highpass=f=60,lowpass=f=11500"))'
new_music_tone = '''music_tone = str(prof.get("music_tone", "highpass=f=60,lowpass=f=11500")).strip()
    if not music_tone:
        music_tone = "highpass=f=60,lowpass=f=11500"'''

if old_music_tone in content:
    content = content.replace(old_music_tone, new_music_tone)
    print("[OK] Fix 1: Safeguarded music_tone from being empty")
    changes += 1

# FIX 2: Safeguard final_loudnorm_filter and amix construction
old_final_append = '''filters.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0.35,"
        + "acompressor=threshold=-18dB:ratio=2.0:attack=10:release=120,"
        + "alimiter=limit=0.97,"
        + f"{final_loudnorm_filter},"
        + "apad[aout]"
    )'''

new_final_append = '''# Safeguard against empty filters causing "No such filter: ''"
    clean_loudnorm = str(final_loudnorm_filter).strip()
    if not clean_loudnorm:
        clean_loudnorm = f"loudnorm=I={target_lufs}:TP={TARGET_TP}:LRA={TARGET_LRA}"
    
    if len(labels) > 1:
        mix_part = "".join(labels) + f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0.35"
    else:
        mix_part = labels[0]
    
    filters.append(
        mix_part + ","
        + "acompressor=threshold=-18dB:ratio=2.0:attack=10:release=120,"
        + "alimiter=limit=0.97,"
        + f"{clean_loudnorm},"
        + "apad[aout]"
    )'''

if old_final_append in content:
    content = content.replace(old_final_append, new_final_append)
    print("[OK] Fix 2: Safeguarded final filter append from empty strings and single-input amix")
    changes += 1

# FIX 3: Fix the hit_labels indentation bug
old_hit_labels = '''    hit_labels = []
    for i, ts in enumerate(interior_chapter_times):
        delay_ms = int(max(0.0, ts) * 1000)
        filters.append(f"[st_src{i}]adelay={delay_ms}|{delay_ms}[sth{i}]")
    hit_labels.append(f"[sth{i}]")
    filters.append("".join(hit_labels) + f"amix=inputs={n_hits}:duration=longest[chapters_mixed]")'''

new_hit_labels = '''    hit_labels = []
    for i, ts in enumerate(interior_chapter_times):
        delay_ms = int(max(0.0, ts) * 1000)
        filters.append(f"[st_src{i}]adelay={delay_ms}|{delay_ms}[sth{i}]")
        hit_labels.append(f"[sth{i}]") # Moved inside the loop to capture all hits
    filters.append("".join(hit_labels) + f"amix=inputs={n_hits}:duration=longest[chapters_mixed]")'''

if old_hit_labels in content:
    content = content.replace(old_hit_labels, new_hit_labels)
    print("[OK] Fix 3: Fixed hit_labels indentation bug (moved append inside the loop)")
    changes += 1

if changes > 0:
    TARGET.write_text(content, encoding="utf-8")
    print(f"\n✅ SUCCESS! {changes} critical audio mixer fixes applied.")
    print("💡 This prevents the 'No such filter: ''' error by ensuring no empty strings are passed to FFmpeg.")
else:
    print("\n⚠️ No changes were made. The file might already be patched or the exact code structure has changed.")
    print("Please check batch_long_renderer.py manually around line 2891.")