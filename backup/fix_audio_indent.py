import re

fn = 'audio_engine.py'
c = open(fn, encoding='utf-8', errors='ignore').read()

# Top-level functions ko exactly 0 spacing par set karna
c = re.sub(r'^[ \t]+def build_integrated_audio_for_pipeline', 'def build_integrated_audio_for_pipeline', c, flags=re.MULTILINE)
c = re.sub(r'^[ \t]+def build_audio_mix', 'def build_audio_mix', c, flags=re.MULTILINE)
c = re.sub(r'^[ \t]+def mix_voice_music_sfx', 'def mix_voice_music_sfx', c, flags=re.MULTILINE)

open(fn, 'w', encoding='utf-8').write(c)
print("SUCCESS: audio_engine.py indentation fixed perfectly!")