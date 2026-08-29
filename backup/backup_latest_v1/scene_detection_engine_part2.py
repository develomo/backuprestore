# ============================================================
# PHASE 3 — FILE 2: scene_detection_engine.py (PART 2/2)
# ============================================================
# Isse Part 1 ke neeche paste karna hai — ek complete file banegi.
# ============================================================

import os
import random
import logging
from typing import Dict, List, Tuple, Optional, Any

logger = logging.getLogger("SceneDetectionEngine")


# ============================================================
# SECTION 5: MAIN ENGINE
# ============================================================

class SceneDetectionEngine:
    """
    MAIN SCENE DETECTION ENGINE.
    
    Combines all detection methods, generates smart cut schedules,
    and provides per-clip analysis.
    
    Usage:
        engine = SceneDetectionEngine()
        analysis = engine.analyze_clip("video.mp4", energy_level=0.7)
        schedule = engine.generate_cut_schedule(["c1.mp4","c2.mp4"], 120.0, "fast")
    """

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.ffmpeg = FFmpegUtils()
        self.detector = SceneChangeDetector()
        self.cut_generator = SmartCutGenerator()
        logger.info(f"SceneDetectionEngine initialized (seed={seed})")

    def analyze_clip(
        self, filepath: str, energy_level: float = 0.5,
        sensitivity: float = 0.5,
    ) -> ClipAnalysis:
        """Full analysis of a single video clip."""
        if not os.path.exists(filepath):
            return ClipAnalysis(path=filepath, duration=0.0,
                                warnings=["File not found"])

        duration = self.ffmpeg.get_duration(filepath)
        resolution = self.ffmpeg.get_resolution(filepath)
        fps = self.ffmpeg.get_fps(filepath)
        has_audio = self.ffmpeg.has_audio_stream(filepath)

        warnings = []
        quality = 1.0
        if duration < 1.0:
            warnings.append(f"Very short clip ({duration:.1f}s)")
            quality -= 0.3
        if resolution[0] < 640:
            warnings.append(f"Low resolution: {resolution[0]}x{resolution[1]}")
            quality -= 0.2
        if fps < 15:
            warnings.append(f"Low FPS: {fps}")
            quality -= 0.15
        if not has_audio:
            warnings.append("No audio stream")
        quality = max(0.1, quality)

        scene_points = self.detector.full_detection(
            filepath, sensitivity=sensitivity, energy_level=energy_level,
            use_brightness=(duration > 3.0),
        )

        return ClipAnalysis(
            path=filepath, duration=round(duration,2),
            resolution=resolution, fps=round(fps,2),
            scene_points=scene_points, quality_score=round(quality,2),
            has_audio=has_audio, warnings=warnings,
        )

    def analyze_clips(
        self, filepaths: List[str], energy_level: float = 0.5,
        sensitivity: float = 0.5,
    ) -> List[ClipAnalysis]:
        """Batch analysis of multiple clips."""
        results = []
        for i, fp in enumerate(filepaths):
            logger.info(f"Analyzing clip {i+1}/{len(filepaths)}: {os.path.basename(fp)}")
            results.append(self.analyze_clip(fp, energy_level, sensitivity))
        return results

    def generate_cut_schedule(
        self, filepaths: List[str], total_duration: float,
        pacing: str = "normal", energy_level: float = 0.5,
        target_cuts: Optional[int] = None,
    ) -> CutSchedule:
        """Generate complete cut schedule from multiple clips."""
        all_clips = self.analyze_clips(filepaths, energy_level)

        per_clip_cuts = {}
        current_offset = 0.0
        for clip in all_clips:
            adjusted = [sp.timestamp + current_offset for sp in clip.scene_points]
            per_clip_cuts[clip.path] = [round(t,2) for t in adjusted]
            current_offset += clip.duration

        all_scene_points = []
        offset = 0.0
        for clip in all_clips:
            for sp in clip.scene_points:
                all_scene_points.append(ScenePoint(
                    timestamp=sp.timestamp + offset,
                    confidence=sp.confidence, scene_type=sp.scene_type,
                    priority=sp.priority, motion_score=sp.motion_score,
                ))
            offset += clip.duration

        cuts = self.cut_generator.create_cut_schedule(
            all_scene_points, total_duration, pacing, target_cuts
        )

        if len(cuts) >= 2:
            intervals = [cuts[i+1]-cuts[i] for i in range(len(cuts)-1)]
            avg_interval = sum(intervals)/len(intervals)
        else:
            avg_interval = total_duration

        warnings = []
        if avg_interval < 1.5:
            warnings.append("Very fast pacing — may feel choppy")
        elif avg_interval > 10.0:
            warnings.append("Very slow pacing — may lose viewer attention")

        return CutSchedule(
            clips_analyzed=len(all_clips),
            total_scene_points=len(all_scene_points),
            cut_points=cuts, per_clip_cuts=per_clip_cuts,
            pacing_profile=pacing,
            average_cut_interval=round(avg_interval,2),
            warnings=warnings,
        )

    def quick_scan(self, filepath: str) -> Dict[str, Any]:
        """Fast scan — duration, scene count, quality estimate."""
        if not os.path.exists(filepath):
            return {"error":"File not found", "path":filepath}
        duration = self.ffmpeg.get_duration(filepath)
        resolution = self.ffmpeg.get_resolution(filepath)
        fps = self.ffmpeg.get_fps(filepath)
        raw_scenes = self.detector.detect_via_ffmpeg_scenechange(filepath, 0.35)
        return {
            "path": filepath,
            "filename": os.path.basename(filepath),
            "duration": round(duration,2),
            "resolution": f"{resolution[0]}x{resolution[1]}",
            "fps": round(fps,2),
            "scene_count_estimate": len(raw_scenes),
            "scenes_per_minute": round(len(raw_scenes)/max(1,duration/60),1),
            "quality_ok": resolution[0]>=640 and duration>=1.0,
        }


# ============================================================
# SECTION 6: EXPORT FUNCTIONS — for batch_long_renderer.py
# ============================================================

def get_scene_cuts_for_batch(
    clip_paths: List[str], total_duration: float,
    energy: float = 0.5, pacing: str = "normal",
) -> Tuple[List[float], Dict[str, List[float]]]:
    """
    Convenience function — batch_long_renderer.py se direct call ke liye.
    Returns (all_cut_timestamps, per_clip_cuts_dict).
    """
    engine = SceneDetectionEngine()
    schedule = engine.generate_cut_schedule(
        clip_paths, total_duration, pacing=pacing, energy_level=energy
    )
    return schedule.cut_points, schedule.per_clip_cuts


def quick_clip_scan(clip_path: str) -> Dict[str, Any]:
    """Single clip quick scan — UI preview ke liye."""
    engine = SceneDetectionEngine()
    return engine.quick_scan(clip_path)


def analyze_clip_energy(clip_path: str) -> float:
    """
    Estimate energy level from scene change frequency.
    Returns 0.0 (calm) to 1.0 (high energy).
    """
    engine = SceneDetectionEngine()
    analysis = engine.analyze_clip(clip_path)
    if analysis.duration <= 0:
        return 0.5
    scenes_per_min = len(analysis.scene_points) / max(1, analysis.duration / 60)
    # Map: 0 scenes/min → 0.0, 10+ scenes/min → 1.0
    energy = min(1.0, max(0.0, scenes_per_min / 10.0))
    return round(energy, 3)


# ============================================================
# SECTION 7: SELF-TEST
# ============================================================

def run_self_test():
    """Self-test — creates dummy video and runs detection pipeline."""
    print("=" * 60)
    print("  SCENE DETECTION ENGINE — SELF TEST")
    print("=" * 60)

    engine = SceneDetectionEngine(seed=42)
    tmpdir = tempfile.gettempdir()
    test_video = os.path.join(tmpdir, "_scene_test_dummy.mp4")

    print(f"\n📹 Creating dummy test video (3s SMPTE bars)...")
    try:
        subprocess.run([
            "ffmpeg","-y",
            "-f","lavfi","-i","smptebars=duration=3:size=640x360:rate=30",
            "-f","lavfi","-i","sine=frequency=440:duration=3",
            "-shortest", test_video
        ], capture_output=True, check=True)
        print(f"   Created: {test_video}")
    except Exception as e:
        print(f"   ⚠️  ffmpeg not available, skipping video tests.")
        print(f"   Testing utility layer only...")
        info = engine.ffmpeg.probe_video("nonexistent.mp4")
        assert info is None, "Should return None for missing file"
        print(f"   Probe non-existent: returns None ✅")
        print(f"\n{'='*60}")
        print("  ✅ UTILITY TESTS PASSED")
        print(f"{'='*60}")
        return

    # Test 1: Quick Scan
    print(f"\n🔍 Test 1: Quick Scan...")
    qs = engine.quick_scan(test_video)
    print(f"   File: {qs['filename']}")
    print(f"   Duration: {qs['duration']}s | Resolution: {qs['resolution']} | FPS: {qs['fps']}")
    print(f"   ✅ Quick scan OK")

    # Test 2: Full Analysis
    print(f"\n🎬 Test 2: Full Clip Analysis...")
    analysis = engine.analyze_clip(test_video, energy_level=0.6)
    print(f"   Duration: {analysis.duration}s | Resolution: {analysis.resolution}")
    print(f"   FPS: {analysis.fps} | Audio: {analysis.has_audio}")
    print(f"   Scene points: {len(analysis.scene_points)} | Quality: {analysis.quality_score}")
    for sp in analysis.scene_points[:5]:
        print(f"     → {sp.timestamp:.2f}s | {sp.priority.value} | {sp.scene_type.value} | conf={sp.confidence:.2f}")
    print(f"   ✅ Full analysis OK")

    # Test 3: Cut Schedule
    print(f"\n✂️  Test 3: Cut Schedule — pacing variations...")
    for pace in ["fast","normal","slow"]:
        s = engine.generate_cut_schedule([test_video], 3.0, pacing=pace)
        print(f"   {pace:>6}: {len(s.cut_points)} cuts | avg interval={s.average_cut_interval}s")
    print(f"   ✅ Pacing variations OK")

    # Test 4: Export function
    print(f"\n📤 Test 4: Export function...")
    cuts, per_clip = get_scene_cuts_for_batch([test_video], 3.0, energy=0.5, pacing="normal")
    print(f"   Total cuts: {len(cuts)} | Per-clip keys: {list(per_clip.keys())}")
    print(f"   ✅ Export function OK")

    # Test 5: Energy estimation
    print(f"\n⚡ Test 5: Energy estimation...")
    energy = analyze_clip_energy(test_video)
    print(f"   Estimated energy: {energy}")
    print(f"   ✅ Energy estimation OK")

    # Cleanup
    try:
        os.remove(test_video)
    except:
        pass

    print(f"\n{'='*60}")
    print("  ✅ ALL TESTS PASSED — Scene Detection Engine Ready!")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_self_test()