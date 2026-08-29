"""
FIX 2/3: safe_long_video_polished.py — Fix SyntaxError on line 200
Line 200: `final=        # PATCH 1: Inject preset info into batch_long_renderer`
This has `final=` with no value, and then a comment. The PATCH injection was corrupted.
Surgical fix: Remove the corrupted comment and fix `final=` assignment.
"""
import os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'safe_long_video_polished.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# The corrupted line with comment
old = """    try:
        final=        # PATCH 1: Inject preset info into batch_long_renderer
        if PRESET_AVAILABLE_LONG and preset.get("_preset_obj"):"""

new = """    try:
        # PATCH 1: Inject preset info into batch_long_renderer
        if PRESET_AVAILABLE_LONG and preset.get("_preset_obj"):"""

if old in content:
    before = content
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ FIX 2 APPLIED: safe_long_video_polished.py — corrupted line fixed")
else:
    print("❌ FIX 2 SKIPPED: exact pattern not found. Trying loose match...")
    lines = content.split('\n')
    for i in range(197, 208):
        if i < len(lines):
            print(f"  L{i+1}: {lines[i]}")