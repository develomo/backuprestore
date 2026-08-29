"""
FIX: sfx_files not defined in safe_long_video_polished.py line 191
"""
import os

BACKUP_DIR = os.path.dirname(os.path.abspath(__file__))
SL_PATH = os.path.join(BACKUP_DIR, 'safe_long_video_polished.py')

if not os.path.exists(SL_PATH):
    print(f"[ERROR] {SL_PATH} not found!")
    import sys; sys.exit(1)

with open(SL_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
bak = SL_PATH + '.backup_sfx'
with open(bak, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"[OK] Backup: {bak}")

fixes = 0

# The problematic line has sfx_files in inline semicolon code:
# sfx=choose_sfx(sfx_files,kwargs,assets);
# FIX 1: Replace sfx_files with sfx_path
if 'sfx=choose_sfx(sfx_files,' in content:
    content = content.replace('sfx=choose_sfx(sfx_files,', 'sfx=choose_sfx(sfx_path,')
    fixes += 1
    print("[FIX 1] sfx_files -> sfx_path in choose_sfx call")

# FIX 2: Any remaining bare sfx_files (not sfx_path)
import re
# Only replace if it's a standalone variable use, not already sfx_path
count_before = content.count('sfx_files')
# Replace sfx_files with sfx_path but be careful
if 'sfx_files' in content:
    # Replace isolated sfx_files that aren't part of a larger word
    content = content.replace('sfx_files', 'sfx_path')
    count_after = content.count('sfx_path')
    # But we might have over-replaced, let's check
    if 'sfx_path_path' in content:
        content = content.replace('sfx_path_path', 'sfx_path')
        print("[FIX 2] Cleaned up double replacement")
    fixes += 1
    print(f"[FIX 2] All remaining sfx_files -> sfx_path")

# FIX 3: clips=clip_list -> clip_paths=clip_list
if 'clips=clip_list' in content:
    content = content.replace('clips=clip_list', 'clip_paths=clip_list')
    fixes += 1
    print("[FIX 3] clips= -> clip_paths=")

# FIX 4: final_quality= remove
if 'final_quality=' in content:
    content = re.sub(r',?\s*final_quality\s*=\s*"[^"]*"', '', content)
    fixes += 1
    print("[FIX 4] Removed final_quality= arg")

# FIX 5: cleanup=True -> keep_temp=False
if 'cleanup=True' in content:
    content = content.replace('cleanup=True', 'keep_temp=False')
    fixes += 1
    print("[FIX 5] cleanup=True -> keep_temp=False")

# Validate syntax
try:
    compile(content, SL_PATH, 'exec')
    print("\n[OK] Syntax check PASSED!")
except SyntaxError as e:
    print(f"\n[ERROR] SyntaxError: {e}")
    print("Restoring from backup...")
    import shutil
    shutil.copy(bak, SL_PATH)
    import sys; sys.exit(1)

# Write
with open(SL_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"[SUCCESS] {fixes} fixes applied to safe_long_video_polished.py")
print("[INFO] sfx_files -> sfx_path (FIXED)")
print("[INFO] clips=clip_list -> clip_paths=clip_list (FIXED)")
print("\n▶ streamlit run app.py")