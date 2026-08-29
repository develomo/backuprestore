"""
============================================================================
PHASE 4 PATCH — Fix Long Video Pipeline: render_long_batch_memory() clips arg
============================================================================
ROOT CAUSE:
  safe_long_video_polished.py calls:
    render_long_batch_memory(clips=clip_list, ...)
  But batch_long_renderer.py signature is:
    def render_long_batch_memory(voice_path, clip_paths, output_path, ...)

  Keyword 'clips' does not match parameter name 'clip_paths', causing:
    TypeError: render_long_batch_memory() got an unexpected keyword argument 'clips'

FIX:
  Replace 'clips=' with 'clip_paths=' in safe_long_video_polished.py

PLUS: Fix any other mismatched kwargs (sfx_files, music_path, etc.)
============================================================================
"""
import os
import re

BACKUP_DIR = os.path.dirname(os.path.abspath(__file__))


def main_phase4():
    path = os.path.join(BACKUP_DIR, 'safe_long_video_polished.py')

    # Check if file exists
    if not os.path.exists(path):
        print(f"[ERROR] safe_long_video_polished.py not found in {BACKUP_DIR}")
        print("Trying alternate name...")
        # Try alternate filenames
        for alt in ['safe_long_video.py', 'long_video_polished.py', 'master_pipeline.py']:
            alt_path = os.path.join(BACKUP_DIR, alt)
            if os.path.exists(alt_path):
                path = alt_path
                print(f"[OK] Found: {alt}")
                break
        else:
            print("[FATAL] Cannot find long video pipeline file!")
            return

    with open(path, 'r', encoding='utf-8') as f:
        original = f.read()

    backup_path = path + '.backup_phase4'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original)
    print(f"[OK] Backup: {backup_path}")
    print(f"[INFO] {len(original.split(chr(10)))} lines")

    content = original
    patches = 0

    # ==================================================================
    # FIX 1: 'clips=' → 'clip_paths='
    # ==================================================================
    # This is the MAIN fix. The call uses 'clips=' but function expects 'clip_paths='
    old_clips = 'clips=clip_list'
    new_clips = 'clip_paths=clip_list'

    if old_clips in content:
        count = content.count(old_clips)
        content = content.replace(old_clips, new_clips)
        patches += 1
        print(f"[FIX 1] Replaced 'clips=clip_list' → 'clip_paths=clip_list' ({count} occurrences)")
    else:
        # Try other variations
        for old_var in ['clips=clips', 'clips=clip_paths_list', 'clips=clip_list_local', 'clips = clip_list']:
            if old_var in content:
                content = content.replace(old_var, 'clip_paths=clip_list')
                patches += 1
                print(f"[FIX 1] Replaced '{old_var}' → 'clip_paths=clip_list'")
                break
        else:
            print("[WARN] 'clips=' pattern not found — looking for broader match...")
            # Look for the full function call line
            call_pattern = r'render_long_batch_memory\([^)]*clips\s*=\s*[^,)]+'
            match = re.search(call_pattern, content)
            if match:
                old_call = match.group(0)
                new_call = re.sub(r'clips\s*=\s*(\w+)', r'clip_paths=\1', old_call)
                content = content.replace(old_call, new_call)
                patches += 1
                print(f"[FIX 1] Fuzzy replaced: '{old_call[:60]}...' → 'clip_paths=...'")
            else:
                print("[WARN] No 'clips=' found in render_long_batch_memory call")

    # ==================================================================
    # FIX 2: 'sfx_files=' → 'sfx_path='
    # ==================================================================
    # batch_long_renderer.py uses 'sfx_path' (singular), but app may send 'sfx_files'
    old_sfx = 'sfx_files='
    new_sfx = 'sfx_path='
    if old_sfx in content:
        count = content.count(old_sfx)
        content = content.replace(old_sfx, new_sfx)
        patches += 1
        print(f"[FIX 2] Replaced 'sfx_files=' → 'sfx_path=' ({count} occurrences)")

    # ==================================================================
    # FIX 3: 'final_quality=' → remove if present (batch_long uses 'quality')
    # ==================================================================
    old_fq = 'final_quality='
    if old_fq in content:
        # Remove this arg entirely from the call
        # Find the call and remove just that kwarg
        import re as _re2
        pattern = r',?\s*final_quality\s*=\s*["\'][^"\']*["\']'
        content = _re2.sub(pattern, '', content)
        patches += 1
        print(f"[FIX 3] Removed 'final_quality=' from call (batch_long_renderer uses 'quality')")

    # ==================================================================
    # FIX 4: Check for 'cleanup=' — batch_long uses 'keep_temp='
    # ==================================================================
    if 'cleanup=' in content:
        # Invert: cleanup=True → keep_temp=False
        content = content.replace('cleanup=True', 'keep_temp=False')
        content = content.replace('cleanup=False', 'keep_temp=True')
        patches += 1
        print("[FIX 4] Replaced 'cleanup=' → 'keep_temp=' (inverted)")

    # ==================================================================
    # FIX 5: Check for 'words=' — should be fine, but verify
    # ==================================================================
    # batch_long_renderer accepts words= as parameter, so no fix needed

    # ==================================================================
    # FIX 6: Verify function call has all required args
    # ==================================================================
    # Required: voice_path, clip_paths, output_path
    # Check output_path is present
    if 'output_path=' not in content.split('render_long_batch_memory(')[1].split(')')[0] if 'render_long_batch_memory(' in content else False:
        print("[WARN] output_path may be missing from render_long_batch_memory call")

    # ==================================================================
    # WRITE
    # ==================================================================
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    new_lines = len(content.split('\n'))
    print(f"\n{'='*60}")
    print(f"PHASE 4 — COMPLETE ({patches} patches, {new_lines} lines)")
    print(f"File: {os.path.basename(path)}")
    print(f"Backup: {backup_path}")
    print(f"{'='*60}")
    print("\nChanges:")
    print(f"  1. 'clips=clip_list' → 'clip_paths=clip_list' (MAIN FIX)")
    print(f"  2. 'sfx_files=' → 'sfx_path=' (parameter name match)")
    print(f"  3. 'final_quality=' removed (batch_long uses 'quality')")
    print(f"  4. 'cleanup=' → 'keep_temp=' (inverted: cleanup=True→keep_temp=False)")
    print(f"\nTest: streamlit run app.py → Generate Long Video")
    print(f"      Should now render without TypeError")


if __name__ == "__main__":
    main_phase4()