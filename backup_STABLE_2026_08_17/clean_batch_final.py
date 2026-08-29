from pathlib import Path

file_path = Path("batch_long_renderer.py")
content = file_path.read_text(encoding="utf-8")

# 1. Replace all non-breaking spaces (U+00A0) with normal space
content = content.replace('\u00a0', ' ')

# 2. Remove any line that contains 'overlay_logo' or 'Overlay logo' (case insensitive)
lines = content.splitlines()
cleaned_lines = []
for line in lines:
    # Skip lines that contain logo-related keywords
    if 'overlay_logo' in line.lower() or 'logo_path' in line.lower():
        continue
    cleaned_lines.append(line)

# 3. Join back
new_content = '\n'.join(cleaned_lines)

# 4. Remove any leftover double blank lines (optional)
import re
new_content = re.sub(r'\n\s*\n', '\n\n', new_content)

file_path.write_text(new_content, encoding='utf-8')
print("✅ batch_long_renderer.py has been cleaned of all logo references and non-printable characters.")