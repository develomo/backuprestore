import os
import re
import multiprocessing

CPU_THREADS = max(1, multiprocessing.cpu_count())

target_files = [
    "safe_long_video_polished.py",
    "batch_long_renderer.py"
]

print("⚡ Starting Ultra-Fast 480p Speed Engine Patch for LONG VIDEOS...")

for file_path in target_files:
    if not os.path.exists(file_path):
        print(f"⚠️ File not found: {file_path}")
        continue

    # Backup create karein
    backup_path = f"{file_path}.bak_speed"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"📦 Created Backup: {backup_path}")

    # 1. Preset ko 'ultrafast' par force karein
    content = re.sub(r'preset\s*=\s*["\'][^"\']+["\']', 'preset="ultrafast"', content)

    # 2. FPS ko 24 par set karein
    content = re.sub(r'fps\s*=\s*\d+', 'fps=24', content)

    # 3. Threads optimize karein
    content = re.sub(r'threads\s*=\s*[^,)\n]+', f'threads={CPU_THREADS}', content)

    # 4. Height resize ko 480p force karein
    content = re.sub(r'height\s*=\s*\d+', 'height=480', content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"⚡ Successfully patched long video file: {file_path}")

print("✅ Long Video Ultra-Fast Engine Patch Complete!")