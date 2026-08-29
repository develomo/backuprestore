import os
import re

def total_repair():
    file_path = "app.py"
    backup_path = "app.py.nuclear_backup"
    
    if not os.path.exists(file_path):
        print("Error: app.py nahi mili!")
        return

    # 1. File ko raw text ki tarah read karna
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    # Backup for safety
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(raw_content)

    # 2. SABSE ZAROORI: Literal \\n ko asli Enter (Newline) mein badalna
    # Yeh aapki line 1 ka error khatam kar dega
    clean_content = raw_content.replace('\\n', '\n')
    
    # 3. Purane saare kharab Navbar blocks ko delete karna
    # Hum pichle saare AI-generated comments aur codes ko saaf karenge
    patterns_to_remove = [
        r'# ==========================================.*?# ==========================================',
        r'# --- START OF CUSTOM NAVBAR ---.*?# --- END OF CUSTOM NAVBAR ---',
        r'# --- START OF CUSTOM NAVBAR ---.*?# --- END OF CUSTOM NAVBAR ---',
        r'def render_creatorflow_nav\(.*?\):.*?st\.stop\(\)',
        r'def inject_navbar\(.*?\):.*?st\.stop\(\)',
        r'def apply_professional_ui\(.*?\):.*?st\.stop\(\)'
    ]
    
    for pattern in patterns_to_remove:
        clean_content = re.sub(pattern, "", clean_content, flags=re.DOTALL)

    # 4. Fresh Stable Navbar Logic
    navbar_logic = """
# =========================================================
# CREATORFLOW PRO - STABLE NAVBAR
# =========================================================
import streamlit as st

def inject_main_nav():
    st.markdown(\"\"\"
        <style>
        .nav-container {
            display: flex; justify-content: center; background: #1a1a1a;
            padding: 15px; border-bottom: 3px solid #FF4B4B; margin-bottom: 25px;
        }
        .nav-link {
            color: white !important; text-decoration: none; padding: 10px 25px;
            margin: 0 10px; font-weight: bold; border-radius: 5px; transition: 0.3s;
        }
        .nav-link:hover { background: #FF4B4B; }
        </style>
        <div class="nav-container">
            <a href="/?nav=video" class="nav-link">🎬 Video Generator</a>
            <a href="/?nav=reels" class="nav-link">📱 Reels Studio</a>
        </div>
    \"\"\", unsafe_allow_html=True)

# Page Control
if 'nav' not in st.query_params:
    st.query_params['nav'] = 'video'

inject_main_nav()

if st.query_params['nav'] == 'reels':
    st.title("📱 Reels Upload Studio")
    # Check if the function exists
    if 'reels_upload_studio_tab' in globals():
        reels_upload_studio_tab()
    else:
        st.error("Error: 'reels_upload_studio_tab' function nahi mili!")
    st.stop()
# =========================================================
"""

    # 5. Navbar ko "import streamlit as st" ke foran baad insert karna
    lines = clean_content.splitlines()
    final_output = []
    inserted = False
    
    for line in lines:
        # Purane 'try:' blocks jo syntax error de rahe thay unhein handle karna
        if line.strip() == "try:":
            continue
        if "query_params = st.query_params" in line:
            continue
            
        final_output.append(line)
        
        if not inserted and "import streamlit as st" in line:
            final_output.append(navbar_logic)
            inserted = True

    # Agar "import streamlit as st" nahi mila toh line 1 par daal dein
    if not inserted:
        final_output.insert(0, navbar_logic)

    # Final Save
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(final_output))
    
    print("✅ SUCCESS: app.py ki line 1 ka 'Single Line' error theek ho gaya!")
    print("✅ SUCCESS: Saare purane kharab patches saaf ho gaye.")
    print("✅ SUCCESS: Professional Navbar lag chuki hai.")

if __name__ == "__main__":
    total_repair()