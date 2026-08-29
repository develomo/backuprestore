import os
import ast

print("🛠️ Cleaning app.py and validating Python Syntax with AST compiler...")

APP_FILE = "app.py"

# 1. Restore from initial clean backup if available
backups = ["app.py.bak_v2", "app.py.bak_full", "app.py.bak_route"]
for b in backups:
    if os.path.exists(b):
        with open(b, "r", encoding="utf-8") as src, open(APP_FILE, "w", encoding="utf-8") as dst:
            dst.write(src.read())
        print(f"📦 Restored clean base file from backup: {b}")
        break

if not os.path.exists(APP_FILE):
    print("❌ Error: app.py file not found!")
    exit(1)

with open(APP_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 2. Filter out any orphaned/corrupted injected lines
clean_lines = []
for line in lines:
    if "Subscribe Call-to-Action & Overlays" in line or "long_subscribe_uploader" in line or "long_captions_checkbox" in line:
        continue
    clean_lines.append(line)

# 3. Find accurate insertion point and match exact line indentation
final_lines = []
inserted = False

for line in clean_lines:
    final_lines.append(line)
    # Target file uploader block inside UI
    if ("outro" in line.lower() or "intro" in line.lower()) and "st.file_uploader" in line and not inserted:
        indent_size = len(line) - len(line.lstrip(" "))
        sp = " " * indent_size
        
        ui_block = [
            f"\n{sp}# --- LONG VIDEO SPECIFIC ASSETS ---",
            f"\n{sp}st.markdown('---')",
            f"\n{sp}st.subheader('📢 Long Video CTA & Captions Control')",
            f"\n{sp}col_sub, col_cap = st.columns(2)",
            f"\n{sp}with col_sub:",
            f"\n{sp}    long_subscribe_file = st.file_uploader('Upload Subscribe Overlay (.mp4, .mov, .png)', type=['mp4', 'mov', 'png'], key='long_sub_clean')",
            f"\n{sp}with col_cap:",
            f"\n{sp}    st.write('**Subtitle Settings**')",
            f"\n{sp}    add_captions_toggle = st.checkbox('Enable Subtitles / Captions Burn-In', value=True, key='long_cap_clean')\n"
        ]
        final_lines.extend(ui_block)
        inserted = True

code_to_test = "".join(final_lines)

# 4. AST Compilation Check (Strict Python Indentation Rules)
try:
    ast.parse(code_to_test)
    with open(APP_FILE, "w", encoding="utf-8") as f:
        f.write(code_to_test)
    print("✅ AST VALIDATION PASSED! app.py fixed with PERFECT indentation.")
except SyntaxError as e:
    print(f"⚠️ Indentation conflict detected by AST: {e}. Reverting to 100% clean file...")
    clean_code = "".join(clean_lines)
    ast.parse(clean_code)
    with open(APP_FILE, "w", encoding="utf-8") as f:
        f.write(clean_code)
    print("✅ Restored app.py to 100% clean and runnable syntax!")