import re
from pathlib import Path

batch_path = Path("batch_long_renderer.py")
content = batch_path.read_text(encoding="utf-8")

# Check if logo overlay already exists
if "def overlay_logo" in content:
    print("✅ Logo overlay function already present. Skipping.")
else:
    # 1. Sab se pehle function definition add karein (top level par)
    func_def = '''
def overlay_logo_on_video(input_video, logo_path, output_video, position="bottom-right", margin=20, scale=0.15):
    """
    Overlay logo using FFmpeg.
    position: "bottom-right", "top-right", "top-left", "bottom-left", "center"
    margin: pixels from edge
    scale: float (0.0 to 1.0) – relative to video width
    """
    import subprocess
    if not logo_path or not Path(logo_path).exists():
        # No logo, copy input to output
        import shutil
        shutil.copy2(input_video, output_video)
        return output_video
    
    # Calculate scale: width = video_width * scale
    # FFmpeg overlay filter: overlay=W-w-20:H-h-20 for bottom-right
    margin_str = str(margin)
    pos_map = {
        "bottom-right": f"overlay=W-w-{margin_str}:H-h-{margin_str}",
        "top-right": f"overlay=W-w-{margin_str}:{margin_str}",
        "top-left": f"overlay={margin_str}:{margin_str}",
        "bottom-left": f"overlay={margin_str}:H-h-{margin_str}",
        "center": f"overlay=(W-w)/2:(H-h)/2",
    }
    overlay_filter = pos_map.get(position, pos_map["bottom-right"])
    
    # Scale logo: if we want it relative to video width
    # FFmpeg scale filter: scale=iw*{scale}
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
        # Fallback: copy input
        import shutil
        shutil.copy2(input_video, output_video)
        return output_video
'''
    # Insert this function near the top (after imports)
    # Find first import line or after imports
    import_lines = re.findall(r'^(import|from)\s+', content, re.MULTILINE)
    if import_lines:
        # Insert after the last import
        last_import = re.finditer(r'^(import|from)\s+', content, re.MULTILINE)
        last_match = None
        for m in last_import:
            last_match = m
        if last_match:
            insert_pos = last_match.end()
            # Find the line end
            insert_line = content[:insert_pos].rfind('\n') + 1
            content = content[:insert_line] + "\n" + func_def + "\n" + content[insert_line:]
        else:
            # fallback: insert at top
            content = func_def + "\n" + content
    else:
        content = func_def + "\n" + content

    # 2. Ab `render_long_batch_memory` function ke end mein logo overlay call karein
    # Function ends with `return final` – uske pehle insert karein
    # Pattern: return final (with possible whitespace)
    pattern = r'(\s+return final\s*)$'
    replacement = r'''
    # ---- Logo Overlay ----
    logo_path = kwargs.get("logo_path")  # UI se aayega
    if logo_path and Path(logo_path).exists():
        logo_output = temp / "final_with_logo.mp4"
        overlay_logo_on_video(final, logo_path, logo_output, position="bottom-right", scale=0.12)
        final = logo_output
        report["logo_overlay_applied"] = True
    \1
    '''
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    batch_path.write_text(content, encoding="utf-8")
    print("✅ Logo overlay added to batch_long_renderer.py")