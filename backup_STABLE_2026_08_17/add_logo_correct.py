from pathlib import Path

file_path = Path("app.py")
content = file_path.read_text(encoding="utf-8")
lines = content.splitlines()

# Search for the assets dict closing part
# We need to insert after line containing "outro": outro,
insert_after_idx = -1
for i, line in enumerate(lines):
    if '"outro": outro,' in line and 'assets' not in line:  # specifically the outro line
        insert_after_idx = i
        break

if insert_after_idx == -1:
    print("❌ Could not find 'outro' line inside assets dict.")
else:
    # Check if logo already exists inside dict
    logo_exists = any('"logo": logo' in line for line in lines)
    if logo_exists:
        print("✅ Logo already present in assets dict. Nothing to do.")
    else:
        # Pehle check karein ke kya line 534 (outro ke baad) pehle se empty hai
        # Actually we want to insert right after outro line.
        # Indentation count from the 'outro' line
        indent_len = len(lines[insert_after_idx]) - len(lines[insert_after_idx].lstrip())
        indent = " " * indent_len
        
        # Insert new line
        lines.insert(insert_after_idx + 1, indent + '"logo": logo,')
        
        # Write back
        file_path.write_text("\n".join(lines), encoding="utf-8")
        print("✅ Logo correctly added inside assets dictionary.")
        print("   (It will appear right before the closing '}')")