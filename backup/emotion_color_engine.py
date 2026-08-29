# emotion_color_engine.py
# ==========================================================
# MY CREATION VIDEO GENERATOR
# SAFE EMOTION COLOR ENGINE v2.0
# ==========================================================
# Purpose:
# - Spoken words/emotions ke hisaab se subtle visual mood hint dena.
# - Old apply_emotion_color(video, words) compatibility maintain karna.
# - Subclip + concatenate method avoid karna because it can create:
#     - tiny gaps
#     - sync drift
#     - render slowness
#     - visual glitches
# - Original AI clip quality preserve karna.
#
# Old issue:
# Old code har word ke liye video.subclip(w["start"], w["end"])
# bana kar concatenate karta tha. Agar words list incomplete ho,
# video timeline toot sakti thi.
#
# New approach:
# One continuous frame function applies very subtle emotion
# adjustment at keyword moments.
# ==========================================================

import re
import numpy as np


# ==========================================================
# EMOTION WORD MAP
# ==========================================================

EMOTION_WORDS = {
    "dark": {
        "words": {"fear", "war", "dark", "danger", "warning", "secret", "hidden", "death", "lost"},
        "brightness": -4,
        "saturation": 0.96,
        "cool": 0.012,
    },
    "success": {
        "words": {"success", "money", "rich", "wealth", "power", "win", "growth", "profit"},
        "brightness": 2,
        "saturation": 1.025,
        "warm": 0.012,
    },
    "calm": {
        "words": {"peace", "calm", "wisdom", "silence", "patience", "life", "truth"},
        "brightness": 1,
        "saturation": 0.985,
        "warm": 0.006,
    },
    "future": {
        "words": {"ai", "future", "technology", "robot", "digital", "system", "machine"},
        "brightness": 0,
        "saturation": 1.015,
        "cool": 0.010,
    },
}


# ==========================================================
# HELPERS
# ==========================================================

def safe_print(message):
    try:
        print(str(message).replace("→", "->").replace("—", "-"), flush=True)
    except Exception:
        pass


def _clean_word(word):
    text = str(word or "").lower()
    text = re.sub(r"[^a-z0-9']", "", text)
    return text.strip()


def _clip_duration(video):
    try:
        return max(float(video.duration), 0.1)
    except Exception:
        return 0.1


def _find_emotion_events(words):
    events = []

    for item in words or []:
        if not isinstance(item, dict):
            continue

        word = _clean_word(item.get("word", ""))

        if not word:
            continue

        for emotion, data in EMOTION_WORDS.items():
            if word in data["words"]:
                try:
                    start = float(item.get("start", 0))
                    end = float(item.get("end", start + 0.35))
                except Exception:
                    continue

                events.append({
                    "emotion": emotion,
                    "word": word,
                    "start": start,
                    "end": end,
                    "center": (start + end) / 2.0,
                })
                break

    return events


def _ease(t):
    t = max(0.0, min(1.0, float(t)))
    return t * t * (3.0 - 2.0 * t)


def _emotion_strength_at_time(t, events, window=0.45):
    best = None
    best_strength = 0.0

    for event in events:
        center = event["center"]
        dist = abs(t - center)

        if dist <= window:
            strength = 1.0 - (dist / window)
            strength = _ease(strength)

            if strength > best_strength:
                best_strength = strength
                best = event

    return best, best_strength


def _apply_emotion_frame(frame, emotion, strength):
    if not emotion or strength <= 0:
        return frame

    data = EMOTION_WORDS.get(emotion, {})
    arr = frame.astype(np.float32)

    brightness = float(data.get("brightness", 0)) * strength
    saturation = 1.0 + (float(data.get("saturation", 1.0)) - 1.0) * strength

    gray = arr.mean(axis=2, keepdims=True)
    arr = gray + (arr - gray) * saturation
    arr += brightness

    warm = float(data.get("warm", 0.0)) * strength
    cool = float(data.get("cool", 0.0)) * strength

    if warm:
        arr[:, :, 0] += warm * 255
        arr[:, :, 2] -= warm * 180

    if cool:
        arr[:, :, 2] += cool * 255
        arr[:, :, 0] -= cool * 150

    return np.clip(arr, 0, 255).astype(np.uint8)


# ==========================================================
# PUBLIC API
# ==========================================================

def apply_emotion_color(video, words, niche=None, render_plan=None):
    """
    Old-compatible function.

    Args:
        video: MoviePy VideoClip.
        words: Whisper word timestamp list.

    Returns:
        MoviePy VideoClip with subtle emotion color hints.
    """
    if video is None:
        return video

    events = _find_emotion_events(words)

    if not events:
        safe_print("[EmotionColor] No emotion keywords found. Skipping.")
        return video

    duration = _clip_duration(video)

    safe_print(f"[EmotionColor] Emotion events scheduled: {len(events)}")

    def process(get_frame, t):
        frame = get_frame(t)
        event, strength = _emotion_strength_at_time(t, events, window=0.45)

        if not event:
            return frame

        return _apply_emotion_frame(frame, event["emotion"], strength)

    try:
        return video.fl(process).set_duration(duration)
    except Exception as e:
        safe_print(f"[EmotionColor] Failed, returning original: {e}")
        return video


def get_emotion_events(words):
    return _find_emotion_events(words)


if __name__ == "__main__":
    print("Safe Emotion Color Engine ready.")
