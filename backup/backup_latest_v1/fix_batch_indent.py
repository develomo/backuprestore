import re
from pathlib import Path

def fix_batch():
    file_path = Path("batch_long_renderer.py")
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    # 1. Find the function start
    start_idx = None
    for i, line in enumerate(lines):
        if re.match(r'^def overlay_logo_on_video\s*\(', line):
            start_idx = i
            break
    
    # 2. Define the correct function (with proper indentation)
    correct_func = '''
def overlay_logo_on_video(input_video, logo_path, output_video, position="bottom-right", margin=20, scale=0.15):
    """Overlay logo using FFmpeg."""
    import subprocess
    from pathlib import Path
    if not logo_path or not Path(logo_path).exists():
        import shutil
        shutil.copy2(input_video, output_video)
        return output_video
    margin_str = str(margin)
    pos_map = {
        "bottom-right": f"overlay=W-w-{margin_str}:H-h-{margin_str}",
        "top-right": f"overlay=W-w-{margin_str}:{margin_str}",
        "top-left": f"overlay={margin_str}:{margin_str}",
        "bottom-left": f"overlay={margin_str}:H-h-{margin_str}",
        "center": f"overlay=(W-w)/2:(H-h)/2",
    }
    overlay_filter = pos_map.get(position, pos_map["bottom-right"])
    scale_filter = f"scale=iw*{scale}"
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_video),
        "-i", str(logo_path),
        "-filter_complex",
        f"[1:v]{scale_filter}[logo];[0:v][logo]{overlay_filter}",
        "-c:a", "copy",
        str(output_video)
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return output_video
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg logo overlay failed: {e.stderr.decode()}")
        import shutil
        shutil.copy2(input_video, output_video)
        return output_video
'''

    if start_idx is None:
        print("ℹ️ Function not found. Adding it at top (after imports).")
        # Insert after last import
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith(("import ", "from ")):
                insert_idx = i + 1
        lines.insert(insert_idx, correct_func)
    else:
        print(f"🔍 Found function at line {start_idx+1}. Removing it...")
        # Find end of function: next line at indentation level 0 (no spaces/tabs)
        end_idx = start_idx + 1
        while end_idx < len(lines):
            if len(lines[end_idx]) > 0 and lines[end_idx][0] not in (' ', '\t'):
                # This is a new top-level line
                break
            end_idx += 1
        # Remove the block
        del lines[start_idx:end_idx]
        print(f"🗑️ Removed old function.")
        # Insert correct function at the same position
        lines.insert(start_idx, correct_func)
        print("✅ Inserted corrected function.")

    # Write back
    file_path.write_text("\n".join(lines), encoding="utf-8")
    print("✅ batch_long_renderer.py is now fixed!")

if __name__ == "__main__":
    fix_batch()