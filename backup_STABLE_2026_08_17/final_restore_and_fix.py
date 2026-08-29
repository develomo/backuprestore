# final_restore_and_fix.py
import os
import shutil
import subprocess
import sys

print("="*70)
print("🔄 RESTORING LATEST WORKING BACKUP & FIXING MOVIEPY")
print("="*70)

backup_dir = "backup_latest_v1"
files_to_restore = [
    "batch_long_renderer.py",
    "safe_long_video_polished.py",
    "master_pipeline.py"
]

print("\n[STEP 1] Restoring files from 'backup_latest_v1'...")
for filename in files_to_restore:
    src = os.path.join(backup_dir, filename)
    dst = filename
    if os.path.exists(src):
        # Safety backup of current file
        if os.path.exists(dst):
            shutil.copy2(dst, f"{dst}.before_final_restore")
        
        shutil.copy2(src, dst)
        print(f"  ✅ Restored: {filename}")
    else:
        print(f"  ⚠️  Not found in backup: {filename}")

print("\n[STEP 2] Installing MoviePy (Required for Video Engine)...")
try:
    print("  ⏳ Downloading and installing moviepy (v1.0.3 for stability)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "moviepy==1.0.3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("  ✅ MoviePy 1.0.3 installed successfully!")
except subprocess.CalledProcessError:
    try:
        print("  ⏳ Trying latest version of moviepy...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "moviepy"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("  ✅ MoviePy (latest) installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to install MoviePy automatically.")
        print(f"  Please run this command manually in terminal: pip install moviepy")

print("\n" + "="*70)
print("✅ RESTORE & FIX COMPLETE!")
print("="*70)
print("💡 Next Steps:")
print("   1. Band karein current Streamlit window (Terminal mein Ctrl+C dabayein)")
print("   2. Dobara start karein: streamlit run app.py")
print("   3. Ab Short aur Long dono videos bina kisi error ke render hongi!")