# fix_add_captions_error.py
from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET = BASE_DIR / "safe_long_video_polished.py"

if not TARGET.exists():
    print("[ERROR] safe_long_video_polished.py not found!")
    exit(1)

content = TARGET.read_text(encoding="utf-8")

# The buggy line has: add_captions=add_captions
# It should be: add_captions=True
content = content.replace("add_captions=add_captions", "add_captions=True")

TARGET.write_text(content, encoding="utf-8")
print("[OK] Fixed 'add_captions' NameError in safe_long_video_polished.py")