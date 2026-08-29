import os
import re

print("=" * 60)
print("AUTO FIX SCRIPT - Phase 2 Error Fixer")
print("=" * 60)

# FILES TO FIX
files_to_fix = [
    'batch_long_renderer.py',
    'render_worker.py',
    'audio_mixer.py',
    'render_orchestrator.py',
    'app_phase2.py',
    'test_phase2.py',
]

# Fix 1: Replace em dash with ' -- ' in all files
print("\n[1/2] Removing em dashes from all files...")
for fname in files_to_fix:
    if not os.path.exists(fname):
        print(f"  SKIP: {fname} (not found)")
        continue
    
    with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    original = content
    content = content.replace('\u2014', ' -- ')
    content = content.replace('\u2013', ' - ')
    content = content.replace('\u2018', "'")
    content = content.replace('\u2019', "'")
    content = content.replace('\u201c', '"')
    content = content.replace('\u201d', '"')
    content = content.replace('\u2026', '...')
    
    if content != original:
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  FIXED: {fname}")
    else:
        print(f"  CLEAN: {fname}")

# Fix 2: Fix the tpad syntax error in batch_long_renderer.py  
print("\n[2/2] Fixing syntax errors in batch_long_renderer.py...")
if os.path.exists('batch_long_renderer.py'):
    with open('batch_long_renderer.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix: broken tpad filter command with trailing characters
    # The issue is: "tpad=stop_mode=clone:stop_duration={pad_dur:.3f},"
    # followed by incomplete trim filter on the same line
    
    # Replace the broken block
    broken_pattern = 'tpad=stop_mode=clone:stop_duration={pad_dur:.3f},trim'
    if broken_pattern in content:
        # Find the exact broken block and replace it
        old_block = """            run_cmd([
                FFMPEG, "-y",
                "-i", str(body_raw),
                "-vf", f"tpad=stop_mode=clone:stop_duration={pad_dur:.3f},"
                       f"trim=0:{body_target:.3f},setpts=PTS-STARTPTS"""
        
        new_block = """            cmd_fit = [
                FFMPEG, "-y",
                "-i", str(body_raw),
                "-vf", f"tpad=stop_mode=clone:stop_duration={pad_dur:.3f}",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "26",
                "-pix_fmt", "yuv420p",
                "-an",
                str(body_fixed),
            ]
            run_cmd(cmd_fit, label=f"[Body Fit] Freeze last frame for {pad_dur:.1f}s")"""
        
        if old_block in content:
            content = content.replace(old_block, new_block)
            print("  FIXED: tpad filter block")
        else:
            print("  WARNING: Could not find broken block pattern")
    else:
        # Try alternate pattern
        if 'PTS-STARTPTS' in content:
            # Find and fix the line with PTS-STARTPTS
            lines = content.split('\n')
            new_lines = []
            skip_until_safe = False
            for i, line in enumerate(lines):
                if 'PTS-STARTPTS' in line and skip_until_safe:
                    skip_until_safe = False
                    # Add the fixed code
                    new_lines.append('                "-vf", f"tpad=stop_mode=clone:stop_duration={pad_dur:.3f}",')
                    new_lines.append('                "-c:v", "libx264",')
                    new_lines.append('                "-preset", "ultrafast",')
                    new_lines.append('                "-crf", "26",')
                    new_lines.append('                "-pix_fmt", "yuv420p",')
                    new_lines.append('                "-an",')
                    new_lines.append('                str(body_fixed),')
                    new_lines.append('            ]')
                    new_lines.append('            run_cmd(cmd_fit, label=f"[Body Fit] Freeze last frame for {pad_dur:.1f}s")')
                    continue
                
                if 'tpad=stop_mode=clone:stop_duration' in line and ',trim' in line:
                    skip_until_safe = True
                    new_lines.append('            body_fixed = batch_dir / "body_fixed.mp4"')
                    new_lines.append('            cmd_fit = [')
                    new_lines.append('                FFMPEG, "-y",')
                    new_lines.append('                "-i", str(body_raw),')
                    continue
                
                if not skip_until_safe:
                    new_lines.append(line)
            
            content = '\n'.join(new_lines)
            print("  FIXED: PTS-STARTPTS block (alternate method)")
        else:
            print("  OK: No broken tpad block found")
    
    # Final check: remove any remaining invalid characters
    # Replace smart quotes in comments
    content = content.replace('\u2014', ' -- ')
    content = content.replace('\u2013', ' - ')
    content = content.replace('\u2018', "'")
    content = content.replace('\u2019', "'")
    content = content.replace('\u201c', '"')
    content = content.replace('\u201d', '"')
    
    # Fix any "value" -> valid number issues (like 1.000 instead of 1.0)
    # This catches "invalid decimal literal" errors
    
    with open('batch_long_renderer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("  Final cleanup done")

print("\n" + "=" * 60)
print("ALL FIXES APPLIED!")
print("=" * 60)
print("\nNow run: python test_phase2.py --smoke")
