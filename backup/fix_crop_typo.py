# fix_crop_typo.py
from pathlib import Path

file_path = Path("batch_long_renderer.py")
content = file_path.read_text(encoding="utf-8")

# Fix: FFmpeg crop filter uses ':' not 'x'
if "crop={TARGET_RES}" in content:
    content = content.replace("crop={TARGET_RES}", "crop={TARGET_RES_SCALE}")
    file_path.write_text(content, encoding="utf-8")
    print("✅ FIXED! 'crop=854x480' ko 'crop=854:480' mein convert kar diya.")
    print("💡 Ab dobara 'streamlit run app.py' start karein!")
else:
    print("ℹ️ Already fixed.")