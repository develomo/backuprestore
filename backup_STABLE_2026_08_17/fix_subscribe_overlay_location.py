# fix_subscribe_overlay_location.py
# Moves Subscribe Overlay uploader from Short Video section to Long Video section
import re
from pathlib import Path

APP_FILE = Path("app.py")
if not APP_FILE.exists():
    print("[ERROR] app.py not found!")
    exit(1)

# Backup first
import shutil
backup = APP_FILE.with_suffix(".py.subscribe_fix_backup")
if not backup.exists():
    shutil.copy2(APP_FILE, backup)
    print(f"[OK] Backup created: {backup.name}")

content = APP_FILE.read_text(encoding="utf-8")
lines = content.split('\n')

# ==========================================================
# STEP 1: Remove Subscribe Overlay from Short Video section
# ==========================================================
# The Subscribe Overlay uploader block to remove (anywhere it appears outside long video section)
subscribe_block_pattern = [
    '# --- SUBSCRIBE OVERLAY UPLOADER',
    'st.markdown("### 📢 Subscribe Overlay',
    'subscribe_overlay_file = st.file_uploader',
    '"Upload Subscribe Overlay',
    'key="long_subscribe_overlay"',
    'help="Upload a transparent PNG',
]

new_lines = []
skip_block = False
skip_indent = 0
removed_short = 0

for i, line in enumerate(lines):
    stripped = line.strip()
    
    # Detect start of subscribe overlay uploader block
    if not skip_block and ('Subscribe Overlay' in stripped or 'subscribe_overlay_file' in stripped or 'subscribe_overlay_path' in stripped):
        # Check if this is in SHORT video section (not long)
        # Look backwards to find which section we're in
        in_short_section = False
        in_long_section = False
        for j in range(i-1, max(0, i-50), -1):
            prev = lines[j].lower()
            if 'short video' in prev or 'short_video' in prev or 'short-video' in prev:
                in_short_section = True
                break
            if 'long video' in prev or 'long_video' in prev or 'long-video' in prev:
                in_long_section = True
                break
        
        # Only remove if in SHORT section OR if it's a stray block
        if in_short_section or not in_long_section:
            skip_block = True
            skip_indent = len(line) - len(line.lstrip())
            removed_short += 1
            print(f"[OK] Removing Subscribe Overlay from line {i+1} (Short Video section)")
            continue
    
    if skip_block:
        current_indent = len(line) - len(line.lstrip())
        # Stop skipping when we hit a line at same or lower indent that's not empty
        if line.strip() and current_indent <= skip_indent:
            skip_block = False
            new_lines.append(line)
        # else: keep skipping
        continue
    
    new_lines.append(line)

lines = new_lines

# ==========================================================
# STEP 2: Add Subscribe Overlay uploader to Long Video section
# ==========================================================
# Find the Long Video section - look for custom_logo_path or logo_file uploader
content = '\n'.join(lines)

# The uploader code to inject
subscribe_uploader_code = '''
    # --- SUBSCRIBE OVERLAY UPLOADER (LONG VIDEO) ---
    st.markdown("### 📢 Subscribe Overlay (Long Video)")
    subscribe_overlay_file = st.file_uploader(
        "Upload Subscribe Overlay (Optional)",
        type=["png", "jpg", "jpeg", "mp4", "mov", "webm"],
        key="long_subscribe_overlay",
        help="Upload a transparent PNG or a green-screen video for the subscribe animation. It will automatically appear around the 8-minute mark."
    )
'''

# Find where to inject - after custom_logo_path / logo_file uploader in Long Video section
# Look for the line that has custom_logo_path or logo_file in the long video call
inject_marker = None
for i, line in enumerate(lines):
    # Find the long video section by looking for long video related markers
    if ('custom_logo_path' in line and 'logo_file' in line) or \
       ('wm_opacity' in line and 'st.slider' in line) or \
       ('logo_file' in line and 'st.file_uploader' in line):
        # Check if we're in long video section
        in_long = False
        for j in range(i-1, max(0, i-100), -1):
            prev = lines[j].lower()
            if 'long video' in prev or 'long_video' in prev:
                in_long = True
                break
            if 'short video' in prev or 'short_video' in prev:
                break
        if in_long:
            # Find the end of this uploader block (next non-indented or new widget)
            inject_idx = i + 1
            while inject_idx < len(lines):
                next_line = lines[inject_idx]
                if next_line.strip() == '':
                    inject_idx += 1
                    continue
                next_indent = len(next_line) - len(next_line.lstrip())
                current_indent = len(line) - len(line.lstrip())
                if next_indent <= current_indent and next_line.strip():
                    break
                inject_idx += 1
            inject_marker = inject_idx
            break

if inject_marker:
    # Insert the subscribe uploader at the marker
    lines.insert(inject_marker, subscribe_uploader_code)
    print(f"[OK] Added Subscribe Overlay uploader to Long Video section at line {inject_marker+1}")
else:
    print("[WARN] Could not find Long Video section marker. Trying alternative...")
    # Fallback: find the render button for long video and inject before it
    for i, line in enumerate(lines):
        if 'run_integrated_long_pipeline' in line or ('long' in line.lower() and 'render' in line.lower() and 'st.button' in line):
            # Find the start of this block
            inject_idx = i
            while inject_idx > 0 and lines[inject_idx-1].strip():
                inject_idx -= 1
            lines.insert(inject_idx, subscribe_uploader_code)
            print(f"[OK] Added Subscribe Overlay uploader before long video render at line {inject_idx+1}")
            break

# ==========================================================
# STEP 3: Ensure subscribe_overlay_file is passed to backend
# ==========================================================
content = '\n'.join(lines)

# Check if subscribe_overlay_path is already being passed
if 'subscribe_overlay_path=_save_streamlit_upload_to_temp(subscribe_overlay_file)' not in content:
    # Find the render_long_batch_memory or run_integrated_long_pipeline call in long video
    # and add subscribe_overlay_path parameter
    old_call_pattern = r'(custom_logo_path=_save_streamlit_upload_to_temp\(logo_file\)[^,]*,)'
    
    def add_subscribe_param(match):
        original = match.group(1)
        # Add subscribe_overlay_path after custom_logo_path
        new_param = '\n                subscribe_overlay_path=_save_streamlit_upload_to_temp(subscribe_overlay_file) if \'subscribe_overlay_file\' in locals() and subscribe_overlay_file else None,'
        return original + new_param
    
    new_content = re.sub(old_call_pattern, add_subscribe_param, content, count=1)
    
    if new_content != content:
        content = new_content
        print("[OK] Added subscribe_overlay_path parameter to backend call")
    else:
        print("[INFO] subscribe_overlay_path may already be passed or pattern not found")
else:
    print("[INFO] subscribe_overlay_path already being passed to backend")

# Save
APP_FILE.write_text(content, encoding="utf-8")

# Verify syntax
try:
    import py_compile
    py_compile.compile(str(APP_FILE), doraise=True)
    print("\n✅ SYNTAX VERIFICATION PASSED!")
except py_compile.PyCompileError as e:
    print(f"\n❌ SYNTAX ERROR: {e}")
    print("Please restore from backup: app.py.subscribe_fix_backup")

print("\n" + "="*60)
print("✅ SUBSCRIBE OVERLAY MOVED TO LONG VIDEO SECTION!")
print("="*60)
print("\n💡 Next Step: Restart Streamlit -> streamlit run app.py")
print("💡 Subscribe Overlay uploader will now appear in Long Video Assets section")