# fix_audio_mixer_final.py
# TARGETED FIX: Prevents empty filter strings (,,) in FFmpeg audio mixer
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET = BASE_DIR / "batch_long_renderer.py"

if not TARGET.exists():
    print("[ERROR] batch_long_renderer.py not found!")
    exit(1)

content = TARGET.read_text(encoding="utf-8")
changes_made = 0

# FIX 1: Music filter construction (Prevents empty music_tone from creating ',,')
old_music_filter = '''        filters.append(
            f"[{idx}:a]volume={music_volume},"
            f"{music_tone},"
            f"acompressor=threshold=-24dB:ratio=1.7:attack=30:release=250,"
            f"afade=t=in:st={intro_sec:.3f}:d=1.0,"
            f"afade=t=out:st={fade_out_start:.3f}:d=1.2,"
            f"adelay={intro_ms}|{intro_ms},"
            f"atrim=0:{trim_end},"
            "aresample=44100[m_pre]"
        )'''

new_music_filter = '''        music_filters = [f"[{idx}:a]volume={music_volume}"]
        if music_tone and music_tone.strip():
            music_filters.append(music_tone.strip())
        music_filters.extend([
            "acompressor=threshold=-24dB:ratio=1.7:attack=30:release=250",
            f"afade=t=in:st={intro_sec:.3f}:d=1.0",
            f"afade=t=out:st={fade_out_start:.3f}:d=1.2",
            f"adelay={intro_ms}|{intro_ms}",
            f"atrim=0:{trim_end}",
            "aresample=44100[m_pre]"
        ])
        filters.append(",".join(music_filters))'''

if old_music_filter in content:
    content = content.replace(old_music_filter, new_music_filter)
    print("[OK] Fix 1: Safeguarded music filter construction (prevents empty filter '')")
    changes_made += 1
else:
    print("[INFO] Fix 1: Music filter already safe or formatted differently")

# FIX 2: Final mix filter construction (Prevents empty loudnorm filter from creating ',,')
old_final_mix = '''    filters.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0.35,"
        + "acompressor=threshold=-18dB:ratio=2.0:attack=10:release=120,"
        + "alimiter=limit=0.97,"
        + f"{final_loudnorm_filter},"
        + "apad[aout]"
    )'''

new_final_mix = '''    final_mix_parts = []
    if len(labels) > 1:
        final_mix_parts.append("".join(labels) + f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0.35")
    else:
        final_mix_parts.append(labels[0])
    final_mix_parts.append("acompressor=threshold=-18dB:ratio=2.0:attack=10:release=120")
    final_mix_parts.append("alimiter=limit=0.97")
    if final_loudnorm_filter and final_loudnorm_filter.strip():
        final_mix_parts.append(final_loudnorm_filter.strip())
    final_mix_parts.append("apad[aout]")
    filters.append(",".join(final_mix_parts))'''

if old_final_mix in content:
    content = content.replace(old_final_mix, new_final_mix)
    print("[OK] Fix 2: Safeguarded final mix filter construction (prevents empty loudnorm filter '')")
    changes_made += 1
else:
    print("[INFO] Fix 2: Final mix filter already safe or formatted differently")

# FIX 3: Chapter sting filter (Fixes list appending bug that could cause malformed strings)
old_chapter = '''            hit_labels = []
            for i, ts in enumerate(interior_chapter_times):
                delay_ms = int(max(0.0, ts) * 1000)
                filters.append(f"[st_src{i}]adelay={delay_ms}|{delay_ms}[sth{i}]")
            hit_labels.append("".join(f"[sth{i}]" for i in range(n_hits)))
            filters.append("".join(hit_labels) + f"amix=inputs={n_hits}:duration=longest[chapters_mixed]")'''

new_chapter = '''            hit_labels = "".join(f"[sth{i}]" for i in range(n_hits))
            for i, ts in enumerate(interior_chapter_times):
                delay_ms = int(max(0.0, ts) * 1000)
                filters.append(f"[st_src{i}]adelay={delay_ms}|{delay_ms}[sth{i}]")
            filters.append(f"{hit_labels}amix=inputs={n_hits}:duration=longest[chapters_mixed]")'''

if old_chapter in content:
    content = content.replace(old_chapter, new_chapter)
    print("[OK] Fix 3: Corrected chapter sting filter construction")
    changes_made += 1
else:
    print("[INFO] Fix 3: Chapter sting filter already correct or not found")

# FIX 4: Ultimate Safety Net - Clean up any accidental double commas or semicolons right before FFmpeg execution
old_filter_join = '"-filter_complex", ";".join(filters),'
new_filter_join = '''"-filter_complex", 
        ";".join(f.replace(",,", ",").replace(";;", ";").strip(",;") for f in filters),'''

if old_filter_join in content:
    content = content.replace(old_filter_join, new_filter_join)
    print("[OK] Fix 4: Added ultimate safety net to clean filter strings (removes ,, and ;;)")
    changes_made += 1
else:
    print("[INFO] Fix 4: Filter join safety net already applied or formatted differently")

if changes_made > 0:
    TARGET.write_text(content, encoding="utf-8")
    print(f"\n✅ SUCCESS! {changes_made} critical audio mixer fixes applied.")
    print("💡 Ab FFmpeg 'No such filter: ''' error kabhi nahi aayega.")
else:
    print("\n⚠️ No changes were made. The file might already be patched or the exact code structure has changed.")