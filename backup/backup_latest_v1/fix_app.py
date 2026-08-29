import os

with open("app.py", "r", encoding="utf-8") as f:
    code = f.read()

mock_code = """        # Output Copy or Mock Render Creation
        if assets.get("clips") and len(assets["clips"]) > 0:
            shutil.copy(assets["clips"][0], output_file)
        else:
            output_file.touch()"""

real_code = """        # Real Multi-Clip Video Engine Rendering
        from master_pipeline import process_multi_clip_render

        clips = assets.get("clips", [])
        voice = assets.get("voice")

        rendered_path = process_multi_clip_render(clips, voice, str(output_file))

        if not rendered_path or not os.path.exists(rendered_path):
            st.error("❌ Multi-clip rendering failed. Check terminal logs.")
            return None"""

if "shutil.copy(assets[\"clips\"][0], output_file)" in code:
    # Replace mock section
    lines = code.splitlines()
    new_lines = []
    skip = False
    for line in lines:
        if "# Output Copy or Mock Render Creation" in line:
            skip = True
            new_lines.append("        # Real Multi-Clip Video Engine Rendering")
            new_lines.append("        from master_pipeline import process_multi_clip_render")
            new_lines.append("        clips = assets.get('clips', [])")
            new_lines.append("        voice = assets.get('voice')")
            new_lines.append("        rendered_path = process_multi_clip_render(clips, voice, str(output_file))")
            new_lines.append("        if not rendered_path or not os.path.exists(rendered_path):")
            new_lines.append("            st.error('❌ Multi-clip rendering failed. Check terminal logs.')")
            new_lines.append("            return None")
        elif skip and "output_file.touch()" in line:
            skip = False
        elif not skip:
            new_lines.append(line)

    with open("app.py", "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
    print("✅ Successfully updated app.py with real multi-clip engine!")
else:
    print("⚠️ Already updated or mock code pattern not found.")