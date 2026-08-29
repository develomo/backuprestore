# test_ram_safety.py
# Test RAM safety before running long video render
import psutil
import time
import subprocess
import gc

def check_ram_status():
    mem = psutil.virtual_memory()
    print("=" * 60)
    print("🔍 RAM STATUS CHECK")
    print("=" * 60)
    print(f"Total RAM: {mem.total / (1024**3):.2f} GB")
    print(f"Used RAM: {mem.used / (1024**3):.2f} GB ({mem.percent}%)")
    print(f"Available RAM: {mem.available / (1024**3):.2f} GB")
    try:
        swap = psutil.swap_memory()
        print(f"Swap Used: {swap.used / (1024**3):.2f} GB / {swap.total / (1024**3):.2f} GB")
    except Exception:
        print("Swap Used: N/A")
    print("=" * 60)
    
    if mem.percent >= 80:
        print("⚠️  WARNING: RAM usage is HIGH!")
        print("💡 Recommendation: Close other applications before rendering")
        print("   - Close browser tabs")
        print("   - Close video editors")
        print("   - Close other Python processes")
    elif mem.percent >= 70:
        print("⚠️  CAUTION: RAM usage is moderate")
        print("💡 Phase 5 will automatically reduce batch_size to 1")
    else:
        print("✅ RAM usage is SAFE for rendering")
    
    # Check for zombie FFmpeg processes
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq ffmpeg.exe"],
            capture_output=True, text=True, timeout=5
        )
        if "ffmpeg.exe" in result.stdout:
            print("\n⚠️  Zombie FFmpeg processes detected!")
            print("💡 Killing them to free RAM...")
            subprocess.run(["taskkill", "/F", "/IM", "ffmpeg.exe"], 
                          capture_output=True, timeout=10)
            print("✅ Zombie processes killed")
            gc.collect()
            time.sleep(2)
            mem2 = psutil.virtual_memory()
            print(f"✅ RAM after cleanup: {mem2.percent}%")
    except Exception as e:
        print(f"Could not check FFmpeg processes: {e}")
    
    print("\n" + "=" * 60)
    print("📋 PHASE 5 SAFETY FEATURES ACTIVE:")
    print("  ✓ RAM guard at 70% (was 80%)")
    print("  ✓ Critical ceiling at 78% (was 90%)")
    print("  ✓ Batch size capped at 2 (was 8)")
    print("  ✓ FFmpeg threads = 1 (was 2)")
    print("  ✓ Force GC after every batch")
    print("  ✓ Zombie FFmpeg killer active")
    print("  ✓ 1.5s pause between batches")
    print("  ✓ Pre-render RAM check")
    print("=" * 60)

if __name__ == "__main__":
    check_ram_status()
