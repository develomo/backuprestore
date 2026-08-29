import re
from pathlib import Path
file_path = Path("batch_long_renderer.py")
content = file_path.read_text(encoding="utf-8")
# Correct version of the function (with proper indentation)
correct_func = '''
def overlay_logo_on_video(input_video, logo_path, output_video, position="bottom-right", margin=20, scale=0.15):
    """
    Overlay logo using FFmpeg.
    position: "bottom-right", "top-right", "top-left", "bottom-left", "center"
    margin: pixels from edge
    scale: float (0.0 to 1.0) – relative to video width
    """
    import subprocess
    from pathlib import Path
    if not logo_path or not Path(logo_path).exists():
        # No logo, copy input to output
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
# Find and replace the entire function definition
pattern = r'(def overlay_logo_on_video$  .*?  $:.*?)(?=\n\S|$)'
content, count = re.subn(pattern, correct_func, content, flags=re.DOTALL)
if count > 0:
    file_path.write_text(content, encoding="utf-8")
    print(f"✅ Replaced overlay_logo_on_video function with fixed indentation.")
else:
    print("⚠️ Could not find the function. Trying to remove it and add fresh...")
    # Fallback: if function not found, maybe it's already missing? We'll just add at top after imports.
    # But we need to ensure we remove any partial definitions.
    # Let's just check if function exists, if not, add it.
    if "def overlay_logo_on_video" not in content:
        # Insert after imports
        lines = content.splitlines()
        # find first import line or after imports
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("import") or line.startswith("from"):
                insert_idx = i + 1
        # Insert the function after that
        lines.insert(insert_idx, correct_func.strip())
        file_path.write_text("\n".join(lines), encoding="utf-8")
        print("✅ Inserted overlay_logo_on_video function at top.")
    else:
        print("❌ Could not fix automatically. Please manually remove the function and paste the correct version.")
 