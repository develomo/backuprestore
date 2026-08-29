# captions_engine.py
# ==========================================================
# MY CREATION VIDEO GENERATOR
# CAPTIONS ENGINE COMPATIBILITY WRAPPER v2.0
# ==========================================================
# Purpose:
# - Old import support:
#       from captions_engine import apply_captions
# - Real caption logic caption_engine.py mein rahe.
# - Duplicate caption systems avoid karna.
# - Old files ko crash hone se bachana.
# ==========================================================

try:
    from caption_engine import (
        apply_captions,
        generate_captions,
        add_captions,
        apply_word_by_word_captions,
        apply_story_flow_captions,
        render_style_preview,
        build_all_caption_previews,
        get_caption_ui_data,
        audit_caption_words,
        fix_words_for_captions,
    )
    CAPTION_ENGINE_AVAILABLE = True
except Exception as e:
    CAPTION_ENGINE_AVAILABLE = False
    print(f"[captions_engine.py] caption_engine import failed: {e}", flush=True)

    def apply_captions(video, words=None, *args, **kwargs):
        return video

    def generate_captions(video, words=None, *args, **kwargs):
        return video

    def add_captions(video, words=None, *args, **kwargs):
        return video

    def apply_word_by_word_captions(video, words=None, *args, **kwargs):
        return video

    def apply_story_flow_captions(video, words=None, *args, **kwargs):
        return video

    def render_style_preview(*args, **kwargs):
        return None

    def build_all_caption_previews(*args, **kwargs):
        return []

    def get_caption_ui_data():
        return {}

    def audit_caption_words(words):
        return {"total_words": len(words or []), "clean_words": 0, "quality": "unavailable"}

    def fix_words_for_captions(words, video_duration=None):
        return words or []


if __name__ == "__main__":
    print("Captions compatibility wrapper ready.")
    print("Caption engine available:", CAPTION_ENGINE_AVAILABLE)
