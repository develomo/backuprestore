
import sys
import os
sys.path.insert(0, r"D:\My Creation Video Generator\backup")
os.chdir(r"D:\My Creation Video Generator\backup")

print("Testing imports...")
errors = []

try:
    import safe_long_video_polished
    print("✅ safe_long_video_polished imported")
except Exception as e:
    errors.append(f"safe_long_video_polished: {e}")
    print(f"❌ safe_long_video_polished failed: {e}")

try:
    import batch_long_renderer
    print("✅ batch_long_renderer imported")
except Exception as e:
    errors.append(f"batch_long_renderer: {e}")
    print(f"❌ batch_long_renderer failed: {e}")

try:
    import voice_humanization_orchestrator
    print("✅ voice_humanization_orchestrator imported")
except Exception as e:
    errors.append(f"voice_humanization_orchestrator: {e}")
    print(f"❌ voice_humanization_orchestrator failed: {e}")

try:
    import professional_voice_engine
    print("✅ professional_voice_engine imported")
except Exception as e:
    errors.append(f"professional_voice_engine: {e}")
    print(f"❌ professional_voice_engine failed: {e}")

if errors:
    print(f"\n❌ {len(errors)} module(s) failed to import")
    sys.exit(1)
else:
    print("\n✅ All critical modules imported successfully!")
    sys.exit(0)
