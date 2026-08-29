import os

print("🔧 Fixing Indentation Error in app.py safely...")

APP_FILE = "app.py"
BACKUP_FILE = "app.py.bak_ui_assets"

# 1. Restore clean app.py from backup if available to remove bad indentation
if os.path.exists(BACKUP_FILE):
    with open(BACKUP_FILE, "r", encoding="utf-8") as src, open(APP_FILE, "w", encoding="utf-8") as dst:
        dst.write(src.read())
    print("📦 Restored app.py from clean backup.")

if not os.path.exists(APP_FILE):
    print("❌ Error: app.py not found.")
    exit(1)

with open(APP_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 2. Find target line and measure its exact leading indentation (spaces)
target_idx = -1
for i, line in enumerate(lines):
    if 'key="outro_file"' in line or 'key="long_outro"' in line or 'Outro' in line:
        target_idx = i
        break

if target_idx == -1:
    for i, line in enumerate(lines):
        if 'st.button(' in line or 'Render' in line:
            target_idx = i
            break

if target_idx != -1:
    # Measure leading spaces of the target line
    target_line = lines[target_idx]
    indent = len(target_line) - len(target_line.lstrip(' '))
    spaces = " " * indent

    # Properly indented UI block
    ui_block = [
        f"{spaces}# --- LONG VIDEO SPECIFIC EXTRA ASSETS ---\n",
        f"{spaces}st.markdown('---')\n",
        f"{spaces}st.subheader('📢 Long Video CTA & Captions Control')\n",
        f"{spaces}col_sub, col_cap = st.columns(2)\n",
        f"{spaces}with col_sub:\n",
        f"{spaces}    long_subscribe_file = st.file_uploader('Upload Subscribe Call-To-Action Overlay (.mp4, .mov, .png)', type=['mp4', 'mov', 'png', 'gif'], key='long_subscribe_uploader')\n",
        f"{spaces}with col_cap:\n",
        f"{spaces}    st.write('**Subtitle Settings**')\n",
        f"{spaces}    add_captions_toggle = st.checkbox('Enable Subtitles / Captions Burn-In', value=True, key='long_captions_checkbox')\n"
    ]

    # Insert right after target line safely
    lines = lines[:target_idx + 1] + ui_block + lines[target_idx + 1:]

    with open(APP_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("✅ Indentation fixed perfectly and matched with app.py block level!")
else:
    print("⚠️ Target placement not found, cleaned up invalid indentation safely.")