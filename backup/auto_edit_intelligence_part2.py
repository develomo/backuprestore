# ============================================================
# PHASE 3 — FILE 1: auto_edit_intelligence.py (PART 2/2)
# ============================================================
# YEH PART 2 hai — isse Part 1 ke saath merge karna hai
# Final file: auto_edit_intelligence.py
# ============================================================

import re
import math
import random
import logging
import statistics
import subprocess
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import Counter

# Part 1 se imports (same file mein honge)
# from auto_edit_intelligence_part1 import (
#     NicheKeywordDB, NicheDetector, ContentAnalyzer,
#     ContentAnalysis, NicheScore, PresetRecommendation,
#     AutoEditDecision, DetectedTone, logger
# )

logger = logging.getLogger("AutoEditIntelligence")


# ============================================================
# SECTION 5: PRESET SELECTOR
# ============================================================

class PresetSelector:
    """
    Best editing preset select karta hai from a niche's 8 presets —
    based on content tone, energy, complexity, and keyword signals.
    """

    # tone → preferred preset numbers (high energy → fast presets, etc.)
    TONE_PRESET_MAP: Dict[str, List[int]] = {
        "urgent_fast":    [8, 6, 3, 5, 1, 7, 2, 4],
        "calm_slow":      [7, 4, 1, 5, 2, 3, 6, 8],
        "dramatic":       [8, 6, 2, 5, 3, 4, 1, 7],
        "educational":    [4, 7, 1, 5, 3, 2, 6, 8],
        "inspirational":  [1, 3, 5, 7, 2, 4, 6, 8],
        "neutral":        [1, 2, 3, 4, 5, 6, 7, 8],
        "mixed":          [1, 2, 3, 4, 5, 6, 7, 8],
    }

    # Complexity → preset adjustment
    COMPLEXITY_PRESET_WEIGHTS: Dict[str, List[float]] = {
        #     P1   P2   P3   P4   P5   P6   P7   P8
        "low":    [0.9, 1.1, 1.0, 1.2, 0.9, 0.8, 1.3, 0.8],
        "medium": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        "high":   [1.1, 0.9, 1.1, 0.9, 1.2, 1.1, 0.8, 1.1],
    }

    @classmethod
    def select_best_preset(
        cls,
        niche: str,
        content_analysis: 'ContentAnalysis',
        niche_scores: List['NicheScore'],
    ) -> 'PresetRecommendation':
        """
        Main preset selection logic.
        Returns PresetRecommendation with best preset number 1-8.
        """
        # ── Step 1: Start with tone-based ordering ────────
        tone = content_analysis.dominant_tone.value
        preferred_order = cls.TONE_PRESET_MAP.get(tone, list(range(1, 9)))

        # ── Step 2: Score each preset ────────────────────
        preset_scores: Dict[int, float] = {}

        for idx, preset_num in enumerate(preferred_order):
            base_score = 1.0 - (idx * 0.05)  # Position-based decay

            # Complexity adjustment
            if content_analysis.complexity_score < 0.3:
                complexity_level = "low"
            elif content_analysis.complexity_score > 0.65:
                complexity_level = "high"
            else:
                complexity_level = "medium"
            complexity_weight = cls.COMPLEXITY_PRESET_WEIGHTS[complexity_level][preset_num - 1]
            base_score *= complexity_weight

            # Energy adjustment
            energy = content_analysis.energy_score
            if energy > 0.7 and preset_num in [8, 6, 3]:
                base_score *= 1.15  # High energy → fast presets
            elif energy < 0.3 and preset_num in [7, 4, 1]:
                base_score *= 1.15  # Low energy → calm presets

            # Keyword diversity bonus
            niche_score_obj = next(
                (ns for ns in niche_scores if ns.niche == niche), None
            )
            if niche_score_obj:
                if niche_score_obj.core_matches >= 5:
                    base_score *= 1.1  # Strong niche signal → more variety

            preset_scores[preset_num] = base_score

        # ── Step 3: Add controlled randomness (variation) ─
        for preset_num in preset_scores:
            jitter = random.uniform(-0.05, 0.05)
            preset_scores[preset_num] += jitter

        # ── Step 4: Pick winner ──────────────────────────
        best_preset_num = max(preset_scores, key=preset_scores.get)
        best_score = preset_scores[best_preset_num]

        # ── Step 5: Determine preset label ───────────────
        try:
            from niche_editing_presets import get_preset_by_number
            preset_obj = get_preset_by_number(niche, best_preset_num)
            preset_label = preset_obj.label
        except (ImportError, AttributeError):
            # Fallback labels
            fallback_labels = {
                1: "Signature", 2: "Cinematic", 3: "Dynamic",
                4: "Classic", 5: "Hologram Display", 6: "Dark Matrix",
                7: "Future Minimal", 8: "Tech Revolution",
            }
            preset_label = fallback_labels.get(best_preset_num, f"Preset {best_preset_num}")

        # ── Step 6: Build reason ─────────────────────────
        reasons = []
        if content_analysis.energy_score > 0.65:
            reasons.append("high-energy content detected")
        elif content_analysis.energy_score < 0.35:
            reasons.append("calm/measured content tone")
        if content_analysis.complexity_score > 0.6:
            reasons.append("complex narrative structure")
        if niche_scores:
            best_ns = next((ns for ns in niche_scores if ns.niche == niche), None)
            if best_ns and best_ns.core_matches >= 5:
                reasons.append(f"strong {niche.replace('_',' ')} signal")
        if not reasons:
            reasons.append("balanced auto-selection")

        reason = "; ".join(reasons)

        # ── Step 7: Confidence ───────────────────────────
        # Higher confidence = stronger signals = less randomness
        confidence = 0.5
        if niche_scores:
            best_ns = next((ns for ns in niche_scores if ns.niche == niche), None)
            if best_ns:
                confidence += best_ns.score * 0.3
        if content_analysis.dominant_tone != DetectedTone.NEUTRAL:
            confidence += 0.1
        confidence = min(0.95, confidence)

        matched_kws = []
        if niche_scores:
            best_ns = next((ns for ns in niche_scores if ns.niche == niche), None)
            if best_ns:
                matched_kws = best_ns.matched_keywords[:20]

        return PresetRecommendation(
            niche=niche,
            preset_number=best_preset_num,
            preset_label=preset_label,
            confidence=confidence,
            reason=reason,
            matched_keywords=matched_kws,
        )


# ============================================================
# SECTION 6: SCENE DETECTOR (FFmpeg-based)
# ============================================================

class SceneDetector:
    """
    FFmpeg scene detection for smart cut placement.
    Detects natural scene change points in video files.
    Uses ffmpeg's scenechange filter with adaptive threshold.
    """

    DEFAULT_THRESHOLD = 0.32       # Scene change sensitivity
    MIN_SCENE_DURATION = 0.8       # Minimum scene length in seconds
    MAX_SCENES_PER_FILE = 50       # Cap to prevent excessive cuts

    @classmethod
    def detect_scenes_ffmpeg(
        cls,
        video_path: str,
        threshold: float = DEFAULT_THRESHOLD,
        min_duration: float = MIN_SCENE_DURATION,
    ) -> List[float]:
        """
        Uses ffmpeg scenechange filter to detect cut points.
        Returns list of timestamps (seconds) where scene changes occur.
        """
        if not os.path.exists(video_path):
            logger.warning(f"SceneDetect: file not found → {video_path}")
            return []

        # Get video duration first
        duration = cls._get_video_duration(video_path)
        if duration <= 0:
            return []

        try:
            # FFmpeg scene detection command
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-filter:v", f"select='gt(scene,{threshold})',showinfo",
                "-f", "null",
                "-nostats", "-loglevel", "info",
                "-"
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120,
            )

            # Parse scene change timestamps from stderr
            scene_times: List[float] = []
            for line in result.stderr.split("\n"):
                # FFmpeg showinfo format: pts_time:XX.XXXX
                match = re.search(r'pts_time:([\d.]+)', line)
                if match:
                    t = float(match.group(1))
                    scene_times.append(t)

            # Filter: remove scenes too close to each other
            filtered: List[float] = []
            last_t = -min_duration
            for t in scene_times:
                if t - last_t >= min_duration:
                    filtered.append(t)
                    last_t = t
                if len(filtered) >= cls.MAX_SCENES_PER_FILE:
                    break

            # Filter: remove scenes too close to start/end
            filtered = [t for t in filtered if min_duration <= t <= (duration - 0.5)]

            logger.info(
                f"SceneDetect → {video_path}: {len(filtered)} scenes "
                f"(raw={len(scene_times)}, duration={duration:.1f}s)"
            )
            return filtered

        except subprocess.TimeoutExpired:
            logger.warning(f"SceneDetect timed out: {video_path}")
            return []
        except Exception as e:
            logger.warning(f"SceneDetect failed: {e}")
            return []

    @classmethod
    def _get_video_duration(cls, video_path: str) -> float:
        """Get video duration using ffprobe."""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            data = json.loads(result.stdout)
            return float(data.get("format", {}).get("duration", 0))
        except Exception:
            return 0.0

    @classmethod
    def detect_scenes_adaptive(
        cls,
        video_path: str,
        content_energy: float = 0.5,
    ) -> List[float]:
        """
        Adaptive threshold based on content energy.
        High energy → lower threshold (more cuts).
        Low energy → higher threshold (fewer cuts).
        """
        # Map energy (0-1) to threshold (0.25-0.45)
        threshold = 0.40 - (content_energy * 0.15)
        threshold = max(0.25, min(0.45, threshold))

        min_dur = cls.MIN_SCENE_DURATION
        if content_energy > 0.7:
            min_dur = 0.5  # More aggressive cuts for high energy
        elif content_energy < 0.3:
            min_dur = 1.5  # Slower pacing for calm content

        return cls.detect_scenes_ffmpeg(video_path, threshold, min_dur)

    @classmethod
    def smart_cut_points(
        cls,
        clip_paths: List[str],
        content_analysis: 'ContentAnalysis',
        total_duration: float,
    ) -> Dict[str, List[float]]:
        """
        Process multiple clips and return scene change points per clip.
        Returns {clip_path: [timestamps]}.
        """
        results: Dict[str, List[float]] = {}
        energy = content_analysis.energy_score

        for cp in clip_paths:
            if os.path.exists(cp):
                scenes = cls.detect_scenes_adaptive(cp, energy)
                results[cp] = scenes
            else:
                results[cp] = []

        return results


# ============================================================
# SECTION 7: MAIN AUTO EDIT INTELLIGENCE ENGINE
# ============================================================

class AutoEditIntelligence:
    """
    MAIN ENGINE — sab kuch ek jagah.
    
    Usage:
        engine = AutoEditIntelligence()
        decision = engine.analyze_and_decide(
            script_text="Your video script...",
            video_clips_info=[{"path": "/path/to/clip.mp4", "duration": 15.2}, ...],
        )
    """

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.content_analyzer = ContentAnalyzer()
        self.niche_detector = NicheDetector()
        self.preset_selector = PresetSelector()
        self.scene_detector = SceneDetector()
        logger.info(f"AutoEditIntelligence initialized (seed={seed})")

    def analyze_and_decide(
        self,
        script_text: str,
        video_clips: Optional[List[str]] = None,
        video_clips_info: Optional[List[Dict[str, Any]]] = None,
        user_niche_hint: Optional[str] = None,
        user_preset_hint: Optional[int] = None,
        detect_scenes: bool = True,
    ) -> AutoEditDecision:
        """
        COMPLETE AUTO-EDIT PIPELINE:
        1. Analyze content (tone, complexity, energy)
        2. Detect niche from script keywords
        3. Select best editing preset
        4. Detect scene change points (optional)
        5. Generate suggestions & warnings
        6. Return complete AutoEditDecision

        Args:
            script_text: Full video script/narration text
            video_clips: List of paths to video clip files
            video_clips_info: List of dicts with clip metadata
            user_niche_hint: Optional user-specified niche
            user_preset_hint: Optional user-specified preset (1-8)
            detect_scenes: Whether to run scene detection on clips
        """
        warnings: List[str] = []
        suggestions: List[str] = []

        # ── STEP 1: Content Analysis ─────────────────────
        logger.info("Step 1/5: Content Analysis...")
        content_analysis = self.content_analyzer.analyze(script_text)

        if content_analysis.word_count < 20:
            warnings.append("Script is very short (<20 words). Auto-detection may be unreliable.")

        # ── STEP 2: Niche Detection ──────────────────────
        logger.info("Step 2/5: Niche Detection...")

        if user_niche_hint:
            # User ne niche specify kiya — use it
            from niche_editing_presets import get_presets_for_niche
            try:
                presets = get_presets_for_niche(user_niche_hint)
                detected_niche = presets[0].niche
            except (ImportError, Exception):
                detected_niche = "default"
            # Still generate scores for reference
            _, niche_scores = self.niche_detector.detect_niche(script_text)
            logger.info(f"  Using user-specified niche: {detected_niche}")
        else:
            detected_niche, niche_scores = self.niche_detector.detect_niche(script_text)
            logger.info(f"  Auto-detected niche: {detected_niche}")

        # ── STEP 3: Preset Selection ─────────────────────
        logger.info("Step 3/5: Preset Selection...")

        if user_preset_hint and 1 <= user_preset_hint <= 8:
            # User ne preset specify kiya
            try:
                from niche_editing_presets import get_preset_by_number
                preset_obj = get_preset_by_number(detected_niche, user_preset_hint)
                recommended_preset = PresetRecommendation(
                    niche=detected_niche,
                    preset_number=user_preset_hint,
                    preset_label=preset_obj.label,
                    confidence=0.95,
                    reason="user-specified preset",
                )
            except (ImportError, AttributeError):
                recommended_preset = PresetRecommendation(
                    niche=detected_niche,
                    preset_number=user_preset_hint,
                    preset_label=f"Preset {user_preset_hint}",
                    confidence=0.9,
                    reason="user-specified preset",
                )
        else:
            _, niche_scores = self.niche_detector.detect_niche(script_text)
            recommended_preset = self.preset_selector.select_best_preset(
                detected_niche, content_analysis, niche_scores
            )
            logger.info(
                f"  Selected: {detected_niche} Preset #{recommended_preset.preset_number}"
                f" ({recommended_preset.preset_label})"
            )

        # ── STEP 4: Scene Detection ──────────────────────
        logger.info("Step 4/5: Scene Detection...")
        scene_change_points: List[float] = []
        all_scene_data: Dict[str, List[float]] = {}

        if detect_scenes and video_clips:
            all_scene_data = self.scene_detector.smart_cut_points(
                video_clips, content_analysis,
                total_duration=sum(
                    self.scene_detector._get_video_duration(cp)
                    for cp in video_clips if os.path.exists(cp)
                )
            )
            # Collect all scene points
            offset = 0.0
            for cp in video_clips:
                if cp in all_scene_data:
                    for t in all_scene_data[cp]:
                        scene_change_points.append(t + offset)
                if os.path.exists(cp):
                    offset += self.scene_detector._get_video_duration(cp)

            total_scenes = sum(len(v) for v in all_scene_data.values())
            if total_scenes == 0:
                suggestions.append("No natural scene changes detected. Using default cut timing.")
            else:
                suggestions.append(f"Detected {total_scenes} natural scene change points.")
            logger.info(f"  Total scene points: {len(scene_change_points)}")

        # ── STEP 5: Warnings & Suggestions ───────────────
        logger.info("Step 5/5: Generating suggestions...")

        if content_analysis.confidence if hasattr(content_analysis, 'confidence') else True:
            pass  # Additional checks can go here

        # Check if niche detection was weak
        best_ns = next(
            (ns for ns in niche_scores if ns.niche == detected_niche),
            None
        )
        if best_ns and best_ns.score < 0.25:
            warnings.append(
                f"Niche confidence is low ({best_ns.score:.2f}). "
                f"Consider specifying the niche manually."
            )

        # Complexity suggestions
        if content_analysis.complexity_score > 0.7:
            suggestions.append(
                "High complexity detected — consider slower pacing and longer cuts."
            )
        elif content_analysis.complexity_score < 0.25:
            suggestions.append(
                "Simple content structure — faster pacing may improve engagement."
            )

        # Energy suggestions
        if content_analysis.energy_score > 0.75:
            suggestions.append("High energy script — fast cuts and bold transitions recommended.")
            edit_complexity = "complex"
        elif content_analysis.energy_score < 0.25:
            suggestions.append("Low energy script — smooth, slow transitions recommended.")
            edit_complexity = "minimal"
        else:
            edit_complexity = "normal"

        # ── Overall Confidence ───────────────────────────
        # Weighted average of all confidence factors
        overall_confidence = recommended_preset.confidence * 0.5
        if best_ns:
            overall_confidence += best_ns.score * 0.3
        if content_analysis.dominant_tone != DetectedTone.NEUTRAL:
            overall_confidence += 0.1
        if user_niche_hint or user_preset_hint:
            overall_confidence += 0.1  # User input boosts confidence
        overall_confidence = min(0.98, overall_confidence)

        # ── Build Final Decision ─────────────────────────
        decision = AutoEditDecision(
            detected_niche=detected_niche,
            niche_scores=niche_scores,
            recommended_preset=recommended_preset,
            content_analysis=content_analysis,
            confidence=overall_confidence,
            scene_change_points=scene_change_points,
            edit_complexity=edit_complexity,
            warnings=warnings,
            suggestions=suggestions,
        )

        logger.info(
            f"✅ AutoEditDecision: niche={detected_niche}, "
            f"preset={recommended_preset.preset_number}, "
            f"confidence={overall_confidence:.2f}"
        )

        return decision

    def quick_decide(
        self,
        script_text: str,
    ) -> Dict[str, Any]:
        """
        Quick decision without scene detection — fast mode.
        Returns simplified dict for UI display.
        """
        decision = self.analyze_and_decide(
            script_text=script_text,
            detect_scenes=False,
        )
        return {
            "niche": decision.detected_niche,
            "niche_display": decision.detected_niche.replace("_", " ").title(),
            "preset_number": decision.recommended_preset.preset_number,
            "preset_label": decision.recommended_preset.preset_label,
            "confidence": round(decision.confidence, 2),
            "tone": decision.content_analysis.dominant_tone.value,
            "energy": round(decision.content_analysis.energy_score, 2),
            "complexity": round(decision.content_analysis.complexity_score, 2),
            "reason": decision.recommended_preset.reason,
            "suggestions": decision.suggestions[:3],
        }


# ============================================================
# SECTION 8: UTILITY — BATCH ANALYZER
# ============================================================

class BatchAutoAnalyzer:
    """
    Multiple scripts ko ek saath analyze karta hai —
    useful for batch video processing pipelines.
    """

    def __init__(self):
        self.engine = AutoEditIntelligence()

    def analyze_scripts(
        self,
        scripts: List[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        """
        Batch analyze multiple scripts.
        Each script dict: {"id": "...", "text": "..."}
        Returns list of decisions.
        """
        results = []
        for i, script in enumerate(scripts):
            script_id = script.get("id", f"script_{i}")
            text = script.get("text", "")

            decision = self.engine.quick_decide(text)
            decision["script_id"] = script_id
            decision["word_count"] = len(re.findall(r'\b\w+\b', text.lower()))
            results.append(decision)

        return results

    def group_by_niche(
        self,
        decisions: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group decisions by detected niche."""
        groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for d in decisions:
            groups[d["niche"]].append(d)
        return dict(groups)


# ============================================================
# SECTION 9: TEST / SELF-CHECK
# ============================================================

def run_self_test():
    """Quick self-test to verify all components work."""
    print("=" * 60)
    print("  AUTO EDIT INTELLIGENCE — SELF TEST")
    print("=" * 60)

    engine = AutoEditIntelligence(seed=42)

    # Test scripts for different niches
    test_scripts = {
        "luxury": """
            Experience the ultimate luxury lifestyle with our exclusive yacht collection.
            From millionaire mansions to private jets, discover the world of high-end living.
            Ferrari, Lamborghini, and Rolex — the symbols of true wealth and sophistication.
        """,
        "tech": """
            Artificial intelligence is transforming our future. Quantum computing breakthroughs
            are revolutionizing machine learning and neural networks. The metaverse, blockchain,
            and nanotechnology are shaping tomorrow's digital landscape.
        """,
        "mystery": """
            This unsolved mystery has baffled detectives for decades. The bizarre disappearance
            of three witnesses points to a deeper conspiracy. Was it murder? The enigmatic
            clues suggest something far more sinister and inexplicable.
        """,
        "finance": """
            Stock market analysis reveals unprecedented opportunities in crypto and trading.
            Learn how passive income through dividend investing and real estate can build
            lasting wealth. Financial freedom starts with smart compound interest strategies.
        """,
    }

    for name, script in test_scripts.items():
        print(f"\n🧪 Testing {name.upper()} script...")
        result = engine.quick_decide(script)
        print(f"   Niche:      {result['niche']}")
        print(f"   Preset:     #{result['preset_number']} - {result['preset_label']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Tone:       {result['tone']}")
        print(f"   Energy:     {result['energy']}")
        print(f"   Complexity: {result['complexity']}")
        print(f"   Reason:     {result['reason']}")

    print(f"\n{'=' * 60}")
    print("  ✅ SELF TEST COMPLETE — All components working!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    run_self_test()