# ==========================================================
# voice_engine package init
# ==========================================================
# This file marks the voice_engine/ folder as a proper Python
# package, which is what allows the rest of the pipeline to
# import from it using the dotted path syntax:
#
#   from voice_engine.professional_voice_engine import humanize_voice_file
#
# Without this file existing (even completely empty), Python
# would not recognize voice_engine/ as an importable package
# at all, and that import line in master_pipeline.py and
# safe_long_video_polished.py would fail immediately.
#
# The try/except import guard already present in both
# pipeline files:
#
#   try:
#       from voice_engine.professional_voice_engine import humanize_voice_file
#       VOICE_ENGINE_AVAILABLE = True
#   except Exception as voice_import_error:
#       VOICE_ENGINE_AVAILABLE = False
#       humanize_voice_file = None
#
# ...means that even if something is wrong with this package
# (a missing __init__.py, a missing dependency, a syntax error
# in one of the four files), the pipeline will not crash — it
# will simply disable voice humanization for that render and
# continue using the original unmodified voice file. This
# __init__.py file existing and being valid Python (even just
# this comment block, with zero executable code) is what
# allows the import to succeed under normal conditions.
#
# This file deliberately does NOT re-export anything via
# wildcard imports or convenience shortcuts — every other file
# in this project that needs something from voice_engine
# imports it with an explicit, fully-qualified path, e.g.:
#
#   from voice_engine.professional_voice_engine import humanize_voice_file
#   from voice_engine.voice_settings_manager import resolve_voice_profile
#
# Keeping this file minimal avoids any risk of import-order
# issues or circular imports between the four files in this
# package.
# ==========================================================