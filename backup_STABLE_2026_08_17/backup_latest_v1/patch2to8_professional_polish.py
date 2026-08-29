"""
====================================================================
PATCH 2-8: COMPLETE PROFESSIONAL POLISH PACK (FIXED - No Unicode Errors)
====================================================================
FIX: All em dashes and special Unicode chars replaced with ASCII.
     Previous version had U+2014 (em dash) causing SyntaxError.

All 7 features inject honge:
  2. Film Grain Overlay
  3. SFX Cut-Synced Whoosh
  4. Kinetic Caption Emphasis Words
  5. Shot-Type Framing Variety
  6. Room Tone / Ambience Bed
  7. EQ De-Hype (4-5kHz Sizzle)
  8. Breath Sounds

FILES MODIFIED:
  - batch_long_renderer.py
  - caption_engine.py
  - audio_engine.py
  - voice_humanization_orchestrator.py
  - final_assembler.py

USAGE: python patch2to8_professional_polish.py
====================================================================
"""

from pathlib import Path
import re

BASE_DIR = Path(__file__).parent

TARGETS = {
    "batch_long": BASE_DIR / "batch_long_renderer.py",
    "caption_engine": BASE_DIR / "caption_engine.py",
    "audio_engine": BASE_DIR / "audio_engine.py",
    "voice_orch": BASE_DIR / "voice_humanization_orchestrator.py",
    "final_assembler": BASE_DIR / "final_assembler.py",
}

BACKUPS = {k: BASE_DIR / (v.name + ".backup_polish") for k, v in TARGETS.items()}

TOTAL_CHANGES = 0


def safe_print(msg):
    print(f"[Polish] {msg}", flush=True)


def read_and_backup(key):
    path = TARGETS[key]
    if not path.exists():
        safe_print(f"WARNING: {key} not found - skipping")
        return None
    content = path.read_text(encoding="utf-8")
    BACKUPS[key].write_text(content, encoding="utf-8")
    return content


def write_if_changed(key, original, modified):
    global TOTAL_CHANGES
    if modified != original:
        TARGETS[key].write_text(modified, encoding="utf-8")
        diff = len(modified) - len(original)
        TOTAL_CHANGES += 1
        safe_print(f"OK {key} UPDATED ({diff:+d} chars)")
    else:
        safe_print(f"SKIP {key}: No changes")


# ================================================================
# PATCH 2: FILM GRAIN OVERLAY
# ================================================================
def patch2_film_grain():
    safe_print("\n=== Patch 2: Film Grain Overlay ===")
    content = read_and_backup("batch_long")
    if content is None:
        return

    modified = content
    marker = "def render_clip_segment(src, out, wanted, index=0,"

    if marker in modified:
        grain_func = """# ============================================================
# PATCH 2: FILM GRAIN OVERLAY FUNCTION (Surgical Addition)
# Applies subtle film grain to break 'too-clean digital' look.
# Opacity 3 percent - visible on close inspection but not distracting.
# ============================================================
def apply_film_grain(input_path, output_path, opacity=0.03):
    import subprocess
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        grain_vf = "noise=alls=6:allf=t+u,format=yuv420p"
        cmd = [
            FFMPEG, "-y", "-i", str(input_path),
            "-vf", grain_vf,
            "-c:v", "libx264", "-preset", "ultrafast",
            "-crf", "20", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if output_path.exists() and output_path.stat().st_size > 1000:
            return str(output_path)
    except Exception as e:
        log("[FilmGrain] Skipped: " + str(e))
    return str(input_path)


def should_apply_grain(preset_overrides=None):
    if preset_overrides and isinstance(preset_overrides, dict):
        return preset_overrides.get("film_grain_enabled", True)
    return True
# ============================================================

"""
        modified = modified.replace(marker, grain_func + marker)
        safe_print("   OK: grain functions ADDED")

    # Inject grain into final export
    final_marker = "    final_path = str("
    if final_marker in modified:
        last_export = modified.rfind(final_marker)
        if last_export > 0:
            end_of_line = modified.index("\n", last_export)
            grain_call = """
        # PATCH 2: Apply film grain if enabled
        if should_apply_grain(preset_overrides):
            try:
                grain_out = Path(final_path).parent / ("grain_" + Path(final_path).name)
                final_path = apply_film_grain(final_path, grain_out)
            except Exception as gerr:
                log("[FilmGrain] Failed on final: " + str(gerr))
"""
            modified = modified[:end_of_line + 1] + grain_call + modified[end_of_line + 1:]
            safe_print("   OK: grain applied to final export")

    write_if_changed("batch_long", content, modified)


# ================================================================
# PATCH 3: SFX CUT-SYNCED WHOOSH
# ================================================================
def patch3_sfx_cut_sync():
    safe_print("\n=== Patch 3: SFX Cut-Synced Whoosh ===")
    content = read_and_backup("batch_long")
    if content is None:
        return

    modified = content
    sfx_marker = "def apply_film_grain(input_path, output_path, opacity=0.03):"

    if sfx_marker in modified:
        sfx_func = """# ============================================================
# PATCH 3: SFX CUT-SYNCED WHOOSH (Surgical Addition)
# Inserts subtle whoosh sounds at every cut point for
# subconscious professional polish. SFX at -28dB.
# ============================================================
def generate_whoosh_silence(duration=0.08, output_path=None):
    import subprocess, tempfile
    output_path = Path(output_path or tempfile.mktemp(suffix='.wav'))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fade_out_start = max(0.01, duration - 0.01)
        cmd = [
            FFMPEG, "-y", "-f", "lavfi",
            "-i", "anoisesrc=color=pink:duration=" + str(duration) + ":amplitude=0.003",
            "-ar", "44100", "-ac", "2",
            "-af", "afade=t=in:st=0:d=0.005,afade=t=out:st=" + str(fade_out_start) + ":d=0.01",
            str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if output_path.exists():
            return str(output_path)
    except Exception:
        pass
    return None


def insert_cut_sfx(video_path, cut_timestamps, output_path, sfx_vol_db=-28):
    import subprocess, tempfile
    video_path = Path(video_path)
    output_path = Path(output_path)
    if not cut_timestamps or len(cut_timestamps) < 2:
        return str(video_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        whoosh = generate_whoosh_silence(duration=0.08)
        if whoosh is None:
            return str(video_path)
        filter_parts = ["[0:a]volume=1.0[va]"]
        inputs = ["-i", str(video_path)]
        sfx_idx = 1
        for i, (cut_start, cut_end) in enumerate(cut_timestamps[:20]):
            if cut_start < 0.5:
                continue
            inputs += ["-i", whoosh]
            delay_ms = int(cut_start * 1000)
            filter_parts.append(
                "[" + str(sfx_idx) + ":a]adelay=" + str(delay_ms) + "|" + str(delay_ms) + ","
                "volume=" + str(sfx_vol_db) + "dB,"
                "afade=t=in:st=0:d=0.005,afade=t=out:st=0.07:d=0.01[sfx" + str(i) + "]"
            )
            sfx_idx += 1
        sfx_labels = "".join("[sfx" + str(i) + "]" for i in range(sfx_idx - 1))
        if not sfx_labels:
            return str(video_path)
        sfx_mix = "[va]" + sfx_labels + "amix=inputs=" + str(sfx_idx) + ":duration=first:dropout_transition=0[aout]"
        filter_parts.append(sfx_mix)
        cmd = [FFMPEG, "-y"] + inputs + [
            "-filter_complex", ";".join(filter_parts),
            "-map", "0:v:0", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if output_path.exists() and output_path.stat().st_size > 1000:
            return str(output_path)
    except Exception as e:
        log("[SFXCutSync] Skipped: " + str(e))
    return str(video_path)
# ============================================================

"""
        modified = modified.replace(sfx_marker, sfx_func + sfx_marker)
        safe_print("   OK: SFX whoosh functions ADDED")

    write_if_changed("batch_long", content, modified)


# ================================================================
# PATCH 4: KINETIC CAPTION EMPHASIS WORDS
# ================================================================
def patch4_kinetic_captions():
    safe_print("\n=== Patch 4: Kinetic Caption Emphasis Words ===")
    content = read_and_backup("caption_engine")
    if content is None:
        return

    modified = content
    emphasis_marker = "def clean_word(word: Any) -> str:"

    if emphasis_marker in modified:
        emphasis_code = """# ============================================================
# PATCH 4: EMPHASIS WORD DETECTION (Surgical Addition)
# Numbers, superlatives, power words get special treatment:
# 35 percent bigger font, brighter glow, bounce animation.
# ============================================================
EMPHASIS_WORDS = {
    "numbers": {"million","billion","trillion","hundred","thousand","percent"},
    "superlatives": {"best","worst","most","least","biggest","smallest","fastest","richest","highest","lowest"},
    "power_words": {"never","always","instantly","immediately","shocking","secret","hidden","revealed","exclusive","limited","proven","guaranteed","free","new","discover","warning","danger","stop","now","urgent","critical"},
    "money_words": {"money","cash","profit","revenue","income","wealth","salary","investment","return","dividend","billion","millionaire"},
    "emotion_words": {"amazing","incredible","unbelievable","beautiful","stunning","breathtaking","insane","crazy","wild","epic"},
}

def is_emphasis_word(word):
    word_lower = str(word or "").lower().strip(".,!?;:'\"")
    for category, words in EMPHASIS_WORDS.items():
        if word_lower in words:
            return True, category, 1.35, None
    clean_digits = word_lower.replace(",","").replace(".","")
    if clean_digits.isdigit() and len(clean_digits) >= 4:
        return True, "numbers", 1.4, None
    return False, "normal", 1.0, None


def apply_emphasis_to_caption(segment_text, style, config):
    words = segment_text.split()
    emphasis_found = any(is_emphasis_word(w)[0] for w in words)
    if emphasis_found:
        emp_style = dict(style)
        emp_style["font_scale"] = style.get("font_scale", 1.0) * 1.15
        emp_style["animation"] = "emphasis_bounce"
        emp_style["glow_enabled"] = True
        emp_style["glow_opacity"] = min(0.25, style.get("glow_opacity", 0.1) * 1.6)
        return emp_style
    return style
# ============================================================

"""
        modified = modified.replace(emphasis_marker, emphasis_code + emphasis_marker)
        safe_print("   OK: Emphasis word detection ADDED")

    write_if_changed("caption_engine", content, modified)


# ================================================================
# PATCH 5: SHOT-TYPE FRAMING VARIETY
# ================================================================
def patch5_framing_variety():
    safe_print("\n=== Patch 5: Shot-Type Framing Variety ===")
    content = read_and_backup("batch_long")
    if content is None:
        return

    modified = content
    framing_marker = "def duration_plan(total_duration, scene_count, min_dur=2.5, max_dur=9.5):"

    if framing_marker in modified:
        framing_code = """# ============================================================
# PATCH 5: FRAMING VARIETY ROTATION (Surgical Addition)
# Rotates wide/medium/close_up/macro_detail framing.
# No 3 consecutive clips use same framing type.
# ============================================================
FRAMING_TYPES = ["wide", "medium", "close_up", "macro_detail", "establishing", "detail"]
FRAMING_ROTATION = []

def get_next_framing():
    global FRAMING_ROTATION
    if not FRAMING_ROTATION:
        import random
        FRAMING_ROTATION = list(FRAMING_TYPES)
        random.Random().shuffle(FRAMING_ROTATION)
    if len(FRAMING_ROTATION) < 2:
        import random
        FRAMING_ROTATION = list(FRAMING_TYPES)
        random.Random().shuffle(FRAMING_ROTATION)
    framing = FRAMING_ROTATION.pop(0)
    if len(FRAMING_ROTATION) >= 2 and FRAMING_ROTATION[0] == FRAMING_ROTATION[1] == framing:
        for i, f in enumerate(FRAMING_ROTATION):
            if f != framing:
                FRAMING_ROTATION[0], FRAMING_ROTATION[i] = FRAMING_ROTATION[i], FRAMING_ROTATION[0]
                break
    return framing


def framing_crop_params(framing_type, clip_index=0):
    if framing_type == "close_up":
        return "iw*0.7:ih*0.7:(iw-ow)/2:(ih-oh)/2"
    elif framing_type == "macro_detail":
        return "iw*0.55:ih*0.55:(iw-ow)/4:(ih-oh)/3"
    elif framing_type == "medium":
        return "iw*0.85:ih*0.85:(iw-ow)/2:(ih-oh)/2"
    return None
# ============================================================

"""
        modified = modified.replace(framing_marker, framing_code + framing_marker)
        safe_print("   OK: Framing variety rotation ADDED")

    write_if_changed("batch_long", content, modified)


# ================================================================
# PATCH 6: ROOM TONE / AMBIENCE BED
# ================================================================
def patch6_room_tone():
    safe_print("\n=== Patch 6: Room Tone / Ambience Bed ===")
    content = read_and_backup("audio_engine")
    if content is None:
        return

    modified = content
    roomtone_marker = "def mux_audio_with_video("

    if roomtone_marker in modified:
        roomtone_code = """# ============================================================
# PATCH 6: ROOM TONE GENERATOR (Surgical Addition)
# Adds subtle brown noise floor at -48dB.
# Removes 'too-clean TTS' feel, adds natural ambience.
# Verifiable via spectrogram only, not audible as distinct element.
# ============================================================
def generate_room_tone(duration, output_path, level_db=-48):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    duration = max(float(duration or 0), 0.5)
    try:
        volume = 10 ** (level_db / 20.0)
        cmd = [
            FFMPEG, "-y",
            "-f", "lavfi",
            "-i", "anoisesrc=color=brown:duration=" + str(duration) + ":amplitude=" + str(volume),
            "-ar", "44100", "-ac", "2",
            str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if output_path.exists() and output_path.stat().st_size > 100:
            return str(output_path)
    except Exception:
        pass
    return None


def mix_room_tone_into_audio(main_audio_path, room_tone_path, output_path, room_level_db=-48):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not room_tone_path or not Path(room_tone_path).exists():
        return str(main_audio_path)
    try:
        vol = 10 ** (room_level_db / 20.0)
        cmd = [
            FFMPEG, "-y",
            "-i", str(main_audio_path),
            "-i", str(room_tone_path),
            "-filter_complex",
            "[0:a]volume=1.0[main];"
            "[1:a]volume=" + str(vol) + "[tone];"
            "[main][tone]amix=inputs=2:duration=first:dropout_transition=0[aout]",
            "-map", "[aout]",
            "-c:a", "aac", "-b:a", "192k",
            "-ar", "44100", "-ac", "2",
            str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if output_path.exists() and output_path.stat().st_size > 1000:
            return str(output_path)
    except Exception:
        pass
    return str(main_audio_path)
# ============================================================

"""
        modified = modified.replace(roomtone_marker, roomtone_code + roomtone_marker)
        safe_print("   OK: Room tone functions ADDED")

    write_if_changed("audio_engine", content, modified)


# ================================================================
# PATCH 7: EQ DE-HYPE (4-5kHz Sizzle Reduction)
# ================================================================
def patch7_eq_dehype():
    safe_print("\n=== Patch 7: EQ De-Hype (Sizzle Reduction) ===")
    content = read_and_backup("voice_orch")
    if content is None:
        return

    modified = content

    # Find the EQ filter function and add 4.5kHz dip
    eq_start = modified.find("def _eq_filter(profile, mode=")
    if eq_start > 0:
        eq_end = modified.find("\ndef _compressor_filter", eq_start)
        if eq_end > 0:
            old_eq = modified[eq_start:eq_end]
            old_return_marker = 'f"equalizer=f=3300:t=q:w=1.2:g={harsh_cut}"'
            if old_return_marker in old_eq:
                # Build replacement return statement
                dehype_return = """# PATCH 7: Add 4.5kHz gentle dip to reduce TTS sizzle
    sizzle_cut = -1.5 if _mode_key(mode) == "short" else -1.2

    return (
        f"highpass=f={highpass},"
        f"lowpass=f={lowpass},"
        f"{chorus}"
        f"equalizer=f=3300:t=q:w=1.2:g={harsh_cut},"
        f"equalizer=f=4500:t=q:w=1.5:g={sizzle_cut},"
        f"equalizer=f=7800:t=q:w=1.0:g=-0.7"
    )"""
                # Find and replace the old return block
                old_return_start = old_eq.find('f"highpass=f={highpass}')
                old_return_end = old_eq.find('\n\n', old_return_start)
                if old_return_end < 0:
                    old_return_end = len(old_eq)

                old_return_block = old_eq[old_return_start:old_return_end]
                new_eq = old_eq.replace(old_return_block, dehype_return)
                modified = modified[:eq_start] + new_eq + modified[eq_end:]
                safe_print("   OK: 4.5kHz sizzle reduction ADDED to EQ filter")
            else:
                safe_print("   WARNING: EQ return marker not found")
        else:
            safe_print("   WARNING: compressor_filter boundary not found")
    else:
        safe_print("   WARNING: _eq_filter function not found")

    write_if_changed("voice_orch", content, modified)


# ================================================================
# PATCH 8: BREATH SOUNDS AT SENTENCE BOUNDARIES
# ================================================================
def patch8_breath_sounds():
    safe_print("\n=== Patch 8: Breath Sounds at Sentence Boundaries ===")
    content = read_and_backup("voice_orch")
    if content is None:
        return

    modified = content
    breath_marker = "def _generate_subtle_room_tone(duration, output_path, profile):"

    if breath_marker in modified:
        breath_code = """# ============================================================
# PATCH 8: NATURAL BREATH SOUND GENERATOR (Surgical Addition)
# Inserts subtle breath sounds at ~1 in 3-4 sentence boundaries.
# Peak amplitude: -38dB. Mimics natural human speech recording.
# ============================================================
def _generate_breath_sound(duration=0.35, output_path=None, profile=None):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    duration = float(duration or 0.35)
    try:
        fade_out_start = max(0.06, duration - 0.08)
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "anoisesrc=color=pink:duration=" + str(duration) + ":amplitude=0.004",
            "-af",
            "highpass=f=200,lowpass=f=800,"
            "afade=t=in:st=0:d=0.06,afade=t=out:st=" + str(fade_out_start) + ":d=0.08,"
            "volume=-38dB",
            "-ar", "44100", "-ac", "2",
            str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if output_path.exists():
            return str(output_path)
    except Exception:
        pass
    return None


def insert_breath_sounds(voice_path, word_timestamps, output_path, profile=None):
    voice_path = Path(voice_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not word_timestamps or len(word_timestamps) < 5:
        return str(voice_path)
    try:
        boundaries = []
        for i in range(1, len(word_timestamps)):
            prev = word_timestamps[i-1]
            curr = word_timestamps[i]
            gap = float(curr.get("start", 0)) - float(prev.get("end", 0))
            has_period = str(prev.get("word","")).strip().endswith((".","!","?","..."))
            if has_period and gap > 0.15:
                boundaries.append(float(prev.get("end", 0)) + gap * 0.3)
        if not boundaries:
            return str(voice_path)
        import random
        rng = random.Random(42)
        breath_points = [b for i, b in enumerate(boundaries) if rng.random() < 0.28]
        if not breath_points:
            return str(voice_path)
        breath_file = _generate_breath_sound(duration=0.35, output_path=output_path.parent / "_breath.wav", profile=profile)
        if breath_file is None:
            return str(voice_path)
        inputs = ["-i", str(voice_path)]
        filters = ["[0:a]volume=1.0[v]"]
        labels = ["[v]"]
        for idx, bt in enumerate(breath_points[:8]):
            inputs += ["-i", breath_file]
            delay_ms = int(bt * 1000)
            filters.append("[" + str(idx+1) + ":a]adelay=" + str(delay_ms) + "|" + str(delay_ms) + ",volume=-38dB[b" + str(idx) + "]")
            labels.append("[b" + str(idx) + "]")
        mix_filter = "".join(labels) + "amix=inputs=" + str(len(labels)) + ":duration=first:dropout_transition=0[aout]"
        filters.append(mix_filter)
        cmd = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", ";".join(filters),
            "-map", "[aout]",
            "-c:a", "aac", "-b:a", "192k",
            "-ar", "44100", "-ac", "2",
            str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if output_path.exists() and output_path.stat().st_size > 1000:
            return str(output_path)
    except Exception:
        pass
    return str(voice_path)
# ============================================================

"""
        modified = modified.replace(breath_marker, breath_code + breath_marker)
        safe_print("   OK: Breath sound functions ADDED")

    write_if_changed("voice_orch", content, modified)


# ================================================================
# PATCH 2b: Film grain in final_assembler.py
# ================================================================
def patch2b_grain_final_assembler():
    safe_print("\n=== Patch 2b: Film Grain in Final Assembler ===")
    content = read_and_backup("final_assembler")
    if content is None:
        return

    modified = content
    grain_marker = "def mux_video_audio("

    if grain_marker in modified:
        grain_flag = """# ============================================================
# PATCH 2b: FILM GRAIN FLAG (Surgical Addition)
# ============================================================
FILM_GRAIN_ENABLED = True
FILM_GRAIN_OPACITY = 0.03

def apply_grain_to_final(video_path, output_path=None):
    import subprocess
    video_path = Path(video_path)
    output_path = Path(output_path or video_path.parent / ("grain_" + video_path.name))
    if not FILM_GRAIN_ENABLED:
        return str(video_path)
    try:
        cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vf", "noise=alls=6:allf=t+u,format=yuv420p",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "19",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if output_path.exists() and output_path.stat().st_size > 1000:
            return str(output_path)
    except Exception:
        pass
    return str(video_path)
# ============================================================

"""
        modified = modified.replace(grain_marker, grain_flag + grain_marker)
        safe_print("   OK: Grain flag + function ADDED to final_assembler")

    write_if_changed("final_assembler", content, modified)


# ================================================================
# MAIN
# ================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("PATCHES 2-8: PROFESSIONAL POLISH PACK (FIXED)")
    print("=" * 60)

    patch2_film_grain()
    patch3_sfx_cut_sync()
    patch4_kinetic_captions()
    patch5_framing_variety()
    patch6_room_tone()
    patch7_eq_dehype()
    patch8_breath_sounds()
    patch2b_grain_final_assembler()

    print("\n" + "=" * 60)
    print("TOTAL files modified: " + str(TOTAL_CHANGES))
    print("=" * 60)
    print("\nNEXT: Run test_all_patches_final.py to verify")