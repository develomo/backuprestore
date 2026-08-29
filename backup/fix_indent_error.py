import os

app_file = "app.py"

if not os.path.exists(app_file):
    print("❌ app.py nahi mili.")
    exit()

with open(app_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    # Detect problem lines around 540-570
    if 540 <= i <= 570:
        if "# Auto-cleaned duplicate call" in line or "pass" in line.strip():
            continue
        # Fix orphaned st.divider() or leftover indented elements
        if "st.divider()" in line or "captions_section" in line:
            stripped = line.strip()
            # Match indent with the previous valid line
            prev_indent = ""
            for prev in reversed(new_lines):
                if prev.strip():
                    prev_indent = " " * (len(prev) - len(prev.lstrip()))
                    break
            new_lines.append(f"{prev_indent}{stripped}\n")
            continue

    new_lines.append(line)

with open(app_file, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("🚀 Indentation error successfully fixed!")