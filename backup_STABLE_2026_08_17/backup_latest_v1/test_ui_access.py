# test_ui_access.py
# UI ACCESS VERIFICATION - Check if all functions are accessible from UI
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent

def verify_ui_access():
    """Verify that all required UI controls exist in app.py"""
    filepath = BASE_DIR / "app.py"
    if not filepath.exists():
        print(f"❌ {filepath.name} not found")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    print("=" * 70)
    print("🔍 VERIFYING UI ACCESS FOR LONG VIDEO FEATURES")
    print("=" * 70)
    
    checks = [
        # Long Video Assets Section
        ("Long Video Assets", "Long Video Assets section title"),
        ("Voice Upload", "Voice upload control"),
        ("Clips Upload", "Clips upload control"),
        ("BG Music Upload", "Background music upload"),
        ("SFX Upload", "SFX upload control"),
        ("Intro Overlay", "Intro overlay upload"),
        ("Outro Overlay", "Outro overlay upload"),
        ("Subscribe Overlay", "Subscribe overlay upload"),
        
        # Logo Watermark (NEW - needs to be added)
        ("Long Video Logo Watermark", "Logo watermark section title"),
        ("Enable Logo Watermark", "Logo watermark checkbox"),
        ("Upload Logo", "Logo upload button"),
        ("Watermark Opacity", "Opacity slider"),
        
        # Caption Settings
        ("Enable Long Video Captions", "Caption toggle checkbox"),
        
        # Backend Wiring
        ("custom_logo_path", "Logo path passed to backend"),
        ("wm_opacity", "Watermark opacity passed to backend"),
        ("intro_path", "Intro path passed to backend"),
        ("outro_path", "Outro path passed to backend"),
        ("subscribe_overlay", "Subscribe overlay passed to backend"),
    ]
    
    passed = 0
    failed = []
    
    for check_str, label in checks:
        if check_str in content:
            print(f"✅ {label:50s} : FOUND")
            passed += 1
        else:
            print(f"❌ {label:50s} : MISSING")
            failed.append(label)
    
    print("\n" + "=" * 70)
    print(f"📊 {passed}/{len(checks)} UI controls verified")
    print("=" * 70)
    
    if failed:
        print("\n⚠️  MISSING UI CONTROLS:")
        for label in failed:
            print(f"   - {label}")
        print("\n💡 These controls need to be added to app.py")
        return False
    else:
        print("\n✅ ALL UI CONTROLS ARE ACCESSIBLE!")
        return True

def check_long_assets_function():
    """Check if long_assets function properly handles UI uploads"""
    filepath = BASE_DIR / "app.py"
    if not filepath.exists():
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    print("\n" + "=" * 70)
    print("🔍 CHECKING LONG ASSETS FUNCTION")
    print("=" * 70)
    
    # Check if long_assets function exists
    if "def long_assets(" not in content:
        print("❌ long_assets function not found")
        return False
    
    print("✅ long_assets function found")
    
    # Check if it uses upload_single and upload_multi
    if "upload_single" in content and "upload_multi" in content:
        print("✅ UI upload functions are used")
    else:
        print("❌ UI upload functions not properly used")
        return False
    
    # Check if assets dictionary is properly built
    if '"voice": voice' in content and '"clips": clips' in content:
        print("✅ Assets dictionary properly built")
    else:
        print("❌ Assets dictionary not properly built")
        return False
    
    # Check if watermark data is included
    if '"wm_logo"' in content or '"custom_logo_path"' in content:
        print("✅ Watermark data included in assets")
    else:
        print("⚠️  Watermark data not included in assets (needs to be added)")
    
    return True

def check_build_render_kwargs():
    """Check if build_render_kwargs properly passes all assets"""
    filepath = BASE_DIR / "app.py"
    if not filepath.exists():
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    print("\n" + "=" * 70)
    print("🔍 CHECKING BUILD_RENDER_KWARGS FUNCTION")
    print("=" * 70)
    
    # Check if function exists
    if "def build_render_kwargs(" not in content:
        print("❌ build_render_kwargs function not found")
        return False
    
    print("✅ build_render_kwargs function found")
    
    # Check if LONG mode assets are passed
    long_mode_checks = [
        ('"intro_path"', "Intro path"),
        ('"outro_path"', "Outro path"),
        ('"subscribe_overlay"', "Subscribe overlay"),
    ]
    
    passed = 0
    for check_str, label in long_mode_checks:
        if check_str in content:
            print(f"✅ {label} passed to backend")
            passed += 1
        else:
            print(f"❌ {label} not passed to backend")
    
    # Check if watermark is passed
    if '"custom_logo_path"' in content or '"wm_logo"' in content:
        print("✅ Custom logo path passed to backend")
        passed += 1
    else:
        print("⚠️  Custom logo path not passed to backend (needs to be added)")
    
    print(f"\n📊 {passed}/{len(long_mode_checks) + 1} backend parameters verified")
    return passed >= len(long_mode_checks)

if __name__ == "__main__":
    print("🚀 Starting UI Access Verification...")
    print()
    
    ui_ok = verify_ui_access()
    long_assets_ok = check_long_assets_function()
    kwargs_ok = check_build_render_kwargs()
    
    print("\n" + "=" * 70)
    print("📋 FINAL VERDICT")
    print("=" * 70)
    
    if ui_ok and long_assets_ok and kwargs_ok:
        print("✅ ALL UI CONTROLS ARE PROPERLY ACCESSIBLE!")
        print("\n📋 NEXT STEPS:")
        print("1. Run: streamlit run app.py")
        print("2. Test Long Video section")
        print("3. Verify all upload controls are visible")
        print("4. Upload test files and render")
    else:
        print("⚠️  SOME UI CONTROLS ARE MISSING OR NOT PROPERLY WIRED")
        print("\n💡 NEXT STEPS:")
        print("1. Add missing UI controls to app.py")
        print("2. Ensure backend wiring is correct")
        print("3. Re-run this verification script")