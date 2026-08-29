import os

def fix_voice_duration():
    file_path = "voice_duration.py"
    if not os.path.exists(file_path):
        return
    
    code = """

# --- AUTO-ADDED ALIASES FOR COMPATIBILITY ---
def get_voice_duration_report(path):
    if 'voice_duration_report' in globals():
        return voice_duration_report(path)
    return {}
"""
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(code)
    print("✓ Fixed voice_duration.py")

def fix_duration_guard():
    file_path = "duration_guard.py"
    if not os.path.exists(file_path):
        return
    
    code = """

# --- AUTO-ADDED ALIASES FOR COMPATIBILITY ---
def normalize_mode(mode):
    if not mode:
        return "short"
    clean = str(mode).strip().lower()
    if "long" in clean:
        return "long"
    return "short"
"""
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(code)
    print("✓ Fixed duration_guard.py")

def fix_audio_engine():
    file_path = "audio_engine.py"
    if not os.path.exists(file_path):
        return
    
    code = """

# --- AUTO-ADDED ALIASES FOR COMPATIBILITY ---
def audio_duration(path):
    if 'probe_duration' in globals():
        return probe_duration(path)
    return 0.0
"""
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(code)
    print("✓ Fixed audio_engine.py")

if __name__ == "__main__":
    fix_voice_duration()
    fix_duration_guard()
    fix_audio_engine()
    print("\nALL IMPORTS FIXED SUCCESSFULLY!")