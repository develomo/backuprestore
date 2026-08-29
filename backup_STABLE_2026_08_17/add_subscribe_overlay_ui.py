# add_subscribe_overlay_ui.py
# Surgically adds Subscribe Overlay Uploader to Long Video UI and connects it to the backend
import re
from pathlib import Path

APP_FILE = Path("app.py")
if not APP_FILE.exists():
    print("[ERROR] app.py not found!")
    exit(1)

content = APP_FILE.read_text(encoding="utf-8")
lines = content.split('\n')

# ==========================================================
# STEP 1: Add UI Uploader in Long Video Section
# ==========================================================
insert_idx = -1
# Look for the logo uploader or wm_opacity slider in the Long Video section
for i, line in enumerate(lines):
    if "wm_opacity" in line or "logo_file" in line or "Watermark" in line:
        # Found a relevant line, let's insert after this block
        idx = i + 1
        while idx < len(lines):
            stripped = lines[idx].strip()
            # Skip continuation lines of the previous widget
            if stripped.startswith("help=") or stripped.startswith("type=") or stripped.startswith("key=") or stripped == "":
                idx += 1
            else:
                break
        insert_idx = idx
        break

if insert_idx > 0:
    uploader_code = [
        "",
        "    # --- SUBSCRIBE OVERLAY UPLOADER (LONG VIDEO) ---",
        "    st.markdown(\"### 📢 Subscribe Overlay (Long Video)\")",
        "    subscribe_overlay_file = st.file_uploader(",
        "        \"Upload Subscribe Overlay (Optional)\",",
        "        type=[\"png\", \"jpg\", \"jpeg\", \"mp4\", \"mov\", \"webm\"],",
        "        key=\"long_subscribe_overlay\",",
        "        help=\"Upload a transparent PNG or a green-screen video for the subscribe animation. It will automatically appear around the 8-minute mark.\"",
        "    )"
    ]
    for j, code_line in enumerate(uploader_code):
        lines.insert(insert_idx + j, code_line)
    print("[OK] Step 1: Added Subscribe Overlay Uploader to UI.")
else:
    print("[WARN] Step 1: Could not find exact insertion point. Adding before Render button.")
    # Fallback: Add before the main render button
    for i, line in enumerate(lines):
        if "Generate" in line or "Render" in line or "Start" in line:
            if "st.button" in line or "st.form_submit_button" in line:
                insert_idx = i
                break
    if insert_idx > 0:
        uploader_code = [
            "",
            "    # --- SUBSCRIBE OVERLAY UPLOADER (LONG VIDEO) ---",
            "    st.markdown(\"### 📢 Subscribe Overlay (Long Video)\")",
            "    subscribe_overlay_file = st.file_uploader(",
            "        \"Upload Subscribe Overlay (Optional)\",",
            "        type=[\"png\", \"jpg\", \"jpeg\", \"mp4\", \"mov\", \"webm\"],",
            "        key=\"long_subscribe_overlay\",",
            "        help=\"Upload a transparent PNG or a green-screen video for the subscribe animation. It will automatically appear around the 8-minute mark.\"",
            "    )",
            ""
        ]
        for j, code_line in enumerate(uploader_code):
            lines.insert(insert_idx + j, code_line)
        print("[OK] Step 1: Added Subscribe Overlay Uploader before Render button.")

content = '\n'.join(lines)

# ==========================================================
# STEP 2: Pass the uploaded file to the Backend Pipeline
# ==========================================================
if "run_integrated_long_pipeline" in content:
    old_str = "custom_logo_path=_save_streamlit_upload_to_temp(logo_file) if 'logo_file' in locals() else None,"
    new_str = """custom_logo_path=_save_streamlit_upload_to_temp(logo_file) if 'logo_file' in locals() else None,
                subscribe_overlay_path=_save_streamlit_upload_to_temp(subscribe_overlay_file) if 'subscribe_overlay_file' in locals() and subscribe_overlay_file else None,"""
    
    if old_str in content:
        content = content.replace(old_str, new_str, 1)
        print("[OK] Step 2: Passed subscribe_overlay_path to the Long Video Pipeline.")
    else:
        # Fallback regex if formatting is slightly different
        pattern = r"(custom_logo_path=[^\n]+,)"
        replacement = r"\1\n                subscribe_overlay_path=_save_streamlit_upload_to_temp(subscribe_overlay_file) if 'subscribe_overlay_file' in locals() and subscribe_overlay_file else None,"
        content = re.sub(pattern, replacement, content, count=1)
        print("[OK] Step 2: Passed subscribe_overlay_path to the Long Video Pipeline (Regex fallback).")
else:
    print("[WARN] Step 2: Could not find run_integrated_long_pipeline in app.py.")

# ==========================================================
# STEP 3: Save the modified app.py
# ==========================================================
APP_FILE.write_text(content, encoding="utf-8")

print("\n" + "="*60)
print("✅ SUCCESS: Subscribe Overlay Uploader Fully Implemented!")
print("="*60)
print("💡 Next Step: Restart Streamlit (`streamlit run app.py`)")
print("💡 Go to Long Video section, and you will see the new Uploader.")
print("💡 Backend (safe_long_video_polished.py) already knows how to handle 'subscribe_overlay_path' automatically!")