# fix_logo_subscribe_outro_final.py
# FINAL COMPREHENSIVE FIX: Logo Watermark + Subscribe Overlay + Outro
import re
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent

def backup_file(filepath):
    if filepath.exists():
        backup = filepath.with_suffix(filepath.suffix + ".backup_final_all")
        if not backup.exists():
            shutil.copy2(filepath, backup)
            print(f"[OK] Backup created: {backup.name}")

def fix_logo_watermark():
    """Fix Logo Watermark: Add custom_logo_path and wm_opacity to safe_long_video_polished.py"""
    filepath = BASE_DIR / "safe_long_video_polished.py"
    if not filepath.exists():
        print(f"[SKIP] {filepath.name} not found")
        return False
    
    backup_file(filepath)
    content = filepath.read_text(encoding="utf-8")
    lines = content.split('\n')
    
    # FIX 1: Add custom_logo_path and wm_opacity to function signature
    signature_found = False
    for i, line in enumerate(lines):
        if 'def run_integrated_long_pipeline(' in line and 'voice_path=None' in line:
            # Check if custom_logo_path already exists
            if 'custom_logo_path' not in line:
                # Find the end of the signature (line ending with **kwargs):
                for j in range(i, min(i + 10, len(lines))):
                    if '**kwargs):' in lines[j]:
                        # Add parameters before **kwargs
                        lines[j] = lines[j].replace('**kwargs):', 'custom_logo_path=None,wm_opacity=0.6,**kwargs):')
                        signature_found = True
                        print(f"[OK] Patch 1: Added custom_logo_path and wm_opacity to function signature (line {j+1})")
                        break
            else:
                print("[INFO] Patch 1: custom_logo_path already in signature")
                signature_found = True
            break
    
    if not signature_found:
        print("[WARN] Could not add parameters to function signature")
    
    # FIX 2: Pass custom_logo_path and wm_opacity to render_long_batch_memory
    render_call_found = False
    for i, line in enumerate(lines):
        if 'final=render_long_batch_memory(' in line:
            # Check if custom_logo_path already passed
            if 'custom_logo_path=custom_logo_path' not in line:
                # Find the end of the call (line ending with preset_overrides=preset))
                for j in range(i, min(i + 15, len(lines))):
                    if 'preset_overrides=preset)' in lines[j]:
                        # Add parameters before preset_overrides
                        lines[j] = lines[j].replace(
                            'preset_overrides=preset)',
                            'preset_overrides=preset,custom_logo_path=custom_logo_path,wm_opacity=wm_opacity)'
                        )
                        render_call_found = True
                        print(f"[OK] Patch 2: Passing custom_logo_path and wm_opacity to renderer (line {j+1})")
                        break
            else:
                print("[INFO] Patch 2: custom_logo_path already passed to renderer")
                render_call_found = True
            break
    
    if not render_call_found:
        print("[WARN] Could not pass parameters to renderer")
    
    # Write back
    new_content = '\n'.join(lines)
    filepath.write_text(new_content, encoding="utf-8")
    
    return signature_found and render_call_found

def fix_subscribe_overlay():
    """Fix Subscribe Overlay: Ensure bottom-right corner"""
    filepath = BASE_DIR / "batch_long_renderer.py"
    if not filepath.exists():
        print(f"[SKIP] {filepath.name} not found")
        return False
    
    backup_file(filepath)
    content = filepath.read_text(encoding="utf-8")
    
    # Check if already patched
    if 'corner="bottom-right"' in content:
        print("[OK] Patch 3: Subscribe overlay already set to bottom-right")
        return True
    
    # Replace top-right with bottom-right
    old_call = 'corner="top-right"'
    new_call = 'corner="bottom-right"'
    
    if old_call in content:
        content = content.replace(old_call, new_call)
        filepath.write_text(content, encoding="utf-8")
        print("[OK] Patch 3: Subscribe overlay moved to bottom-right")
        return True
    else:
        print("[WARN] Could not find subscribe overlay corner parameter")
        return False

def fix_outro():
    """Fix Outro: Ensure it's properly appended"""
    filepath = BASE_DIR / "batch_long_renderer.py"
    if not filepath.exists():
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # Check if outro append logic exists
    if 'outputs.append(outro_out)' in content:
        print("[OK] Patch 4: Outro append logic verified")
        return True
    else:
        print("[WARN] Outro append logic might be missing")
        return False

def verify_all_fixes():
    """Verify all fixes are applied"""
    print("\n" + "="*60)
    print("VERIFYING ALL FIXES")
    print("="*60)
    
    # Check safe_long_video_polished.py
    safe_long = BASE_DIR / "safe_long_video_polished.py"
    if safe_long.exists():
        content = safe_long.read_text(encoding="utf-8")
        
        checks = [
            ("custom_logo_path=None", "Logo parameter in signature"),
            ("wm_opacity=0.6", "Opacity parameter in signature"),
            ("custom_logo_path=custom_logo_path", "Logo passed to renderer"),
            ("wm_opacity=wm_opacity", "Opacity passed to renderer"),
        ]
        
        passed = 0
        for check_str, label in checks:
            if check_str in content:
                print(f"  ✅ {label}")
                passed += 1
            else:
                print(f"  ❌ {label}")
        
        print(f"\n📊 {passed}/{len(checks)} logo fixes verified")
    
    # Check batch_long_renderer.py
    batch_renderer = BASE_DIR / "batch_long_renderer.py"
    if batch_renderer.exists():
        content = batch_renderer.read_text(encoding="utf-8")
        
        checks = [
            ('corner="bottom-right"', "Subscribe bottom-right"),
            ('outputs.append(outro_out)', "Outro append"),
        ]
        
        passed = 0
        for check_str, label in checks:
            if check_str in content:
                print(f"  ✅ {label}")
                passed += 1
            else:
                print(f"  ❌ {label}")
        
        print(f"\n📊 {passed}/{len(checks)} subscribe/outro fixes verified")

if __name__ == "__main__":
    print("🚀 Starting FINAL FIX: Logo + Subscribe + Outro...")
    print("="*60)
    
    logo_ok = fix_logo_watermark()
    print()
    
    subscribe_ok = fix_subscribe_overlay()
    print()
    
    outro_ok = fix_outro()
    print()
    
    verify_all_fixes()
    
    print("\n" + "="*60)
    if logo_ok and subscribe_ok and outro_ok:
        print("✅ ALL FIXES APPLIED SUCCESSFULLY!")
    else:
        print("⚠️  SOME FIXES MAY HAVE ISSUES - Check above")
    print("="*60)
    print("\n📋 NEXT STEPS:")
    print("1. Run: streamlit run app.py")
    print("2. Test Long Video with:")
    print("   - Logo watermark (should appear bottom-right)")
    print("   - Subscribe overlay (should appear bottom-right)")
    print("   - Outro (should appear last 2 seconds, silent)")
    print("\n💡 IMPORTANT:")
    print("   - UI mein 'Enable Logo Watermark' checkbox ON karein")
    print("   - Logo upload karein")
    print("   - Subscribe overlay upload karein")
    print("   - Outro upload karein")
    print("   - Video generate karein")