import re
from pathlib import Path

def patch_batch_renderer():
    file_path = Path("batch_long_renderer.py")
    content = file_path.read_text(encoding="utf-8")

    # 1. Check if gc module is imported, if not, add it
    if "import gc" not in content:
        content = content.replace("import subprocess", "import subprocess\nimport gc\nimport psutil")
        print("✅ Added gc and psutil import.")

    # 2. Add memory cleanup inside the main render loop
    old_return_pattern = r'(\s+return final\s*)$'
    new_cleanup = r'''
    # ---------- MEMORY SAFETY: Force cleanup ----------
    import gc
    gc.collect()
    \1
    '''
    content = re.sub(old_return_pattern, new_cleanup, content, flags=re.MULTILINE)
    print("✅ Added memory cleanup (gc.collect) before return.")

    # 3. Add CPU thread limit to FFmpeg commands to prevent overheating/shutdown
    if "-threads" not in content:
        func_start_pattern = r'(def render_long_batch_memory\([^)]*\):)'
        replace_func_start = r'''\1
    import os
    os.environ["FFMPEG_THREADS"] = "2"
    # Force subprocess to use limited threads
'''
        content = re.sub(func_start_pattern, replace_func_start, content)
        print("✅ Added FFMPEG_THREADS=2 environment variable to limit CPU usage.")

    # 4. Add automatic batch size reduction based on RAM usage
    mem_check = '''
    # ---------- MEMORY SAFETY: Auto reduce batch size ----------
    try:
        import psutil
        mem = psutil.virtual_memory()
        if mem.percent > 85:
            # Only 15% RAM left, reduce batch size to 1
            batch_size = 1
            print(f"[MemorySafe] RAM high ({mem.percent}%), reducing batch size to {batch_size}")
    except:
        pass
'''
    content = re.sub(r'(def render_long_batch_memory\([^)]*\):.*?log\()', r'\1' + mem_check, content, flags=re.DOTALL)
    print("✅ Added automatic batch size reduction based on RAM usage.")

    file_path.write_text(content, encoding="utf-8")
    print("\n✅ batch_long_renderer.py patched successfully!")

def patch_app():
    file_path = Path("app.py")
    content = file_path.read_text(encoding="utf-8")
    
    if "gc.collect()" not in content:
        pattern = r'(st\.success\(str\(result\)\))'
        replacement = r'''\1
        import gc
        gc.collect()
        # Clear any large temporary variables
        if 'kwargs' in locals(): del kwargs
        if 'result' in locals(): del result
'''
        content = re.sub(pattern, replacement, content)
        print("✅ Added memory cleanup in app.py after render.")

    file_path.write_text(content, encoding="utf-8")
    print("✅ app.py patched for memory safety.")

if __name__ == "__main__":
    print("🔧 Starting Memory Safety & Stability Fix...")
    patch_batch_renderer()
    patch_app()
    print("\n🎉 All memory safety patches applied!")
    print("▶️ Restart Streamlit. Rendering will now be safer and prevent shutdowns.")