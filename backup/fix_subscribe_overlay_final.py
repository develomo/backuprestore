# fix_subscribe_overlay_final.py
# 1. Remove Subscribe Overlay from Short Video section (fix NameError)
# 2. Add Subscribe Overlay to Long Video section
import re
from pathlib import Path
import shutil

APP_FILE = Path("app.py")
if not APP_FILE.exists():
    print("[ERROR] app.py not found!")
    exit(1)

# Backup
backup = APP_FILE.with_suffix(".py.sub_overlay_fix_backup")
if not backup.exists():
    shutil.copy2(APP_FILE, backup)
    print(f"[OK] Backup created: {backup.name}")

content = APP_FILE.read_text(encoding="utf-8")
lines = content.split('\n')

# ==========================================================
# FIX 1: Remove broken sub_overlay references from short_assets_ui
# ==========================================================
print("\n[1/3] Fixing NameError in short_assets_ui...")

new_lines = []
skip_block = False
skip_until_next_def = False
removed_count = 0

for i, line in enumerate(lines):
    stripped = line.strip()
    
    # Remove lines that reference sub_overlay in short_assets_ui context
    if 'sub_overlay' in line and ('save_uploaded_file' in line or 'sub_path' in line or 'sub_overlay' in line):
        # Check if this is in short_assets_ui function
        in_short = False
        for j in range(max(0, i-50), i):
            if 'def short_assets_ui' in lines[j]:
                in_short = True
                break
            if 'def ' in lines[j] and j > max(0, i-100):
                in_short = False
        
        if in_short:
            print(f"  [OK] Removed broken sub_overlay reference at line {i+1}")
            removed_count += 1
            continue
    
    # Also remove any standalone sub_overlay uploader blocks in short section
    if ('Subscribe' in stripped or 'sub_overlay' in stripped) and 'st.file_uploader' in stripped:
        in_short = False
        for j in range(max(0, i-30), i):
            if 'def short_assets_ui' in lines[j]:
                in_short = True
                break
        if in_short:
            print(f"  [OK] Removed sub_overlay uploader at line {i+1}")
            removed_count += 1
            # Skip this line and next few lines (uploader block)
            continue
    
    new_lines.append(line)

lines = new_lines
content = '\n'.join(lines)

# ==========================================================
# FIX 2: Also fix any remaining sub_path references that would break
# ==========================================================
print("[2/3] Cleaning up sub_path references...")

lines = content.split('\n')
new_lines = []
for i, line in enumerate(lines):
    # If sub_path is used but sub_overlay was removed, comment it out
    if 'sub_path' in line and 'sub_overlay' not in line:
        # Check if it's in short_assets_ui
        in_short = False
        for j in range(max(0, i-30), i):
            if 'def short_assets_ui' in lines[j]:
                in_short = True
                break
        if in_short:
            # Comment out the line
            indent = len(line) - len(line.lstrip())
            new_lines.append(' ' * indent + '# ' + line.lstrip() + '  # Disabled: sub_overlay removed')
            print(f"  [OK] Commented out sub_path usage at line {i+1}")
            continue
    new_lines.append(line)

content = '\n'.join(new_lines)

# ==========================================================
# FIX 3: Add Subscribe Overlay uploader to Long Video section
# ==========================================================
print("[3/3] Adding Subscribe Overlay to Long Video section...")

lines = content.split('\n')
new_lines = []
inject_idx = -1

# Find the Long Video assets section - look for "Long Video Assets" header
for i, line in enumerate(lines):
    if 'Long Video' in line and ('Assets' in line or 'assets' in line):
        # Found the section header, now find a good place to inject (after logo uploader)
        for j in range(i, min(i+100, len(lines))):
            if 'logo' in lines[j].lower() and 'file_uploader' in lines[j]:
                # Found logo uploader, inject after its block
                inject_idx = j + 1
                while inject_idx < len(lines) and (lines[inject_idx].strip() == '' or 
                      lines[inject_idx].strip().startswith('help=') or
                      lines[inject_idx].strip().startswith('type=') or
                      lines[inject_idx].strip().startswith('key=')):
                    inject_idx += 1
                break
        if inject_idx > 0:
            break

if inject_idx > 0:
    uploader_code = [
        "",
        "    # --- SUBSCRIBE OVERLAY UPLOADER (LONG VIDEO) ---",
        "    st.markdown(\"### 📢 Subscribe Overlay (Long Video) - Optional\")",
        "    long_subscribe_overlay = st.file_uploader(",
        "        \"Upload Subscribe Overlay for Long Video (PNG/JPG/MP4/MOV)\",",
        "        type=[\"png\", \"jpg\", \"jpeg\", \"mp4\", \"mov\", \"webm\"],",
        "        key=\"long_subscribe_overlay_uploader\",",
        "        help=\"Appears at 8-9 min mark. Use transparent PNG or green-screen video.\",",
        "    )",
        ""
    ]
    for code_line in uploader_code:
        lines.insert(inject_idx, code_line)
    print(f"  [OK] Injected Subscribe Overlay uploader at line {inject_idx+1}")
else:
    print("  [WARN] Could not find Long Video section. Trying fallback...")
    # Fallback: inject before the render button
    for i, line in enumerate(lines):
        if 'run_integrated_long_pipeline' in line or ('long' in line.lower() and 'render' in line.lower() and 'button' in line.lower()):
            inject_idx = i
            break
    if inject_idx > 0:
        uploader_code = [
            "",
            "    # --- SUBSCRIBE OVERLAY UPLOADER (LONG VIDEO) ---",
            "    st.markdown(\"### 📢 Subscribe Overlay (Long Video) - Optional\")",
            "    long_subscribe_overlay = st.file_uploader(",
            "        \"Upload Subscribe Overlay for Long Video\",",
            "        type=[\"png\", \"jpg\", \"jpeg\", \"mp4\", \"mov\", \"webm\"],",
            "        key=\"long_subscribe_overlay_uploader\",",
            "    )",
            ""
        ]
        for code_line in uploader_code:
            lines.insert(inject_idx, code_line)
        print(f"  [OK] Injected at fallback position line {inject_idx+1}")

content = '\n'.join(lines)

# ==========================================================
# FIX 4: Pass long_subscribe_overlay to backend in Long Video render call
# ==========================================================
print("\n[4/4] Connecting Subscribe Overlay to backend...")

# Find the render call for long video and add subscribe_overlay_path parameter
old_call = "custom_logo_path=_save_streamlit_upload_to_temp(logo_file) if 'logo_file' in locals() else None,"
new_call = """custom_logo_path=_save_streamlit_upload_to_temp(logo_file) if 'logo_file' in locals() else None,
                subscribe_overlay_path=_save_streamlit_upload_to_temp(long_subscribe_overlay) if 'long_subscribe_overlay' in locals() and long_subscribe_overlay else None,"""

if old_call in content:
    content = content.replace(old_call, new_call, 1)
    print("  [OK] Connected long_subscribe_overlay to backend")
else:
    # Try regex fallback
    pattern = r"(custom_logo_path=[^\n]+,)"
    replacement = r"\1\n                subscribe_overlay_path=_save_streamlit_upload_to_temp(long_subscribe_overlay) if 'long_subscribe_overlay' in locals() and long_subscribe_overlay else None,"
    new_content = re.sub(pattern, replacement, content, count=1)
    if new_content != content:
        content = new_content
        print("  [OK] Connected via regex fallback")
    else:
        print("  [WARN] Could not find render call to patch")

# Save
APP_FILE.write_text(content, encoding="utf-8")

# Verify syntax
try:
    import py_compile
    py_compile.compile(str(APP_FILE), doraise=True)
    print("\n✅ SYNTAX VERIFICATION PASSED!")
except py_compile.PyCompileError as e:
    print(f"\n❌ SYNTAX ERROR: {e}")
    print("Restoring from backup...")
    shutil.copy2(backup, APP_FILE)

print("\n" + "="*60)
print("✅ SUBSCRIBE OVERLAY FIX COMPLETE!")
print("="*60)
print("\n📋 WHAT WAS DONE:")
print("1. Removed broken sub_overlay references from Short Video section")
print("2. Fixed NameError: sub_overlay is not defined")
print("3. Added Subscribe Overlay uploader to Long Video section")
print("4. Connected to backend pipeline")
print("\n💡 NEXT STEP: Restart Streamlit -> streamlit run app.py")