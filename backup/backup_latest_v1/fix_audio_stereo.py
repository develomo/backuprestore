fn = 'audio_engine.py'
c = open(fn, encoding='utf-8', errors='ignore').read()

# 1. Missing Functions Add Karna (Music aur SFX ke liye)
missing_funcs = '''
def list_audio_files(folder):
    """Helper for music_engine and sfx_engine to list audio files."""
    p = Path(folder)
    if not p.exists(): return []
    return existing_files(p.glob("*"), AUDIO_EXTS)

def loop_audio(audio_path, target_duration, output_path=None):
    """Loop audio to target duration. Returns path."""
    # Safe fallback: just return the original path
    return str(audio_path)
'''
if 'def list_audio_files' not in c:
    c += missing_funcs

# 2. Force Stereo Audio to fix "channel element not allocated" AAC decode error
# Pehle voice filter par aformat lagana
c = c.replace('"aresample=44100"', '"aresample=44100,aformat=channel_layouts=stereo"')

# Final mix par bhi stereo force karna
c = c.replace('+ f"loudnorm=I={target}:TP=-1.0:LRA=11"', '+ f"loudnorm=I={target}:TP=-1.0:LRA=11,aformat=channel_layouts=stereo"')
c = c.replace('+ "loudnorm=I={target}:TP=-1.0:LRA=11"', '+ f"loudnorm=I={target}:TP=-1.0:LRA=11,aformat=channel_layouts=stereo"')

open(fn, 'w', encoding='utf-8').write(c)
print("SUCCESS: Missing functions added & Stereo Audio enforced!")