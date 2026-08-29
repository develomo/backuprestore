import re
from pathlib import Path

def remove_logo_from_batch():
    file_path = Path("batch_long_renderer.py")
    content = file_path.read_text(encoding="utf-8")
    
    # 1. Remove the entire overlay_logo_on_video function
    # Pattern to match the function definition and its body until next top-level line
    pattern = r'^def overlay_logo_on_video.*?(\n\S.*?)*?(?=\n\S|$)'
    # Use DOTALL to match across lines
    content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
    
    # 2. Remove any leftover calls to overlay_logo_on_video inside render_long_batch_memory
    # Look for the logo overlay block we added earlier
    content = re.sub(r'# ---- Logo Overlay ----.*?overlay_logo_on_video\([^)]+\)\s*', '', content, flags=re.DOTALL)
    
    # 3. Remove any extra imports added for logo (like import shutil inside function is already removed)
    
    file_path.write_text(content, encoding="utf-8")
    print("✅ Removed overlay_logo_on_video function from batch_long_renderer.py")
    
    # Also remove any 'logo_path' in kwargs handling if present
    # We'll do a simple search and replace for logo_path references in the render function
    content = file_path.read_text(encoding="utf-8")
    # Remove logo_path from kwargs usage (if any)
    content = re.sub(r'logo_path = kwargs\.get\("logo_path"\)', '', content)
    content = re.sub(r'if logo_path and Path\(logo_path\)\.exists\(\):.*?\n', '', content, flags=re.DOTALL)
    file_path.write_text(content, encoding="utf-8")
    print("✅ Cleaned up any remaining logo_path references.")

def remove_logo_from_app():
    file_path = Path("app.py")
    content = file_path.read_text(encoding="utf-8")
    
    # 1. Remove the upload_single line for logo
    # Find and remove line containing "Logo Overlay"
    lines = content.splitlines()
    new_lines = []
    skip_next = False
    for i, line in enumerate(lines):
        if 'upload_single("Logo Overlay"' in line:
            continue
        # Also remove the line after (which might be empty or part of assets)
        new_lines.append(line)
    
    # 2. Remove logo entry from assets dict
    content = "\n".join(new_lines)
    # Remove line with "logo": logo,
    content = re.sub(r'^\s*"logo": logo,\s*$', '', content, flags=re.MULTILINE)
    
    file_path.write_text(content, encoding="utf-8")
    print("✅ Removed logo upload and assets entry from app.py")

if __name__ == "__main__":
    print("🧹 Removing Logo feature completely...")
    remove_logo_from_batch()
    remove_logo_from_app()
    print("\n✅ Logo feature removed. Now run streamlit run app.py")