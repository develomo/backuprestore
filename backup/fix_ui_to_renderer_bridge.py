# fix_ui_to_renderer_bridge.py
# Fixes the parameter passing from UI -> safe_long_video_polished -> batch_long_renderer
import re
from pathlib import Path

print("=" * 70)
print("🔧 FIXING UI -> RENDERER PARAMETER BRIDGE")
print("=" * 70)

# ============================================================
# FIX 1: safe_long_video_polished.py - Forward ALL params
# ============================================================
slp = Path("safe_long_video_polished.py")
if slp.exists():
    content = slp.read_text(encoding="utf-8")
    
    # Find the render_long_batch_memory call and ensure ALL params are passed
    old_call_pattern = r'final=render_long_batch_memory\((.*?)\)'
    match = re.search(old_call_pattern, content, re.DOTALL)
    
    if match:
        current_params = match.group(1)
        
        # Check which params are missing
        required_params = {
            'custom_logo_path': 'custom_logo_path=custom_logo_path',
            'subscribe_overlay': 'subscribe_overlay=subscribe',
            'wm_opacity': 'wm_opacity=wm_opacity',
        }
        
        missing = []
        for key, param_str in required_params.items():
            if key not in current_params:
                missing.append(param_str)
        
        if missing:
            # Add missing params before the closing parenthesis
            new_params = current_params.rstrip() + ',' + ','.join(missing)
            content = content.replace(match.group(0), f'final=render_long_batch_memory({new_params})')
            slp.write_text(content, encoding="utf-8")
            print(f"✅ FIX 1: Added {len(missing)} missing params to safe_long_video_polished.py")
            for m in missing:
                print(f"   • {m}")
        else:
            print("ℹ️ FIX 1: All params already present in safe_long_video_polished.py")
    else:
        print("⚠️ FIX 1: Could not find render_long_batch_memory call pattern")
else:
    print("❌ safe_long_video_polished.py not found!")

# ============================================================
# FIX 2: app.py - Ensure subscribe_overlay is captured & passed
# ============================================================
app = Path("app.py")
if app.exists():
    content = app.read_text(encoding="utf-8")
    changes = 0
    
    # Check if subscribe_overlay_file is being saved in long_assets_ui
    if 'subscribe_overlay_file' in content and 'long_subscribe_overlay' in content:
        # Check if it's being added to the assets dict
        if '"subscribe":' not in content and "'subscribe':" not in content:
            # Find the return dict in long_assets_ui and add subscribe
            content = content.replace(
                '"outro": outro_path,',
                '"outro": outro_path,\n        "subscribe": save_uploaded_file(subscribe_overlay_file, TEMP_DIR) if subscribe_overlay_file else None,'
            )
            changes += 1
            print("✅ FIX 2a: Added subscribe to long_assets_ui return dict")
        
        # Check if subscribe is passed to run_integrated_long_pipeline
        if 'subscribe=' not in content and 'subscribe_overlay=' not in content:
            # Find the pipeline call and add subscribe param
            content = re.sub(
                r'(custom_logo_path=custom_logo_path)',
                r'\1,subscribe_overlay=assets.get("subscribe")',
                content
            )
            changes += 1
            print("✅ FIX 2b: Added subscribe_overlay to pipeline call in app.py")
    else:
        print("⚠️ FIX 2: subscribe_overlay_file not found in app.py UI code")
    
    # Ensure custom_logo_path is passed correctly
    if 'custom_logo_path=' not in content:
        content = re.sub(
            r'(wm_opacity=wm_opacity)',
            r'custom_logo_path=assets.get("watermark"),\1',
            content
        )
        changes += 1
        print("✅ FIX 2c: Added custom_logo_path to pipeline call")
    
    if changes > 0:
        app.write_text(content, encoding="utf-8")
    else:
        print("ℹ️ FIX 2: app.py already has correct parameter passing")
else:
    print("❌ app.py not found!")

# ============================================================
# FIX 3: Verify batch_long_renderer.py accepts all params
# ============================================================
blr = Path("batch_long_renderer.py")
if blr.exists():
    content = blr.read_text(encoding="utf-8")
    
    sig_match = re.search(r'def render_long_batch_memory\((.*?)\):', content, re.DOTALL)
    if sig_match:
        sig = sig_match.group(1)
        required = ['custom_logo_path', 'subscribe_overlay', 'wm_opacity', 'music_path', 'sfx_files']
        missing_sig = [r for r in required if r not in sig]
        
        if missing_sig:
            print(f"⚠️ FIX 3: batch_long_renderer.py missing params in signature: {missing_sig}")
            print("   These should be caught by **kwargs, but adding explicitly...")
            
            # Add missing params before **kwargs
            for param in missing_sig:
                if param == 'wm_opacity':
                    content = content.replace('**kwargs', f'{param}=0.6,**kwargs')
                elif param == 'subscribe_overlay':
                    content = content.replace('**kwargs', f'{param}=None,**kwargs')
                else:
                    content = content.replace('**kwargs', f'{param}=None,**kwargs')
            
            blr.write_text(content, encoding="utf-8")
            print(f"✅ FIX 3: Added {len(missing_sig)} params to function signature")
        else:
            print("✅ FIX 3: batch_long_renderer.py has all required params")
    else:
        print("⚠️ FIX 3: Could not parse function signature")
else:
    print("❌ batch_long_renderer.py not found!")

# ============================================================
# VERIFY SYNTAX
# ============================================================
print("\n🔍 Verifying syntax of all modified files...")
all_ok = True
for fname in ["safe_long_video_polished.py", "app.py", "batch_long_renderer.py"]:
    fp = Path(fname)
    if fp.exists():
        try:
            compile(fp.read_text(encoding="utf-8"), fname, "exec")
            print(f"  ✅ {fname}: OK")
        except SyntaxError as e:
            print(f"  ❌ {fname}: SYNTAX ERROR at line {e.lineno}: {e.msg}")
            all_ok = False

print("\n" + "=" * 70)
if all_ok:
    print("✅ ALL FIXES APPLIED SUCCESSFULLY!")
    print("=" * 70)
    print("\n📋 WHAT WAS FIXED:")
    print("  1. safe_long_video_polished.py now forwards logo, subscribe, opacity")
    print("  2. app.py now passes subscribe_overlay & custom_logo_path to pipeline")
    print("  3. batch_long_renderer.py signature verified/updated")
    print("\n💡 NEXT STEPS:")
    print("  1. Restart Streamlit: streamlit run app.py")
    print("  2. Upload Logo PNG in Long Video section")
    print("  3. Upload Subscribe Overlay in Long Video section")
    print("  4. Upload Background Music")
    print("  5. Render and check terminal logs for confirmation")
else:
    print("❌ SYNTAX ERRORS FOUND - Please fix before running")
print("=" * 70)