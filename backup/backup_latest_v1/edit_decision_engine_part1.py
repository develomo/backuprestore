# ============================================================
# PHASE 3 — FILE 4: edit_decision_engine.py (PART 1/2)
# ============================================================
# Purpose: FINAL decision engine — sab kuch combine karta hai.
# Takes outputs from File 1 (niche+preset), File 2 (scene cuts),
# File 3 (content analysis) → produces COMPLETE edit config.
#
# Usage:
#   from edit_decision_engine import EditDecisionEngine
#   engine = EditDecisionEngine()
#   config = engine.generate_edit_config(script="...", clips=["c1.mp4"], render_count=3)
#   # config ab master_pipeline.py mein feed karo!
#
# Dependencies: auto_edit_intelligence.py, scene_detection_engine.py,
#               content_analyzer.py, niche_editing_presets.py
# ============================================================

import math
import random
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter

logger = logging.getLogger("EditDecisionEngine")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [EditDecision] %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(h)


# ============================================================
# SECTION 1: DATA STRUCTURES
# ============================================================

class QualityTier(Enum):
    PERFECT = "perfect"; EXCELLENT = "excellent"; GREAT = "great"
    GOOD = "good"; AVERAGE = "average"; POOR = "poor"


@dataclass
class ClipEditInstruction:
    clip_index: int; clip_path: str; duration: float
    motion_direction: str; zoom_min: float; zoom_max: float; zoom_step: float
    is_static: bool = False
    transition_type: str = "dissolve"; transition_duration: float = 0.25
    color_filter: str = ""; brightness_adjust: float = 0.0; saturation_adjust: float = 0.0
    vignette: float = 0.0; animation_style: str = "premium_float"
    cut_at_timestamp: float = 0.0; section_type: str = "body"
    voice_volume: float = 1.45; music_volume: float = 0.15; sfx_volume: float = 0.08


@dataclass
class QualityScores:
    video_score: float; voice_score: float; caption_score: float; combined_score: float
    video_breakdown: Dict[str, float] = field(default_factory=dict)
    voice_breakdown: Dict[str, float] = field(default_factory=dict)

    @property
    def tier(self) -> QualityTier:
        c = self.combined_score
        if c >= 9.5: return QualityTier.PERFECT
        if c >= 8.5: return QualityTier.EXCELLENT
        if c >= 7.5: return QualityTier.GREAT
        if c >= 6.5: return QualityTier.GOOD
        if c >= 5.0: return QualityTier.AVERAGE
        return QualityTier.POOR

    def to_dict(self) -> Dict[str, Any]:
        return {"video_score": round(self.video_score,1), "voice_score": round(self.voice_score,1),
                "caption_score": round(self.caption_score,1), "combined_score": round(self.combined_score,1),
                "tier": self.tier.value, "video_breakdown": self.video_breakdown,
                "voice_breakdown": self.voice_breakdown}


@dataclass
class EditConfig:
    config_id: str; niche: str; preset_number: int; preset_label: str; render_count: int
    script_summary: Dict[str, Any] = field(default_factory=dict)
    detected_tone: str = "neutral"; energy_level: float = 0.5
    clip_instructions: List[ClipEditInstruction] = field(default_factory=list)
    total_clips: int = 0; total_duration: float = 0.0
    scene_cuts: List[float] = field(default_factory=list)
    pacing_mode: str = "normal"; average_cut_interval: float = 3.0
    target_lufs: float = -14.0; voice_volume: float = 1.45
    music_volume: float = 0.15; sfx_volume: float = 0.08
    ducking_strength: float = 0.25; recommended_bpm: int = 100
    quality_scores: Optional[QualityScores] = None
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    variation_seed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        qs = self.quality_scores.to_dict() if self.quality_scores else {}
        return {
            "config_id": self.config_id, "niche": self.niche,
            "preset_number": self.preset_number, "preset_label": self.preset_label,
            "render_count": self.render_count, "detected_tone": self.detected_tone,
            "energy_level": round(self.energy_level, 3),
            "total_clips": self.total_clips, "total_duration": round(self.total_duration, 2),
            "scene_cuts": self.scene_cuts, "pacing_mode": self.pacing_mode,
            "average_cut_interval": round(self.average_cut_interval, 2),
            "audio": {"target_lufs": self.target_lufs, "voice_volume": self.voice_volume,
                       "music_volume": self.music_volume, "sfx_volume": self.sfx_volume,
                       "ducking_strength": self.ducking_strength, "recommended_bpm": self.recommended_bpm},
            "quality_scores": qs,
            "clip_instructions": [
                {"index": ci.clip_index, "clip_path": ci.clip_path, "duration": ci.duration,
                 "motion": {"direction": ci.motion_direction, "zoom_min": ci.zoom_min,
                            "zoom_max": ci.zoom_max, "zoom_step": ci.zoom_step, "is_static": ci.is_static},
                 "transition": {"type": ci.transition_type, "duration": ci.transition_duration},
                 "color": {"filter": ci.color_filter, "brightness": ci.brightness_adjust,
                           "saturation": ci.saturation_adjust, "vignette": ci.vignette},
                 "animation": ci.animation_style, "cut_at": ci.cut_at_timestamp,
                 "section": ci.section_type,
                 "audio": {"voice_volume": ci.voice_volume, "music_volume": ci.music_volume,
                           "sfx_volume": ci.sfx_volume}}
                for ci in self.clip_instructions
            ],
            "warnings": self.warnings, "suggestions": self.suggestions,
            "variation_seed": self.variation_seed,
        }


# ============================================================
# SECTION 2: ANTI-PATTERN VARIATION ENGINE
# ============================================================

class VariationEngine:
    """Ensures no two videos look identical — YouTube anti-bot detection."""

    MOTION_POOL = ["gentle_float_up","gentle_float_down","slow_pan_left","slow_pan_right",
                   "left_to_right","right_to_left","top_to_bottom","bottom_to_top",
                   "diagonal_soft","diagonal_reverse","center_push","static_hold",
                   "subtle_zoom_in","soft_reveal"]

    TRANSITION_POOL = ["dissolve","fade","fadewhite","fadeblack","smoothleft","smoothright",
                       "smoothup","smoothdown","wipeleft","wiperight","wipeup","wipedown",
                       "circleopen","circleclose","rectcrop","pixelize"]

    ANIMATION_POOL = ["premium_float","hook_punch","mystery_creep","documentary_hold",
                      "subtle_zoom_in","soft_reveal","left_drift","right_drift",
                      "up_drift","down_drift","slow_push","diagonal_soft"]

    COLOR_MICRO = [
        {"b":0.000,"s":0.000,"c":0.000},{"b":0.002,"s":0.005,"c":0.003},
        {"b":-0.002,"s":-0.003,"c":0.005},{"b":0.003,"s":-0.004,"c":-0.002},
        {"b":-0.001,"s":0.006,"c":0.004},{"b":0.004,"s":0.002,"c":-0.003},
        {"b":-0.003,"s":-0.005,"c":-0.004},{"b":0.001,"s":-0.002,"c":0.006},
    ]

    @classmethod
    def get_variation_seed(cls, render_count: int, preset_number: int) -> int:
        return (render_count * 31 + preset_number * 17) % 10000

    @classmethod
    def rotate_pool(cls, pool: List[str], seed: int, clip_index: int) -> List[str]:
        rng = random.Random(seed + clip_index * 7 + clip_index * clip_index * 13)
        rotated = pool.copy(); rng.shuffle(rotated)
        shift = (seed + clip_index) % len(rotated)
        return rotated[shift:] + rotated[:shift]

    @classmethod
    def pick_from_pool(cls, pool: List[str], seed: int, clip_index: int,
                       last_picks: List[str], avoid_count: int = 3) -> str:
        rotated = cls.rotate_pool(pool, seed, clip_index)
        for item in rotated:
            if item not in last_picks[-avoid_count:]: return item
        return random.Random(seed + clip_index).choice(rotated)

    @classmethod
    def pick_motion(cls, seed: int, clip_index: int, last_motions: List[str]) -> str:
        return cls.pick_from_pool(cls.MOTION_POOL, seed, clip_index, last_motions, 3)

    @classmethod
    def pick_transition(cls, seed: int, clip_index: int, last_trans: List[str]) -> str:
        return cls.pick_from_pool(cls.TRANSITION_POOL, seed, clip_index, last_trans, 4)

    @classmethod
    def pick_animation(cls, seed: int, clip_index: int, section: str,
                       last_anims: List[str]) -> str:
        rng = random.Random(seed + clip_index * 19)
        if section == "hook":
            p = [a for a in cls.ANIMATION_POOL if a in ("hook_punch","premium_float","soft_reveal","subtle_zoom_in")]
            return rng.choice(p) if p else rng.choice(cls.ANIMATION_POOL)
        if section == "climax":
            p = [a for a in cls.ANIMATION_POOL if a in ("hook_punch","up_drift","slow_push","premium_float")]
            return rng.choice(p) if p else rng.choice(cls.ANIMATION_POOL)
        return cls.pick_from_pool(cls.ANIMATION_POOL, seed, clip_index, last_anims, 3)

    @classmethod
    def apply_color_micro(cls, base_filter: str, seed: int, clip_index: int
                          ) -> Tuple[str, float, float]:
        import re
        rng = random.Random(seed + clip_index * 23)
        micro = rng.choice(cls.COLOR_MICRO)
        c, s, b = 1.0, 1.0, 0.0
        cm = re.search(r'contrast=([\d.]+)', base_filter)
        sm = re.search(r'saturation=([\d.]+)', base_filter)
        bm = re.search(r'brightness=([\d.-]+)', base_filter)
        if cm: c = float(cm.group(1))
        if sm: s = float(sm.group(1))
        if bm: b = float(bm.group(1))
        c += micro["c"] + rng.uniform(-0.003, 0.003)
        s += micro["s"] + rng.uniform(-0.004, 0.004)
        b += micro["b"] + rng.uniform(-0.001, 0.001)
        new_f = f"eq=contrast={c:.4f}:saturation={s:.4f}:brightness={b:.4f}"
        return new_f, micro["b"], micro["s"]


# ============================================================
# SECTION 3: QUALITY SCORING ENGINE
# ============================================================

class QualityScoringEngine:
    """10/10 scoring for video, voice, combined."""

    @staticmethod
    def score_video(clip_instructions: List[ClipEditInstruction],
                    scene_cuts: List[float], total_duration: float,
                    energy: float) -> Tuple[float, Dict[str, float]]:
        bd = {}
        nc = max(1, len(clip_instructions))
        um = len(set(ci.motion_direction for ci in clip_instructions))
        bd["motion_variety"] = round(min(2.5, um/nc*3.5), 1)
        ut = len(set(ci.transition_type for ci in clip_instructions))
        bd["transition_variety"] = round(min(2.0, ut/nc*3.0), 1)
        if len(scene_cuts) >= 2:
            iv = [scene_cuts[i+1]-scene_cuts[i] for i in range(len(scene_cuts)-1)]
            if iv:
                avg = sum(iv)/len(iv)
                std = (sum((x-avg)**2 for x in iv)/len(iv))**0.5
                cv = std/max(0.1, avg)
                bd["cut_rhythm"] = round(2.0 if 0.15<=cv<0.5 else (1.5 if cv<0.8 else (0.8 if cv<0.15 else 1.0)), 1)
            else: bd["cut_rhythm"] = 1.0
        else: bd["cut_rhythm"] = 0.5
        uc = len(set(ci.color_filter for ci in clip_instructions))
        cr = uc/nc
        bd["color_variety"] = round(1.5 if 0.2<=cr<=0.8 else (1.0 if cr<0.2 else 1.2), 1)
        cpm = len(scene_cuts)/max(1, total_duration/60)
        bd["pacing_match"] = round(2.0 if (energy>0.6 and cpm>4) or (energy<0.4 and cpm<4) else 1.5, 1)
        total = round(sum(bd.values()), 1); bd["_total"] = total
        return total, bd

    @staticmethod
    def score_voice(lufs: float, lra: float, has_sr: bool = True,
                    has_pv: bool = True, has_hm: bool = False) -> Tuple[float, Dict[str, float]]:
        bd = {}
        diff = abs(lufs - (-14.0))
        bd["lufs_accuracy"] = round(2.5 if diff<=0.5 else (2.0 if diff<=1.0 else (1.5 if diff<=2.0 else (1.0 if diff<=3.0 else 0.5))), 1)
        bd["dynamic_range"] = round(2.5 if 4.0<=lra<=6.0 else (2.0 if 3.0<=lra<=7.0 else (1.5 if 2.0<=lra<=8.0 else 0.5)), 1)
        fs = 0.0
        if has_sr: fs += 1.5
        if has_pv: fs += 1.5
        if has_hm: fs += 2.0
        bd["features"] = round(fs, 1)
        total = round(sum(bd.values()), 1); bd["_total"] = total
        return total, bd

    @staticmethod
    def score_combined(vs: float, vos: float, cs: float) -> Tuple[float, Dict[str, float]]:
        w = {"video": 0.40, "voice": 0.35, "caption": 0.25}
        total = round(vs*w["video"] + vos*w["voice"] + cs*w["caption"], 1)
        return total, {"video_weighted": round(vs*w["video"],1),
                       "voice_weighted": round(vos*w["voice"],1),
                       "caption_weighted": round(cs*w["caption"],1), "_total": total}


print("✅ edit_decision_engine.py PART 1/2 loaded.")
print("   👉 PART 2 mein EditDecisionEngine (MAIN) + Export + Self-test hai.")