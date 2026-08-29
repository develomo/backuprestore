from pathlib import Path
import re

p = Path(r"D:\My Creation Video Generator\backup\caption_engine.py")
text = p.read_text(encoding="utf-8")

# Remove smart quotes
text = text.replace('\u201c', '')
text = text.replace('\u201d', '')

# Fix the broken strip() line
text = re.sub(
    r'\.strip\(["\u201c\u201d.,!?;:\\\'\"\u2018\u2019]+\)',
    '.strip(".,!?;:\'\\\"")',
    text
)

p.write_text(text, encoding="utf-8")

try:
    compile(text, "caption_engine.py", "exec")
    print("CAPTION ENGINE SYNTAX OK")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")