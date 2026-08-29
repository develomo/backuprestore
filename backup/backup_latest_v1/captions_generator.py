# captions_generator.py
# ==========================================================
# MY CREATION VIDEO GENERATOR
# CAPTIONS GENERATOR v2.0
# ==========================================================
# Purpose:
# - Audio/voice file se transcript aur segments generate karna.
# - Old manual script behavior maintain karna.
# - whisper_engine.py ke advanced functions ko prefer karna.
# - Agar whisper_engine unavailable ho to openai-whisper direct use karna.
# - Captions ke liye clean word timestamps return karna.
#
# Important:
# Ye file captions render nahi karti.
# Rendering caption_engine.py karta hai.
# Ye file sirf transcript/timestamps generate karti hai.
# ==========================================================

from pathlib import Path
import json


BASE_DIR = Path(__file__).parent
DEFAULT_VOICE_PATH = BASE_DIR / "assets" / "shorts" / "voices" / "voice.mp3"
OUTPUT_DIR = BASE_DIR / "outputs" / "transcripts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================================
# IMPORT ADVANCED WHISPER ENGINE
# ==========================================================

try:
    from whisper_engine import get_word_timestamps, transcribe_audio
    ADVANCED_WHISPER_AVAILABLE = True
except Exception as e:
    print(f"[CaptionsGenerator] whisper_engine unavailable: {e}", flush=True)
    ADVANCED_WHISPER_AVAILABLE = False
    get_word_timestamps = None
    transcribe_audio = None


# ==========================================================
# FALLBACK OPENAI WHISPER
# ==========================================================

def _fallback_whisper_transcribe(audio_path, model_name="base", language=None):
    import whisper

    model = whisper.load_model(model_name)

    kwargs = {
        "word_timestamps": True,
        "fp16": False,
    }

    if language:
        kwargs["language"] = language

    result = model.transcribe(str(audio_path), **kwargs)
    return result


def _extract_words_from_result(result):
    words = []

    for seg in result.get("segments", []):
        seg_words = seg.get("words") or []

        if seg_words:
            for w in seg_words:
                word = str(w.get("word", "")).strip()
                if not word:
                    continue
                words.append({
                    "word": word,
                    "start": float(w.get("start", seg.get("start", 0))),
                    "end": float(w.get("end", seg.get("end", seg.get("start", 0) + 0.25))),
                })
        else:
            # Segment-level fallback.
            text_words = str(seg.get("text", "")).strip().split()
            start = float(seg.get("start", 0))
            end = float(seg.get("end", start + 0.5))
            dur = max(end - start, 0.1)

            if text_words:
                step = dur / len(text_words)
                for i, word in enumerate(text_words):
                    words.append({
                        "word": word,
                        "start": start + i * step,
                        "end": start + (i + 1) * step,
                    })

    return words


# ==========================================================
# PUBLIC API
# ==========================================================

def generate_caption_words(audio_path, model_name="base", language=None):
    """
    Returns word timestamps for caption_engine.py.

    Args:
        audio_path: voice/audio path.
        model_name: whisper model.
        language: optional language code.

    Returns:
        list of dicts:
            {"word": "...", "start": 0.0, "end": 0.4}
    """
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if ADVANCED_WHISPER_AVAILABLE and get_word_timestamps is not None:
        try:
            return get_word_timestamps(str(audio_path), model_name=model_name, language=language)
        except TypeError:
            # Old whisper_engine may not accept keyword args.
            return get_word_timestamps(str(audio_path))
        except Exception as e:
            print(f"[CaptionsGenerator] Advanced whisper failed, fallback used: {e}", flush=True)

    result = _fallback_whisper_transcribe(audio_path, model_name=model_name, language=language)
    return _extract_words_from_result(result)


def generate_transcript(audio_path, model_name="base", language=None):
    """
    Returns full transcript result.
    """
    audio_path = Path(audio_path)

    if ADVANCED_WHISPER_AVAILABLE and transcribe_audio is not None:
        try:
            return transcribe_audio(str(audio_path), model_name=model_name, language=language)
        except TypeError:
            return transcribe_audio(str(audio_path))
        except Exception:
            pass

    return _fallback_whisper_transcribe(audio_path, model_name=model_name, language=language)


def save_caption_words(audio_path, output_json=None, model_name="base", language=None):
    words = generate_caption_words(audio_path, model_name=model_name, language=language)

    if output_json is None:
        audio_path = Path(audio_path)
        output_json = OUTPUT_DIR / f"{audio_path.stem}_words.json"
    else:
        output_json = Path(output_json)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(words, indent=2, ensure_ascii=False), encoding="utf-8")

    return str(output_json)


# ==========================================================
# OLD SCRIPT BEHAVIOR
# ==========================================================

def print_segments(audio_path=DEFAULT_VOICE_PATH, model_name="base", language=None):
    result = generate_transcript(audio_path, model_name=model_name, language=language)

    for seg in result.get("segments", []):
        print(seg.get("start"), "->", seg.get("end"), ":", seg.get("text"))

    return result


if __name__ == "__main__":
    if DEFAULT_VOICE_PATH.exists():
        print_segments(DEFAULT_VOICE_PATH)
    else:
        print("Default voice not found:", DEFAULT_VOICE_PATH)
