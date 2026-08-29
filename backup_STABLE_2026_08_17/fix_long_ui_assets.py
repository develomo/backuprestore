import os
import re

print("🚀 Fixing app.py UI for Long Video Subscribe Overlay & Captions Checkbox...")

if os.path.exists("app.py"):
    with open("app.py", "r", encoding="utf-8") as f:
        code = f.read()

    # Create backup
    with open("app.py.bak_ui_assets", "w", encoding="utf-8") as dst:
        dst.write(code)

    # 1. Clean up previous attempt snippets if any
    code = code.replace('st.subheader("Subscribe Call-to-Action & Overlays")', '')

    # 2. Inject Subscribe Overlay & Captions Checkbox directly into Long Video Assets UI Section
    ui_elements_to_inject = '''
            # --- LONG VIDEO SPECIFIC EXTRA ASSETS ---
            st.markdown("---")
            st.subheader("📢 Long Video CTA & Captions Control")
            col_sub, col_cap = st.columns(2)
            with col_sub:
                long_subscribe_file = st.file_uploader(
                    "Upload Subscribe Call-To-Action Overlay (.mp4, .mov, .png)", 
                    type=["mp4", "mov", "png", "gif"], 
                    key="long_subscribe_uploader"
                )
            with col_cap:
                st.write("**Subtitle Settings**")
                add_captions_toggle = st.checkbox(
                    "Enable Subtitles / Captions Burn-In", 
                    value=True, 
                    key="long_captions_checkbox"
                )
'''

    # Find where long video inputs are processed or where Outro uploader is located in app.py
    if "long_subscribe_uploader" not in code:
        # Search for key UI markers in app.py for Long Video
        if 'key="outro_file"' in code or 'key="long_outro"' in code or 'Outro' in code:
            # Place after Outro/Intro input block
            target_pattern = r'(st\.file_uploader\(.*?[oO]utro.*?\))'
            if re.search(target_pattern, code):
                code = re.sub(target_pattern, r'\1\n' + ui_elements_to_inject, code, count=1)
            else:
                # Fallback insertion before render button
                code = code.replace('st.button("🚀 Render High-Quality Video Project"', ui_elements_to_inject + '\n            st.button("🚀 Render High-Quality Video Project"')
        else:
            # Direct placement before render trigger
            code = code.replace('st.button(', ui_elements_to_inject + '\n    st.button(')

    # 3. Ensure backend receives add_captions_toggle state correctly
    code = code.replace(
        'add_captions=True',
        'add_captions=add_captions_toggle if "add_captions_toggle" in locals() else True'
    )

    with open("app.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("✅ Successfully added Subscribe Overlay & Captions Checkbox to Long Video Assets UI!")
else:
    print("❌ Error: app.py file not found in current directory.")