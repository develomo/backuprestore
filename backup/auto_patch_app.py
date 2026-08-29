import ast
import os
import shutil

APP_FILE = "app.py"
BACKUP_FILE = "app.py.bak"

IMPORTS_CODE = """from master_pipeline import run_integrated_short_pipeline
from safe_long_video_polished import run_integrated_long_pipeline
"""

NEW_FUNCTION_CODE = '''def execute_rendering_pipeline(mode, settings, assets, add_captions, caption_mode, style_id):
    """
    Short aur Long Video modes ko UI settings aur assets ke mutabiq unki respective pipelines mein route karta hai.
    """
    voice_path = assets.get("voice_path")
    clips = assets.get("clips", [])
    words = assets.get("words", None)
    words_path = assets.get("words_path", None)
    transcript_text = assets.get("transcript_text", "")
    output_path = settings.get("output_path", "output_render.mp4")
    niche = settings.get("niche", "General")
    render_count = settings.get("render_count", 1)
    music_path = assets.get("music_path", None)
    sfx_files = assets.get("sfx_files", [])
    use_hook = settings.get("use_hook", False)
    hook_text = settings.get("hook_text", "")
    final_4k = settings.get("final_4k", False)
    fps = settings.get("fps", 30)
    quality = settings.get("quality", "720p")
    clean_silence = settings.get("clean_silence", True)
    preset_overrides = settings.get("preset_overrides", {})

    mode_clean = str(mode).strip().lower()

    if mode_clean == "short":
        return run_integrated_short_pipeline(
            voice_path=voice_path,
            clips=clips,
            words=words,
            words_path=words_path,
            transcript_text=transcript_text,
            output_path=output_path,
            niche=niche,
            render_count=render_count,
            caption_mode=caption_mode,
            style_id=style_id,
            music_path=music_path,
            sfx_files=sfx_files,
            use_hook=use_hook,
            hook_text=hook_text,
            final_4k=final_4k,
            fps=fps,
            quality=quality,
            clean_silence=clean_silence,
            add_captions=add_captions,
            preset_overrides=preset_overrides
        )

    elif mode_clean == "long":
        use_overlays = settings.get("use_overlays", False)
        custom_logo_path = settings.get("custom_logo_path", None)
        wm_opacity = settings.get("wm_opacity", 0.8)

        return run_integrated_long_pipeline(
            voice_path=voice_path,
            clips=clips,
            words=words,
            words_path=words_path,
            transcript_text=transcript_text,
            output_path=output_path,
            niche=niche,
            render_count=render_count,
            caption_mode=caption_mode,
            style_id=style_id,
            music_path=music_path,
            sfx_files=sfx_files,
            use_hook=use_hook,
            hook_text=hook_text,
            use_overlays=use_overlays,
            final_4k=final_4k,
            fps=fps,
            quality=quality,
            clean_silence=clean_silence,
            add_captions=add_captions,
            preset_overrides=preset_overrides,
            custom_logo_path=custom_logo_path,
            wm_opacity=wm_opacity
        )

    else:
        raise ValueError(f"Invalid Video Mode Selected: '{mode}'. Expected 'short' or 'long'.")
'''

def apply_patch():
    if not os.path.exists(APP_FILE):
        print(f"Error: '{APP_FILE}' nahi mili! Make sure script project folder mein chal rahi ho.")
        return

    # Backup original file
    shutil.copyfile(APP_FILE, BACKUP_FILE)
    print(f"[1/3] Backup file saved as: {BACKUP_FILE}")

    with open(APP_FILE, "r", encoding="utf-8") as f:
        source = f.read()

    lines = source.splitlines(keepends=True)
    tree = ast.parse(source)

    target_func = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "execute_rendering_pipeline":
            target_func = node
            break

    if target_func is None:
        print("Error: 'execute_rendering_pipeline' function app.py mein nahi mili.")
        return

    start_line = target_func.lineno - 1
    end_line = target_func.end_lineno

    # Replace function code
    new_lines = lines[:start_line] + [NEW_FUNCTION_CODE + "\n\n"] + lines[end_line:]
    updated_source = "".join(new_lines)

    # Ensure required imports are present at top
    if "run_integrated_short_pipeline" not in updated_source:
        updated_source = IMPORTS_CODE + "\n" + updated_source

    with open(APP_FILE, "w", encoding="utf-8") as f:
        f.write(updated_source)

    print("[2/3] Imports & execute_rendering_pipeline function replaced.")
    print("[3/3] SUCCESS: app.py fully update ho gayi hai!")

if __name__ == "__main__":
    apply_patch()