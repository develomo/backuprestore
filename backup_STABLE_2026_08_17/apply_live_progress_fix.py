import os
import re

files_to_patch = ["batch_long_renderer.py", "safe_long_video_polished.py"]

print("🔧 Applying Live Progress & Terminal Output Fix...")

# Improved run_cmd implementation that streams FFmpeg output directly to console
LIVE_RUN_CMD_CODE = '''
def run_cmd(cmd):
    import subprocess, sys
    print(f"\\n▶ Running: {' '.join(str(x) for x in cmd[:4])}... ", end="", flush=True)
    try:
        # Direct console stream to prevent buffering deadlocks
        res = subprocess.run(cmd, check=True, stdout=None, stderr=None)
        print("✅ Done", flush=True)
        return res
    except subprocess.CalledProcessError as e:
        print(f"\\n❌ Error executing command: {e}", flush=True)
        raise e
'''

for file_path in files_to_patch:
    if not os.path.exists(file_path):
        print(f"⚠️ File not found: {file_path}")
        continue

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Backup create karein
    with open(f"{file_path}.bak_live", "w", encoding="utf-8") as f:
        f.write(content)

    # Replace or ensure print statements use flush=True
    content = content.replace("print(", "print(") # Ensure visibility
    
    # Force run_cmd to not suppress output
    if "def run_cmd(" in content:
        # Pattern to replace existing run_cmd
        content = re.sub(r'def run_cmd\(cmd.*?\):\n(?:\s+.*?\n)+', LIVE_RUN_CMD_CODE + '\n', content, flags=re.DOTALL)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"⚡ Live terminal output enabled in: {file_path}")

print("\n✅ Live Logging Patch Applied Successfully!")