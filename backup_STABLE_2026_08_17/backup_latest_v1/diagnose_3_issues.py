# diagnose_3_issues.py
# Diagnoses why Logo, Subscribe Overlay, and Outro are not showing in video
import json
import re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs"

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_latest_render_report():
    """Find and analyze the latest render report JSON."""
    print_header("1. LATEST RENDER REPORT ANALYSIS")
    
    reports = list(OUTPUT_DIR.glob("final_long_stable_*.stable_report.json"))
    if not reports:
        print("❌ No render reports found. Run a render first.")
        return None
    
    latest = max(reports, key=lambda p: p.stat().st_mtime)
    print(f"📄 Latest report: {latest.name}")
    print(f"📅 Modified: {datetime.fromtimestamp(latest.stat().st_mtime)}")
    
    try:
        data = json.loads(latest.read_text(encoding="utf-8"))
        
        print("\n🔍 KEY FIELDS:")
        print(f"   intro_used:           {data.get('intro_used')}")
        print(f"   outro_asset_type:     {data.get('outro_asset_type')}")
        print(f"   outro_seconds:        {data.get('outro_seconds')}")
        print(f"   subscribe_shown:      {data.get('subscribe_overlay_shown')}")
        print(f"   subscribe_duration:   {data.get('subscribe_overlay_duration_actual')}s")
        print(f"   custom_logo_used:     {data.get('custom_logo_used')}")
        print(f"   total_duration:       {data.get('total_duration')}s")
        print(f"   clips_rendered:       {data.get('clips_rendered')}")
        
        return data
    except Exception as e:
        print(f"❌ Failed to parse report: {e}")
        return None

def check_assets_folders():
    """Check if assets exist in the long video folders."""
    print_header("2. ASSETS FOLDERS CHECK")
    
    folders = {
        "Intro": BASE_DIR / "assets" / "long" / "intro",
        "Outro": BASE_DIR / "assets" / "long" / "outro",
        "Subscribe": BASE_DIR / "assets" / "long" / "overlays",
        "Logo (custom)": BASE_DIR / "assets" / "long" / "watermark",
        "Logo (default)": BASE_DIR / "assets" / "logos",
    }
    
    for name, folder in folders.items():
        if folder.exists():
            files = [f for f in folder.iterdir() if f.is_file()]
            if files:
                print(f"✅ {name:20s} : {len(files)} file(s) found")
                for f in files[:3]:
                    print(f"      - {f.name} ({f.stat().st_size} bytes)")
            else:
                print(f"⚠️  {name:20s} : FOLDER EMPTY")
        else:
            print(f"❌ {name:20s} : FOLDER MISSING ({folder})")

def check_app_py_patches():
    """Verify that app.py has all required patches."""
    print_header("3. APP.PY PATCH VERIFICATION")
    
    app_file = BASE_DIR / "app.py"
    if not app_file.exists():
        print("❌ app.py not found")
        return
    
    content = app_file.read_text(encoding="utf-8")
    
    checks = [
        ("custom_logo_path", "Logo watermark parameter in build_render_kwargs"),
        ("wm_logo", "Watermark logo from UI assets"),
        ("wm_opacity", "Watermark opacity slider"),
        ("Enable Logo Watermark", "Logo watermark UI checkbox"),
        ("Enable Long Video Captions", "Caption toggle UI checkbox"),
        ("long_enable_wm", "Watermark checkbox session key"),
        ("subscribe_overlay", "Subscribe overlay passed to backend"),
        ("outro_path", "Outro path passed to backend"),
    ]
    
    for check_str, label in checks:
        if check_str in content:
            print(f"✅ {label:50s} : FOUND")
        else:
            print(f"❌ {label:50s} : MISSING")

def check_batch_renderer_patches():
    """Verify that batch_long_renderer.py has all required patches."""
    print_header("4. BATCH_LONG_RENDERER.PY PATCH VERIFICATION")
    
    renderer_file = BASE_DIR / "batch_long_renderer.py"
    if not renderer_file.exists():
        print("❌ batch_long_renderer.py not found")
        return
    
    content = renderer_file.read_text(encoding="utf-8")
    
    checks = [
        ('corner="bottom-right"', "Subscribe overlay bottom-right position"),
        ('corner="top-right"', "Subscribe overlay top-right position (OLD)"),
        ("custom_logo_path", "Custom logo parameter in render function"),
        ("resolve_watermark_path", "Watermark path resolver function"),
        ("apply_niche_watermark", "Watermark application function"),
        ("outputs.append(outro_out)", "Outro appended to outputs list"),
        ("resolve_outro_segment", "Outro segment resolver function"),
        ("generate_fallback_outro_card", "Fallback outro card generator"),
        ("apply_subscribe_overlay_reliable", "Subscribe overlay function"),
        ("subscribe_overlay_shown", "Subscribe shown report field"),
        ("exclude_after_seconds", "Watermark excluded during outro"),
    ]
    
    for check_str, label in checks:
        if check_str in content:
            print(f"✅ {label:50s} : FOUND")
        else:
            print(f"❌ {label:50s} : MISSING")

def check_safe_long_controller():
    """Verify that safe_long_video_polished.py passes all parameters."""
    print_header("5. SAFE_LONG_VIDEO_POLISHED.PY CHECK")
    
    controller_file = BASE_DIR / "safe_long_video_polished.py"
    if not controller_file.exists():
        print("❌ safe_long_video_polished.py not found")
        return
    
    content = controller_file.read_text(encoding="utf-8")
    
    checks = [
        ("custom_logo_path", "Custom logo path passed to renderer"),
        ("wm_opacity", "Watermark opacity passed to renderer"),
        ("outro_path", "Outro path passed to renderer"),
        ("subscribe_overlay", "Subscribe overlay passed to renderer"),
        ("return bool(add_captions)", "Caption toggle respected"),
        ("FORCED CAPTIONS ON", "FORCED CAPTIONS BUG (should be REMOVED)"),
    ]
    
    for check_str, label in checks:
        if check_str in content:
            if check_str == "FORCED CAPTIONS ON":
                print(f"⚠️  {label:50s} : STILL PRESENT (BUG)")
            else:
                print(f"✅ {label:50s} : FOUND")
        else:
            if check_str == "FORCED CAPTIONS ON":
                print(f"✅ {label:50s} : CORRECTLY REMOVED")
            else:
                print(f"❌ {label:50s} : MISSING")

def analyze_root_causes(report_data):
    """Based on report data, identify root causes."""
    print_header("6. ROOT CAUSE ANALYSIS")
    
    if not report_data:
        print("⚠️  No report data to analyze. Run a render first.")
        return
    
    issues = []
    
    # Logo analysis
    if not report_data.get("custom_logo_used"):
        issues.append({
            "issue": "LOGO NOT SHOWING",
            "possible_causes": [
                "1. UI checkbox 'Enable Logo Watermark' was NOT checked",
                "2. Logo file was NOT uploaded",
                "3. app.py mein custom_logo_path pass nahi ho raha",
                "4. safe_long_video_polished.py custom_logo_path ko renderer tak pass nahi kar raha",
                "5. batch_long_renderer.py mein apply_niche_watermark function call nahi ho raha",
                "6. Logo file invalid hai (corrupt/empty)",
            ]
        })
    else:
        print("✅ Logo was used in last render")
    
    # Subscribe overlay analysis
    if not report_data.get("subscribe_overlay_shown"):
        issues.append({
            "issue": "SUBSCRIBE OVERLAY NOT SHOWING",
            "possible_causes": [
                "1. Subscribe overlay file NOT uploaded",
                "2. Video duration < 8 minutes (overlay only shows 8-9 min)",
                "3. app.py subscribe_overlay parameter pass nahi kar raha",
                "4. batch_long_renderer.py mein apply_subscribe_overlay_reliable call fail",
                "5. Overlay file corrupt ya invalid format",
            ]
        })
    else:
        print(f"✅ Subscribe overlay shown for {report_data.get('subscribe_overlay_duration_actual')}s")
    
    # Outro analysis
    outro_type = report_data.get("outro_asset_type")
    if outro_type == "fallback_generated":
        issues.append({
            "issue": "OUTRO SHOWING AS FALLBACK (NOT YOUR UPLOADED OUTRO)",
            "possible_causes": [
                "1. outro_path parameter renderer tak nahi pahuncha",
                "2. Uploaded outro file path invalid hai",
                "3. app.py outro_path ko assets se correctly nahi le raha",
                "4. safe_long_video_polished.py outro ko renderer tak pass nahi kar raha",
            ]
        })
    elif outro_type == "uploaded":
        print("✅ Uploaded outro was used")
    else:
        issues.append({
            "issue": "OUTRO STATUS UNKNOWN",
            "possible_causes": [
                "Report mein outro_asset_type field missing hai",
            ]
        })
    
    # Print issues
    if issues:
        print(f"\n🚨 {len(issues)} ISSUE(S) DETECTED:\n")
        for i, issue in enumerate(issues, 1):
            print(f"{'─' * 70}")
            print(f"🔴 ISSUE #{i}: {issue['issue']}")
            print(f"{'─' * 70}")
            print("Possible causes:")
            for cause in issue["possible_causes"]:
                print(f"   {cause}")
    else:
        print("\n✅ All 3 features appear to be working correctly in last render!")
        print("   If video still doesn't show them, check the actual output video file.")

def check_output_video():
    """Check if the latest output video exists."""
    print_header("7. OUTPUT VIDEO CHECK")
    
    videos = list(OUTPUT_DIR.glob("final_long_stable_*.mp4"))
    if not videos:
        print("❌ No output videos found")
        return
    
    latest = max(videos, key=lambda p: p.stat().st_mtime)
    size_mb = latest.stat().st_size / (1024 * 1024)
    print(f"📹 Latest video: {latest.name}")
    print(f"📏 Size: {size_mb:.2f} MB")
    print(f"📅 Modified: {datetime.fromtimestamp(latest.stat().st_mtime)}")
    print(f"📂 Path: {latest}")

if __name__ == "__main__":
    print("🔍 DIAGNOSING: Logo, Subscribe Overlay, and Outro Issues")
    print("=" * 70)
    
    report_data = check_latest_render_report()
    check_assets_folders()
    check_app_py_patches()
    check_batch_renderer_patches()
    check_safe_long_controller()
    analyze_root_causes(report_data)
    check_output_video()
    
    print("\n" + "=" * 70)
    print("📋 NEXT STEPS:")
    print("=" * 70)
    print("1. Upar ka output copy karke mujhe bhejo")
    print("2. Main exact root cause ke hisaab se fix dunga")
    print("3. Koi guess-work nahi, sirf facts ke basis par fix")