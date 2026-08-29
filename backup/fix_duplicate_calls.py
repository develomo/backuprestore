import re

app_file = "app.py"

with open(app_file, "r", encoding="utf-8") as f:
    content = f.read()

# Remove duplicate function calls/sections causing StreamlitDuplicateElementId
# Replace lines calling captions_section() at line 558
content = re.sub(
    r"add_captions,\s*caption_mode,\s*style_id\s*=\s*captions_section\(\)",
    "# Auto-cleaned duplicate call\n    pass",
    content
)

with open(app_file, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Duplicate calls cleaned successfully!")