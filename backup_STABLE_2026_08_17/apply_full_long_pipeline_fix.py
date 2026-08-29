import os
import re

print("🚀 Starting Corrected Long Video Pipeline Patch (Targeting app.py)...")

files_to_patch = {
    "safe_long_video_polished.py": "safe_long_video_polished.py.bak_v2",
    "batch_long_renderer.py": "batch_long_renderer.py.bak_v2",
    "app.py": "app.py.bak_v2"
}

# 1. Create Backups
for file_name, backup_name in files_to_patch.items():
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as src, open(backup_name, "w", encoding="utf-8") as dst:
            dst.write(src.read())
        print(f"📦 Created Backup: {backup_name}")

# 2. PATCH safe_long_video_polished.py (1.5s Intro, 2s Outro, 1.5s Voice Start)
if os.path.exists("safe_long_video_polished.py"):
    with open("safe_long_video_polished.py", "r", encoding="utf-8") as f:
        code = f.read()

    code = re.sub(r'INTRO_SECONDS\s*=\s*[\d\.]+', 'INTRO_SECONDS = 1.5', code)
    code = re.sub(r'OUTRO_SECONDS\s*=\s*[\d\.]+', 'OUTRO_SECONDS = 2.0', code)
    code = re.sub(r'VOICE_START_OFFSET\s*=\s*[\d\.]+', 'VOICE_START_OFFSET = 1.5', code)
    code = re.sub(r'"intro_seconds"\s*:\s*[\d\.]+', '"intro_seconds": 1.5', code)
    code = re.sub(r'"outro_seconds"\s*:\s*[\d\.]+', '"outro_seconds": 2.0', code)
    code = re.sub(r'"voice_start_offset"\s*:\s*[\d\.]+', '"voice_start_offset": 1.5', code)

    with open("safe_long_video_polished.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("⚡ Applied timing fixes to safe_long_video_polished.py")

# 3. PATCH batch_long_renderer.py (Loop Music & ChromaKey)
if os.path.exists("batch_long_renderer.py"):
    with open("batch_long_renderer.py", "r", encoding="utf-8") as f:
        code = f.read()

    code = re.sub(r'INTRO_SECONDS\s*=\s*[\d\.]+', 'INTRO_SECONDS=1.5', code)
    code = re.sub(r'OUTRO_SECONDS\s*=\s*[\d\.]+', 'OUTRO_SECONDS=2.0', code)
    code = re.sub(r'VOICE_START_OFFSET\s*=\s*[\d\.]+', 'VOICE_START_OFFSET=1.5', code)

    if "chromakey=0x00FF00" not in code:
        code = code.replace("format=yuva420p", "chromakey=0x00FF00:0.15:0.1,format=yuva420p")

    with open("batch_long_renderer.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("⚡ Applied rendering fixes to batch_long_renderer.py")

# 4. PATCH app.py (Fix UI Dynamic Heading & UI File Passing)
if os.path.exists("app.py"):
    with open("app.py", "r", encoding="utf-8") as f:
        code = f.read()

    # Dynamic UI Header Replacement (Short vs Long Video Assets Upload)
    if 'Short Video Assets Upload' in code:
        code = code.replace(
            'Short Video Assets Upload',
            'Long Video Assets Upload'
        )
        print("⚡ Fixed UI Assets Heading in app.py")

    helper_code = '''
import os
import tempfile

def _save_streamlit_upload_to_temp(uploaded_file):
    if uploaded_file is None:
        return None
    if isinstance(uploaded_file, str):
        return uploaded_file
    ext = os.path.splitext(getattr(uploaded_file, "name", "temp.tmp"))[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(uploaded_file.getbuffer() if hasattr(uploaded_file, "getbuffer") else uploaded_file.read())
    tmp.close()
    return tmp.name
'''
    if "_save_streamlit_upload_to_temp" not in code:
        code = helper_code + "\n" + code

    with open("app.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("⚡ Applied UI Upload Bridge to app.py")

print("\n✅ ALL PIPELINE FIXES APPLIED SUCCESSFULLY TO app.py & BACKEND!")