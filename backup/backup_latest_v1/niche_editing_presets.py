# ============================================================
# MY CREATION VIDEO GENERATOR — PHASE 1
# niche_editing_presets.py — COMPLETE v2.0 + ALL FIXES
# ============================================================
# 56 Total Presets: 7 Niches × 8 Styles Each
# FIXES: Future Tech 5-8, Interior 7, no duplicate return
# ============================================================

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class MotionConfig:
    directions: List[str]
    zoom_min: float
    zoom_max: float
    zoom_step: float
    use_static_contrast: bool
    static_every_n_clips: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TransitionConfig:
    types: List[str]
    min_repeat_gap: int
    duration_base: float
    duration_range: Tuple[float, float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CutRhythmConfig:
    hook_min: float
    hook_max: float
    body_min: float
    body_max: float
    emphasis_min: float
    emphasis_max: float
    long_min: float
    long_max: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ColorConfig:
    grade_filter: str
    temperature_shift: float
    vignette_strength: float
    film_grain_opacity: float
    sharpness: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AnimationConfig:
    styles: List[str]
    min_repeat_gap: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AudioConfig:
    voice_volume: float
    music_volume: float
    sfx_volume: float
    target_lufs: float
    ducking_strength: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EditingPreset:
    preset_id: str
    preset_number: int
    niche: str
    label: str
    description: str
    motion: MotionConfig = field(default_factory=lambda: MotionConfig([], 1.0, 1.0, 0.0, False, 10))
    transition: TransitionConfig = field(default_factory=lambda: TransitionConfig([], 0, 0.3, (0.1, 0.5)))
    cut_rhythm: CutRhythmConfig = field(default_factory=lambda: CutRhythmConfig(0, 0, 0, 0, 0, 0, 0, 0))
    color: ColorConfig = field(default_factory=lambda: ColorConfig("", 0, 0, 0, 0))
    animation: AnimationConfig = field(default_factory=lambda: AnimationConfig([], 0))
    audio: AudioConfig = field(default_factory=lambda: AudioConfig(1.0, 0.0, 0.0, -14.0, 0.0))
    variation_seed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["motion"]["directions"] = list(self.motion.directions)
        d["transition"]["types"] = list(self.transition.types)
        d["animation"]["styles"] = list(self.animation.styles)
        return d


# ============================================================
# HELPER MACROS
# ============================================================

def _m(dirs, zoom_min, zoom_max, zoom_step, use_static=False, static_every=10):
    return MotionConfig(list(dirs), zoom_min, zoom_max, zoom_step, use_static, static_every)

def _t(types, gap=0, dur_base=0.3, dur_lo=0.1, dur_hi=0.5):
    return TransitionConfig(list(types), gap, dur_base, (dur_lo, dur_hi))

def _c(h_min, h_max, b_min, b_max, e_min, e_max, l_min, l_max):
    return CutRhythmConfig(h_min, h_max, b_min, b_max, e_min, e_max, l_min, l_max)

def _g(eq_str, temp=0, vig=0, grain=0, sharp=0.1):
    return ColorConfig(eq_str, temp, vig, grain, sharp)

def _a(styles, gap=3):
    return AnimationConfig(list(styles), gap)

def _au(voice=1.5, music=0.15, sfx=0.07, lufs=-14.0, duck=0.25):
    return AudioConfig(voice, music, sfx, lufs, duck)


# ============================================================
# ANIMATION & MOTION POOLS
# ============================================================

MOTION_14 = [
    "slow_pan_right", "static_hold", "gentle_float_up", "gentle_float_down",
    "left_to_right", "right_to_left", "top_to_bottom", "bottom_to_top",
    "center_push", "diagonal_soft", "diagonal_reverse",
    "slow_push", "slow_pan_left", "premium_float",
]

TRANSITION_16 = [
    "dissolve", "fade", "fadewhite", "wipeleft", "wiperight",
    "wipeup", "wipedown", "smoothleft", "smoothright",
    "slideright", "slideleft", "circleopen", "circleclose",
    "rectcrop", "pixelize", "blur",
]

ANIMATION_9 = [
    "hook_punch", "subtle_zoom_in", "subtle_zoom_out", "left_drift",
    "right_drift", "soft_reveal", "documentary_hold",
    "up_drift", "down_drift",
]

# Extra animation styles for mystery/other niches
ANIMATION_EXTRA = [
    "mystery_creep", "premium_float", "gentle_float_up", "gentle_float_down",
    "slow_push", "diagonal_soft", "diagonal_reverse",
]

ALL_ANIMATIONS = ANIMATION_9 + ANIMATION_EXTRA


# ============================================================
# NICHE DISPLAY NAMES
# ============================================================

NICHE_DISPLAY_NAMES = {
    "luxury_lifestyle": "Luxury Lifestyle",
    "quantum_future": "Future / Tech",
    "mystery": "Mystery / Crime",
    "stoic_wisdom": "Stoic Wisdom",
    "interior_design": "Interior Design",
    "finance_simulation": "Finance / Business",
    "default": "Default / General",
}

NICHE_FAMILY_MAP = {
    "luxury_lifestyle": "luxury",
    "quantum_future": "future_tech",
    "mystery": "mystery",
    "stoic_wisdom": "wisdom",
    "interior_design": "design",
    "finance_simulation": "finance",
    "default": "general",
}


# ============================================================
# PRESET BUILDERS
# ============================================================

def _build_luxury_lifestyle_presets() -> List[EditingPreset]:
    niche = "luxury_lifestyle"
    return [
        EditingPreset(preset_id=f"{niche}_preset_1", preset_number=1, niche=niche, label="Golden Hour",
            description="Warm golden glow, dreamy dissolves, slow cinematic motion. Perfect for high-end product showcases.",
            motion=_m(["slow_pan_right","center_push","gentle_float_up","static_hold","left_to_right","gentle_float_down","diagonal_soft","premium_float"], zoom_min=1.035, zoom_max=1.080, zoom_step=0.00038, use_static=True, static_every=4),
            transition=_t(["dissolve","fade","dissolve","fade","dissolve","fadewhite","circleopen","dissolve"], gap=3, dur_base=0.40, dur_lo=0.20, dur_hi=0.55),
            cut_rhythm=_c(1.8,2.8, 4.5,7.0, 7.0,10.0, 5.5,8.5),
            color=_g("eq=contrast=1.032:saturation=1.022:brightness=0.004", 0.05, 0.018, 0.010, 0.13),
            animation=_a(["premium_float","subtle_zoom_in","soft_reveal","left_drift","slow_push","right_drift","static_hold","gentle_float_down"]),
            audio=_au(1.55, 0.125, 0.055, duck=0.20), variation_seed=100),
        EditingPreset(preset_id=f"{niche}_preset_2", preset_number=2, niche=niche, label="Crystal Clear",
            description="Cold crisp clarity, sharp contrast, modern luxury. Jewelry & glass product focus.",
            motion=_m(["center_push","static_hold","left_to_right","gentle_float_up","diagonal_soft","right_to_left","static_hold","premium_float"], zoom_min=1.028, zoom_max=1.072, zoom_step=0.00032, use_static=True, static_every=3),
            transition=_t(["smoothleft","dissolve","smoothright","dissolve","circleclose","smoothleft","fade","dissolve"], gap=3, dur_base=0.35, dur_lo=0.18, dur_hi=0.48),
            cut_rhythm=_c(1.6,2.5, 4.0,6.8, 6.5,9.5, 5.0,8.0),
            color=_g("eq=contrast=1.038:saturation=1.015:brightness=0.008", -0.02, 0.012, 0.006, 0.15),
            animation=_a(["documentary_hold","soft_reveal","subtle_zoom_in","left_drift","right_drift","slow_push","premium_float","gentle_float_down"]),
            audio=_au(1.52, 0.130, 0.050, duck=0.18), variation_seed=200),
        EditingPreset(preset_id=f"{niche}_preset_3", preset_number=3, niche=niche, label="Heritage",
            description="Vintage film look, warm brown tones, classic dissolves. Old-money aesthetic.",
            motion=_m(["gentle_float_up","slow_pan_right","static_hold","left_to_right","center_push","gentle_float_down","diagonal_soft","slow_pan_left"], zoom_min=1.042, zoom_max=1.090, zoom_step=0.00045, use_static=True, static_every=5),
            transition=_t(["dissolve","fade","circleopen","dissolve","fade","blur","circleclose","dissolve"], gap=4, dur_base=0.45, dur_lo=0.22, dur_hi=0.60),
            cut_rhythm=_c(2.0,3.2, 5.0,7.5, 8.0,11.0, 6.0,9.0),
            color=_g("eq=contrast=1.030:saturation=1.040:brightness=-0.002", 0.08, 0.025, 0.020, 0.08),
            animation=_a(["soft_reveal","premium_float","subtle_zoom_in","documentary_hold","left_drift","right_drift","slow_push","subtle_zoom_out"]),
            audio=_au(1.58, 0.118, 0.048, duck=0.15), variation_seed=300),
        EditingPreset(preset_id=f"{niche}_preset_4", preset_number=4, niche=niche, label="High Energy",
            description="Fast paced showcase, quick cuts, bold motion. For luxury sports cars & lifestyle.",
            motion=_m(["diagonal_reverse","left_to_right","bottom_to_top","center_push","right_to_left","top_to_bottom","diagonal_soft","gentle_float_down"], zoom_min=1.058, zoom_max=1.125, zoom_step=0.00058, use_static=False, static_every=10),
            transition=_t(["wipeleft","slideright","pixelize","wipeup","wipedown","smoothleft","smoothright","fadewhite"], gap=5, dur_base=0.28, dur_lo=0.12, dur_hi=0.38),
            cut_rhythm=_c(0.9,1.8, 3.0,5.2, 5.0,7.5, 3.5,5.5),
            color=_g("eq=contrast=1.055:saturation=1.048:brightness=0.000", -0.04, 0.015, 0.012, 0.12),
            animation=_a(["hook_punch","left_drift","right_drift","up_drift","down_drift","diagonal_reverse","diagonal_soft","subtle_zoom_out"]),
            audio=_au(1.48, 0.168, 0.095, duck=0.30), variation_seed=400),
        EditingPreset(preset_id=f"{niche}_preset_5", preset_number=5, niche=niche, label="Champagne",
            description="Celebration vibe. Bright gold tones, circular reveals, high energy. For party/lifestyle.",
            motion=_m(["center_push","gentle_float_up","static_hold","slow_pan_right","left_to_right","gentle_float_down","diagonal_soft","premium_float"], zoom_min=1.045, zoom_max=1.105, zoom_step=0.00050, use_static=True, static_every=5),
            transition=_t(["circleopen","fadewhite","circleclose","dissolve","blur","circleopen","smoothleft","smoothright"], gap=4, dur_base=0.32, dur_lo=0.15, dur_hi=0.44),
            cut_rhythm=_c(1.2,2.2, 3.8,6.0, 5.5,8.0, 4.5,7.0),
            color=_g("eq=contrast=1.042:saturation=1.055:brightness=0.005", 0.06, 0.020, 0.010, 0.13),
            animation=_a(["premium_float","gentle_float_up","soft_reveal","left_drift","right_drift","diagonal_soft","slow_push","hook_punch"]),
            audio=_au(1.50, 0.155, 0.080, duck=0.26), variation_seed=500),
        EditingPreset(preset_id=f"{niche}_preset_6", preset_number=6, niche=niche, label="Midnight",
            description="Dark, moody, atmospheric. Deep blacks, slow motion, minimal cuts. For high-end watches.",
            motion=_m(["static_hold","gentle_float_up","slow_pan_right","center_push","left_to_right","slow_pan_left","gentle_float_down","static_hold"], zoom_min=1.025, zoom_max=1.065, zoom_step=0.00028, use_static=True, static_every=3),
            transition=_t(["dissolve","fade","dissolve","fade","blur","dissolve","fade","circleclose"], gap=3, dur_base=0.42, dur_lo=0.22, dur_hi=0.55),
            cut_rhythm=_c(2.2,3.5, 5.5,8.0, 8.5,12.0, 6.5,9.5),
            color=_g("eq=contrast=1.042:saturation=1.008:brightness=-0.012", -0.02, 0.035, 0.018, 0.10),
            animation=_a(["subtle_zoom_in","soft_reveal","documentary_hold","left_drift","slow_push","static_hold","right_drift","premium_float"]),
            audio=_au(1.58, 0.112, 0.045, duck=0.14), variation_seed=600),
        EditingPreset(preset_id=f"{niche}_preset_7", preset_number=7, niche=niche, label="Runway",
            description="Fashion runway inspired. Sharp cuts, snappy transitions, model-centric. High contrast.",
            motion=_m(["left_to_right","center_push","right_to_left","top_to_bottom","bottom_to_top","diagonal_soft","static_hold","slow_pan_right"], zoom_min=1.052, zoom_max=1.118, zoom_step=0.00055, use_static=False, static_every=11),
            transition=_t(["wipeleft","wiperight","fadewhite","pixelize","wipeup","wipedown","smoothleft","smoothright"], gap=5, dur_base=0.25, dur_lo=0.10, dur_hi=0.35),
            cut_rhythm=_c(0.8,1.6, 2.8,5.0, 4.5,7.0, 3.2,5.2),
            color=_g("eq=contrast=1.058:saturation=1.042:brightness=0.002", -0.05, 0.022, 0.014, 0.14),
            animation=_a(["left_drift","right_drift","hook_punch","up_drift","down_drift","diagonal_reverse","diagonal_soft","soft_reveal"]),
            audio=_au(1.46, 0.175, 0.102, duck=0.32), variation_seed=700),
        EditingPreset(preset_id=f"{niche}_preset_8", preset_number=8, niche=niche, label="Bespoke",
            description="Artisan crafted. Handmade feel, organic pans, natural light. For craftsmanship content.",
            motion=_m(["slow_pan_right","slow_pan_left","gentle_float_up","center_push","static_hold","gentle_float_down","diagonal_soft","left_to_right"], zoom_min=1.032, zoom_max=1.075, zoom_step=0.00035, use_static=True, static_every=4),
            transition=_t(["dissolve","fade","smoothleft","dissolve","fade","smoothright","circleopen","dissolve"], gap=3, dur_base=0.38, dur_lo=0.20, dur_hi=0.50),
            cut_rhythm=_c(1.8,3.0, 4.8,7.5, 7.5,10.5, 6.0,8.5),
            color=_g("eq=contrast=1.025:saturation=1.018:brightness=0.005", 0.03, 0.015, 0.012, 0.11),
            animation=_a(["premium_float","slow_push","subtle_zoom_in","soft_reveal","documentary_hold","left_drift","static_hold","gentle_float_down"]),
            audio=_au(1.55, 0.122, 0.052, duck=0.18), variation_seed=800),
    ]


def _build_future_tech_presets() -> List[EditingPreset]:
    """Quantum / Future Tech — 8 presets: futuristic, clean, high-energy."""
    niche = "quantum_future"

    p1 = EditingPreset(preset_id=f"{niche}_preset_1", preset_number=1, niche=niche, label="Neon Pulse",
        description="Cyberpunk-inspired neon energy. Fast cuts, flash transitions, bold motion. For AI/tech hype videos.",
        motion=_m(["diagonal_reverse","bottom_to_top","left_to_right","center_push","right_to_left","diagonal_soft","top_to_bottom","slow_pan_right"], zoom_min=1.065, zoom_max=1.135, zoom_step=0.00062, use_static=False, static_every=10),
        transition=_t(["fadewhite","wipeleft","slideright","pixelize","smoothleft","fadewhite","wiperight","smoothright"], gap=5, dur_base=0.25, dur_lo=0.10, dur_hi=0.35),
        cut_rhythm=_c(0.8,1.6, 2.8,5.0, 4.5,7.0, 3.5,5.5),
        color=_g("eq=contrast=1.050:saturation=1.050:brightness=0.000", -0.05, 0.018, 0.012, 0.12),
        animation=_a(["hook_punch","left_drift","right_drift","diagonal_reverse","up_drift","subtle_zoom_in","down_drift","mystery_creep"]),
        audio=_au(1.50, 0.160, 0.090, duck=0.30), variation_seed=1100)

    p2 = EditingPreset(preset_id=f"{niche}_preset_2", preset_number=2, niche=niche, label="Clean Silicon",
        description="Apple-style clean tech presentation. Minimal motion, crisp cuts, white-space aesthetic. For product reveals.",
        motion=_m(["center_push","static_hold","slow_pan_right","left_to_right","gentle_float_up","static_hold","right_to_left","center_push"], zoom_min=1.030, zoom_max=1.075, zoom_step=0.00035, use_static=True, static_every=3),
        transition=_t(["smoothleft","dissolve","smoothright","fade","smoothleft","dissolve","smoothright","fade"], gap=4, dur_base=0.28, dur_lo=0.15, dur_hi=0.38),
        cut_rhythm=_c(1.4,2.2, 4.0,6.5, 6.5,8.5, 5.0,7.5),
        color=_g("eq=contrast=1.028:saturation=1.015:brightness=0.006", -0.02, 0.008, 0.008, 0.14),
        animation=_a(["documentary_hold","subtle_zoom_in","soft_reveal","left_drift","slow_push","static_hold","right_drift","subtle_zoom_out"]),
        audio=_au(1.52, 0.135, 0.055, duck=0.22), variation_seed=1200)

    p3 = EditingPreset(preset_id=f"{niche}_preset_3", preset_number=3, niche=niche, label="Data Stream",
        description="High-speed data/information flow. Rapid cuts, glitch transitions, constant motion. For charts/stats/data videos.",
        motion=_m(["right_to_left","left_to_right","diagonal_reverse","top_to_bottom","bottom_to_top","diagonal_soft","right_to_left","left_to_right"], zoom_min=1.072, zoom_max=1.145, zoom_step=0.00070, use_static=False, static_every=12),
        transition=_t(["pixelize","rectcrop","wipeleft","wiperight","slideright","pixelize","wipeup","wipedown"], gap=5, dur_base=0.20, dur_lo=0.08, dur_hi=0.30),
        cut_rhythm=_c(0.6,1.4, 2.4,4.5, 4.0,6.5, 3.0,5.0),
        color=_g("eq=contrast=1.055:saturation=1.055:brightness=-0.003", -0.06, 0.012, 0.010, 0.16),
        animation=_a(["hook_punch","left_drift","right_drift","up_drift","down_drift","diagonal_reverse","diagonal_soft","mystery_creep"]),
        audio=_au(1.48, 0.170, 0.095, duck=0.32), variation_seed=1300)

    p4 = EditingPreset(preset_id=f"{niche}_preset_4", preset_number=4, niche=niche, label="Quantum Lab",
        description="Scientific research style. Precise pacing, clean dissolves, measured zooms. For deep-dive science content.",
        motion=_m(["center_push","slow_pan_right","gentle_float_up","static_hold","left_to_right","diagonal_soft","slow_pan_left","center_push"], zoom_min=1.038, zoom_max=1.085, zoom_step=0.00042, use_static=True, static_every=4),
        transition=_t(["dissolve","fade","dissolve","fade","smoothleft","dissolve","fade","smoothright"], gap=4, dur_base=0.35, dur_lo=0.18, dur_hi=0.45),
        cut_rhythm=_c(1.5,2.4, 4.2,7.0, 7.0,9.5, 5.5,8.0),
        color=_g("eq=contrast=1.035:saturation=1.025:brightness=0.002", -0.02, 0.022, 0.015, 0.10),
        animation=_a(["soft_reveal","subtle_zoom_in","documentary_hold","left_drift","slow_push","right_drift","premium_float","static_hold"]),
        audio=_au(1.55, 0.145, 0.060, duck=0.24), variation_seed=1400)

    p5 = EditingPreset(preset_id=f"{niche}_preset_5", preset_number=5, niche=niche, label="Hologram Display",
        description="3D holographic interface feel. Float motions, circle transitions, cyan glow aesthetic. Sci-fi UI style.",
        motion=_m(["gentle_float_up","diagonal_soft","gentle_float_down","center_push","left_to_right","right_to_left","slow_pan_left","slow_pan_right"], zoom_min=1.058, zoom_max=1.120, zoom_step=0.00055, use_static=True, static_every=6),
        transition=_t(["circleopen","dissolve","wipeleft","rectcrop","circleopen","smoothleft","wiperight","dissolve"], gap=6, dur_base=0.30, dur_lo=0.14, dur_hi=0.42),
        cut_rhythm=_c(1.0,1.8, 3.2,5.8, 5.5,8.0, 4.0,6.5),
        color=_g("eq=contrast=1.048:saturation=1.045:brightness=0.001", -0.08, 0.025, 0.010, 0.11),
        animation=_a(["premium_float","gentle_float_up","gentle_float_down","diagonal_soft","left_drift","right_drift","slow_push","soft_reveal"]),
        audio=_au(1.50, 0.155, 0.085, duck=0.28), variation_seed=1500)

    p6 = EditingPreset(preset_id=f"{niche}_preset_6", preset_number=6, niche=niche, label="Dark Matrix",
        description="Dark terminal/matrix code aesthetic. Green tints, glitch effects, data-stream transitions. Hacker/cyber feel.",
        motion=_m(["right_to_left","bottom_to_top","diagonal_reverse","top_to_bottom","left_to_right","center_push","diagonal_soft","gentle_float_up"], zoom_min=1.062, zoom_max=1.128, zoom_step=0.00058, use_static=False, static_every=10),
        transition=_t(["pixelize","rectcrop","wipeup","slideright","pixelize","wipeleft","wipedown","rectcrop"], gap=5, dur_base=0.22, dur_lo=0.08, dur_hi=0.30),
        cut_rhythm=_c(0.7,1.5, 2.5,4.8, 4.0,6.5, 3.0,5.0),
        color=_g("eq=contrast=1.058:saturation=1.042:brightness=-0.004", -0.07, 0.030, 0.018, 0.14),
        animation=_a(["hook_punch","mystery_creep","left_drift","right_drift","up_drift","down_drift","diagonal_reverse","diagonal_soft"]),
        audio=_au(1.48, 0.165, 0.092, duck=0.32), variation_seed=1600)

    p7 = EditingPreset(preset_id=f"{niche}_preset_7", preset_number=7, niche=niche, label="Future Minimal",
        description="Future minimal. White space, clean lines, floating UI elements. Apple keynote/product launch feel.",
        motion=_m(["center_push","gentle_float_up","static_hold","slow_pan_right","gentle_float_down","left_to_right","diagonal_soft","static_hold"], zoom_min=1.025, zoom_max=1.068, zoom_step=0.00030, use_static=True, static_every=3),
        transition=_t(["smoothleft","fade","smoothright","dissolve","smoothleft","fade","smoothright","dissolve"], gap=3, dur_base=0.32, dur_lo=0.18, dur_hi=0.42),
        cut_rhythm=_c(1.6,2.6, 4.5,7.2, 7.0,9.5, 5.5,8.0),
        color=_g("eq=contrast=1.025:saturation=1.012:brightness=0.006", -0.01, 0.010, 0.008, 0.13),
        animation=_a(["documentary_hold","subtle_zoom_in","soft_reveal","left_drift","slow_push","right_drift","static_hold","premium_float"]),
        audio=_au(1.55, 0.122, 0.048, duck=0.18), variation_seed=1700)

    p8 = EditingPreset(preset_id=f"{niche}_preset_8", preset_number=8, niche=niche, label="Tech Revolution",
        description="Tech revolution style. Bold, fast, disruptive. Startup pitch energy meets sci-fi visuals.",
        motion=_m(["diagonal_reverse","left_to_right","bottom_to_top","center_push","right_to_left","top_to_bottom","diagonal_soft","gentle_float_up"], zoom_min=1.068, zoom_max=1.138, zoom_step=0.00065, use_static=False, static_every=11),
        transition=_t(["fadewhite","wipeleft","slideright","pixelize","fadewhite","wiperight","rectcrop","smoothleft"], gap=6, dur_base=0.22, dur_lo=0.08, dur_hi=0.30),
        cut_rhythm=_c(0.6,1.3, 2.2,4.5, 3.5,6.0, 2.8,4.5),
        color=_g("eq=contrast=1.055:saturation=1.050:brightness=0.000", -0.03, 0.020, 0.012, 0.15),
        animation=_a(["hook_punch","left_drift","right_drift","up_drift","down_drift","mystery_creep","diagonal_reverse","premium_float"]),
        audio=_au(1.48, 0.175, 0.098, duck=0.34), variation_seed=1800)

    return [p1, p2, p3, p4, p5, p6, p7, p8]


def _build_mystery_presets() -> List[EditingPreset]:
    niche = "mystery"
    return [
        EditingPreset(preset_id=f"{niche}_preset_1", preset_number=1, niche=niche, label="Noir",
            description="Classic film noir. High contrast B&W feel, slow reveals, shadowy atmosphere. For crime/thriller.",
            motion=_m(["slow_pan_right","static_hold","center_push","gentle_float_up","left_to_right","gentle_float_down","slow_pan_left","diagonal_soft"], zoom_min=1.030, zoom_max=1.072, zoom_step=0.00034, use_static=True, static_every=4),
            transition=_t(["dissolve","fade","dissolve","blur","dissolve","fade","circleclose","dissolve"], gap=3, dur_base=0.42, dur_lo=0.22, dur_hi=0.58),
            cut_rhythm=_c(2.5,4.0, 5.5,8.5, 9.0,13.0, 7.0,10.0),
            color=_g("eq=contrast=1.068:saturation=0.985:brightness=-0.015", -0.05, 0.040, 0.025, 0.09),
            animation=_a(["soft_reveal","subtle_zoom_in","documentary_hold","left_drift","slow_push","right_drift","static_hold","mystery_creep"]),
            audio=_au(1.60, 0.108, 0.042, duck=0.14), variation_seed=2100),
        EditingPreset(preset_id=f"{niche}_preset_2", preset_number=2, niche=niche, label="Suspense",
            description="Building tension. Slow zooms, long pauses, dramatic reveals. Heartbeat rhythm.",
            motion=_m(["static_hold","center_push","gentle_float_up","slow_pan_right","left_to_right","gentle_float_down","diagonal_soft","static_hold"], zoom_min=1.028, zoom_max=1.068, zoom_step=0.00030, use_static=True, static_every=3),
            transition=_t(["dissolve","fade","circleopen","blur","dissolve","fade","dissolve","circleclose"], gap=3, dur_base=0.45, dur_lo=0.25, dur_hi=0.60),
            cut_rhythm=_c(3.0,4.5, 6.0,9.0, 10.0,14.0, 8.0,11.0),
            color=_g("eq=contrast=1.055:saturation=0.992:brightness=-0.008", -0.03, 0.038, 0.022, 0.08),
            animation=_a(["mystery_creep","soft_reveal","subtle_zoom_in","documentary_hold","left_drift","slow_push","right_drift","static_hold"]),
            audio=_au(1.62, 0.102, 0.038, duck=0.12), variation_seed=2200),
        EditingPreset(preset_id=f"{niche}_preset_3", preset_number=3, niche=niche, label="Fast Thriller",
            description="Rapid-fire thriller pacing. Quick cuts, jerky motion, high anxiety. For action/crime scenes.",
            motion=_m(["diagonal_reverse","right_to_left","bottom_to_top","left_to_right","top_to_bottom","center_push","diagonal_soft","gentle_float_down"], zoom_min=1.068, zoom_max=1.140, zoom_step=0.00068, use_static=False, static_every=12),
            transition=_t(["pixelize","wipeleft","wiperight","rectcrop","wipedown","wipeup","pixelize","slideright"], gap=5, dur_base=0.20, dur_lo=0.08, dur_hi=0.30),
            cut_rhythm=_c(0.7,1.5, 2.5,4.5, 4.0,6.5, 3.0,5.0),
            color=_g("eq=contrast=1.065:saturation=1.035:brightness=-0.005", -0.04, 0.018, 0.015, 0.14),
            animation=_a(["hook_punch","left_drift","right_drift","up_drift","down_drift","diagonal_reverse","diagonal_soft","mystery_creep"]),
            audio=_au(1.45, 0.172, 0.098, duck=0.34), variation_seed=2300),
        EditingPreset(preset_id=f"{niche}_preset_4", preset_number=4, niche=niche, label="Detective",
            description="Methodical detective work. Steady pacing, evidence reveals, logical flow. For true crime docs.",
            motion=_m(["slow_pan_right","center_push","static_hold","slow_pan_left","left_to_right","gentle_float_up","diagonal_soft","gentle_float_down"], zoom_min=1.035, zoom_max=1.082, zoom_step=0.00038, use_static=True, static_every=5),
            transition=_t(["dissolve","fade","smoothleft","dissolve","fade","smoothright","blur","dissolve"], gap=4, dur_base=0.38, dur_lo=0.20, dur_hi=0.50),
            cut_rhythm=_c(1.8,3.0, 4.5,7.5, 8.0,11.0, 6.0,9.0),
            color=_g("eq=contrast=1.045:saturation=1.008:brightness=-0.005", -0.02, 0.028, 0.018, 0.11),
            animation=_a(["documentary_hold","subtle_zoom_in","soft_reveal","left_drift","slow_push","right_drift","static_hold","mystery_creep"]),
            audio=_au(1.58, 0.128, 0.052, duck=0.20), variation_seed=2400),
        EditingPreset(preset_id=f"{niche}_preset_5", preset_number=5, niche=niche, label="Paranormal",
            description="Supernatural horror. Unnatural motion, glitch effects, eerie atmosphere. For ghost/paranormal.",
            motion=_m(["gentle_float_up","diagonal_reverse","static_hold","gentle_float_down","left_to_right","right_to_left","diagonal_soft","center_push"], zoom_min=1.048, zoom_max=1.112, zoom_step=0.00052, use_static=True, static_every=7),
            transition=_t(["pixelize","blur","rectcrop","circleopen","pixelize","fade","dissolve","circleclose"], gap=5, dur_base=0.28, dur_lo=0.12, dur_hi=0.38),
            cut_rhythm=_c(1.5,2.8, 4.0,7.0, 6.5,10.0, 5.0,8.0),
            color=_g("eq=contrast=1.062:saturation=0.978:brightness=-0.010", -0.06, 0.042, 0.022, 0.12),
            animation=_a(["mystery_creep","soft_reveal","subtle_zoom_in","left_drift","right_drift","diagonal_reverse","diagonal_soft","hook_punch"]),
            audio=_au(1.52, 0.138, 0.062, duck=0.24), variation_seed=2500),
        EditingPreset(preset_id=f"{niche}_preset_6", preset_number=6, niche=niche, label="Interrogation",
            description="Tense interview/interrogation feel. Close-ups, minimal motion, intense eye contact. Drama focus.",
            motion=_m(["static_hold","center_push","gentle_float_up","slow_pan_right","left_to_right","static_hold","gentle_float_down","slow_pan_left"], zoom_min=1.022, zoom_max=1.058, zoom_step=0.00025, use_static=True, static_every=2),
            transition=_t(["dissolve","fade","dissolve","fade","blur","dissolve","fade","dissolve"], gap=2, dur_base=0.48, dur_lo=0.28, dur_hi=0.62),
            cut_rhythm=_c(2.8,4.2, 6.0,9.5, 10.0,14.0, 8.5,12.0),
            color=_g("eq=contrast=1.058:saturation=0.985:brightness=-0.008", -0.01, 0.032, 0.020, 0.10),
            animation=_a(["soft_reveal","subtle_zoom_in","documentary_hold","left_drift","static_hold","right_drift","slow_push","mystery_creep"]),
            audio=_au(1.65, 0.095, 0.035, duck=0.10), variation_seed=2600),
        EditingPreset(preset_id=f"{niche}_preset_7", preset_number=7, niche=niche, label="Evidence Board",
            description="Crime board aesthetic. Push pins, red string connections, map overlays. For unsolved cases.",
            motion=_m(["center_push","left_to_right","gentle_float_up","static_hold","slow_pan_right","diagonal_soft","gentle_float_down","right_to_left"], zoom_min=1.052, zoom_max=1.115, zoom_step=0.00054, use_static=True, static_every=6),
            transition=_t(["rectcrop","wipeleft","wiperight","circleopen","rectcrop","smoothleft","smoothright","dissolve"], gap=5, dur_base=0.25, dur_lo=0.12, dur_hi=0.36),
            cut_rhythm=_c(1.2,2.4, 3.5,6.0, 5.5,8.5, 4.5,7.0),
            color=_g("eq=contrast=1.052:saturation=1.028:brightness=-0.003", -0.04, 0.025, 0.016, 0.12),
            animation=_a(["hook_punch","left_drift","right_drift","soft_reveal","up_drift","down_drift","mystery_creep","subtle_zoom_in"]),
            audio=_au(1.50, 0.145, 0.072, duck=0.26), variation_seed=2700),
        EditingPreset(preset_id=f"{niche}_preset_8", preset_number=8, niche=niche, label="Twist Ending",
            description="M. Night Shyamalan style. Slow burn, sudden reveals, dramatic contrast shifts. Plot twist energy.",
            motion=_m(["slow_pan_right","static_hold","gentle_float_up","center_push","left_to_right","gentle_float_down","diagonal_soft","slow_pan_left"], zoom_min=1.032, zoom_max=1.078, zoom_step=0.00036, use_static=True, static_every=4),
            transition=_t(["dissolve","fade","blur","circleopen","dissolve","fadewhite","circleclose","dissolve"], gap=4, dur_base=0.40, dur_lo=0.20, dur_hi=0.55),
            cut_rhythm=_c(2.0,3.5, 5.0,8.0, 8.5,12.0, 6.5,9.5),
            color=_g("eq=contrast=1.048:saturation=1.015:brightness=-0.004", 0.02, 0.030, 0.020, 0.11),
            animation=_a(["mystery_creep","soft_reveal","subtle_zoom_in","documentary_hold","premium_float","slow_push","static_hold","hook_punch"]),
            audio=_au(1.58, 0.118, 0.048, duck=0.16), variation_seed=2800),
    ]


def _build_stoic_wisdom_presets() -> List[EditingPreset]:
    niche = "stoic_wisdom"
    return [
        EditingPreset(preset_id=f"{niche}_preset_1", preset_number=1, niche=niche, label="Morning Meditations",
            description="Calm sunrise energy. Slow pans, warm light, gentle dissolves. For morning routine/philosophy.",
            motion=_m(["gentle_float_up","slow_pan_right","center_push","static_hold","left_to_right","gentle_float_down","diagonal_soft","slow_pan_left"], zoom_min=1.025, zoom_max=1.065, zoom_step=0.00028, use_static=True, static_every=4),
            transition=_t(["dissolve","fade","dissolve","fade","dissolve","circleopen","dissolve","fade"], gap=3, dur_base=0.42, dur_lo=0.22, dur_hi=0.55),
            cut_rhythm=_c(2.2,3.5, 5.0,8.0, 8.0,11.0, 6.5,9.5),
            color=_g("eq=contrast=1.028:saturation=1.012:brightness=0.006", 0.06, 0.015, 0.010, 0.12),
            animation=_a(["soft_reveal","subtle_zoom_in","documentary_hold","left_drift","slow_push","right_drift","static_hold","premium_float"]),
            audio=_au(1.58, 0.112, 0.042, duck=0.13), variation_seed=3100),
        EditingPreset(preset_id=f"{niche}_preset_2", preset_number=2, niche=niche, label="Stoic Discipline",
            description="Strong, grounded. Dark contrast, firm cuts, steady motion. For discipline/mental toughness.",
            motion=_m(["center_push","static_hold","slow_pan_right","left_to_right","gentle_float_up","gentle_float_down","diagonal_soft","center_push"], zoom_min=1.032, zoom_max=1.078, zoom_step=0.00035, use_static=True, static_every=5),
            transition=_t(["smoothleft","dissolve","smoothright","dissolve","circleclose","smoothleft","fade","dissolve"], gap=4, dur_base=0.35, dur_lo=0.18, dur_hi=0.45),
            cut_rhythm=_c(1.8,3.0, 4.5,7.5, 7.0,10.0, 6.0,8.5),
            color=_g("eq=contrast=1.042:saturation=1.008:brightness=-0.004", -0.01, 0.022, 0.012, 0.13),
            animation=_a(["documentary_hold","subtle_zoom_in","soft_reveal","left_drift","slow_push","right_drift","static_hold","premium_float"]),
            audio=_au(1.55, 0.125, 0.050, duck=0.20), variation_seed=3200),
        EditingPreset(preset_id=f"{niche}_preset_3", preset_number=3, niche=niche, label="Ancient Wisdom",
            description="Classical, timeless. Vintage tones, slow reveals, philosophical pacing. For quotes/teachings.",
            motion=_m(["slow_pan_right","static_hold","center_push","gentle_float_up","left_to_right","slow_pan_left","diagonal_soft","gentle_float_down"], zoom_min=1.028, zoom_max=1.072, zoom_step=0.00032, use_static=True, static_every=4),
            transition=_t(["dissolve","fade","circleopen","dissolve","fade","blur","circleclose","dissolve"], gap=4, dur_base=0.45, dur_lo=0.24, dur_hi=0.58),
            cut_rhythm=_c(2.5,3.8, 5.5,8.5, 9.0,12.0, 7.0,10.0),
            color=_g("eq=contrast=1.025:saturation=1.035:brightness=0.002", 0.08, 0.022, 0.018, 0.10),
            animation=_a(["premium_float","soft_reveal","subtle_zoom_in","documentary_hold","left_drift","slow_push","right_drift","static_hold"]),
            audio=_au(1.60, 0.108, 0.040, duck=0.12), variation_seed=3300),
        EditingPreset(preset_id=f"{niche}_preset_4", preset_number=4, niche=niche, label="Mindful Flow",
            description="Meditative, flowing. Gentle floats, soft transitions, breathing rhythm. For mindfulness content.",
            motion=_m(["gentle_float_up","gentle_float_down","gentle_float_up","gentle_float_down","slow_pan_right","slow_pan_left","center_push","static_hold"], zoom_min=1.020, zoom_max=1.055, zoom_step=0.00022, use_static=True, static_every=3),
            transition=_t(["fade","dissolve","fade","dissolve","fade","dissolve","fade","dissolve"], gap=2, dur_base=0.48, dur_lo=0.28, dur_hi=0.62),
            cut_rhythm=_c(2.8,4.5, 6.0,9.5, 10.0,14.0, 8.0,11.5),
            color=_g("eq=contrast=1.020:saturation=1.010:brightness=0.008", 0.04, 0.010, 0.008, 0.10),
            animation=_a(["soft_reveal","subtle_zoom_in","documentary_hold","gentle_float_up","gentle_float_down","slow_push","static_hold","diagonal_soft"]),
            audio=_au(1.62, 0.098, 0.035, duck=0.08), variation_seed=3400),
        EditingPreset(preset_id=f"{niche}_preset_5", preset_number=5, niche=niche, label="Warrior",
            description="Spartan mindset. Sharp contrast, punchy cuts, aggressive zooms. For motivational/hustle content.",
            motion=_m(["diagonal_reverse","center_push","left_to_right","right_to_left","bottom_to_top","top_to_bottom","diagonal_soft","gentle_float_down"], zoom_min=1.058, zoom_max=1.128, zoom_step=0.00060, use_static=False, static_every=11),
            transition=_t(["wipeleft","wiperight","fadewhite","pixelize","wipeup","wipedown","slideright","smoothleft"], gap=5, dur_base=0.25, dur_lo=0.10, dur_hi=0.35),
            cut_rhythm=_c(0.8,1.8, 2.8,5.2, 4.5,7.0, 3.5,5.5),
            color=_g("eq=contrast=1.058:saturation=1.035:brightness=-0.003", -0.04, 0.020, 0.014, 0.14),
            animation=_a(["hook_punch","left_drift","right_drift","up_drift","down_drift","diagonal_reverse","diagonal_soft","mystery_creep"]),
            audio=_au(1.48, 0.168, 0.095, duck=0.32), variation_seed=3500),
        EditingPreset(preset_id=f"{niche}_preset_6", preset_number=6, niche=niche, label="Evening Reflection",
            description="Twilight introspection. Warm sunset tones, slow pans, reflective mood. For end-of-day philosophy.",
            motion=_m(["static_hold","gentle_float_up","slow_pan_right","center_push","left_to_right","gentle_float_down","diagonal_soft","static_hold"], zoom_min=1.022, zoom_max=1.060, zoom_step=0.00026, use_static=True, static_every=3),
            transition=_t(["dissolve","fade","dissolve","fade","blur","dissolve","fade","circleclose"], gap=3, dur_base=0.44, dur_lo=0.24, dur_hi=0.58),
            cut_rhythm=_c(2.5,3.8, 5.5,8.5, 9.0,12.0, 7.0,10.0),
            color=_g("eq=contrast=1.022:saturation=1.018:brightness=0.004", 0.07, 0.018, 0.012, 0.09),
            animation=_a(["soft_reveal","subtle_zoom_in","documentary_hold","left_drift","slow_push","right_drift","static_hold","premium_float"]),
            audio=_au(1.60, 0.105, 0.040, duck=0.11), variation_seed=3600),
        EditingPreset(preset_id=f"{niche}_preset_7", preset_number=7, niche=niche, label="Nature",
            description="Outdoor philosophy. Natural light, organic pans, earthy tones. For nature/wisdom combination.",
            motion=_m(["slow_pan_right","slow_pan_left","gentle_float_up","center_push","static_hold","gentle_float_down","diagonal_soft","left_to_right"], zoom_min=1.030, zoom_max=1.075, zoom_step=0.00033, use_static=True, static_every=5),
            transition=_t(["dissolve","fade","smoothleft","dissolve","fade","smoothright","circleopen","dissolve"], gap=3, dur_base=0.38, dur_lo=0.20, dur_hi=0.50),
            cut_rhythm=_c(2.0,3.2, 4.8,7.5, 7.5,10.5, 6.0,8.5),
            color=_g("eq=contrast=1.030:saturation=1.025:brightness=0.005", 0.05, 0.015, 0.010, 0.12),
            animation=_a(["premium_float","gentle_float_up","gentle_float_down","soft_reveal","subtle_zoom_in","diagonal_soft","left_drift","right_drift"]),
            audio=_au(1.55, 0.118, 0.048, duck=0.16), variation_seed=3700),
        EditingPreset(preset_id=f"{niche}_preset_8", preset_number=8, niche=niche, label="Minimalist",
            description="Minimal aesthetic. White space, clean lines, intentional stillness. For simplicity philosophy.",
            motion=_m(["static_hold","center_push","static_hold","gentle_float_up","static_hold","left_to_right","static_hold","diagonal_soft"], zoom_min=1.018, zoom_max=1.050, zoom_step=0.00020, use_static=True, static_every=2),
            transition=_t(["fade","dissolve","fade","dissolve","fade","dissolve","fade","dissolve"], gap=2, dur_base=0.50, dur_lo=0.30, dur_hi=0.65),
            cut_rhythm=_c(3.0,4.8, 6.5,10.0, 11.0,16.0, 9.0,13.0),
            color=_g("eq=contrast=1.018:saturation=1.005:brightness=0.010", 0.02, 0.008, 0.006, 0.11),
            animation=_a(["soft_reveal","subsection_zoom_in","documentary_hold","static_hold","left_drift","right_drift","slow_push","premium_float"]),
            audio=_au(1.65, 0.092, 0.030, duck=0.06), variation_seed=3800),
    ]


def _build_interior_design_presets() -> List[EditingPreset]:
    niche = "interior_design"
    return [
        EditingPreset(preset_id=f"{niche}_preset_1", preset_number=1, niche=niche, label="Scandi Minimal",
            description="Scandinavian minimalism. Clean lines, bright whites, natural light. For modern home tours.",
            motion=_m(["slow_pan_right","center_push","gentle_float_up","static_hold","left_to_right","gentle_float_down","diagonal_soft","slow_pan_left"], zoom_min=1.028, zoom_max=1.072, zoom_step=0.00032, use_static=True, static_every=4),
            transition=_t(["smoothleft","dissolve","smoothright","dissolve","fade","smoothleft","circleopen","dissolve"], gap=3, dur_base=0.35, dur_lo=0.18, dur_hi=0.45),
            cut_rhythm=_c(1.6,2.5, 4.0,6.5, 6.0,8.5, 5.0,7.5),
            color=_g("eq=contrast=1.025:saturation=1.010:brightness=0.008", 0.02, 0.010, 0.006, 0.14),
            animation=_a(["soft_reveal","subtle_zoom_in","documentary_hold","left_drift","slow_push","right_drift","static_hold","premium_float"]),
            audio=_au(1.55, 0.122, 0.048, duck=0.16), variation_seed=4100),
        EditingPreset(preset_id=f"{niche}_preset_2", preset_number=2, niche=niche, label="Industrial Loft",
            description="Urban industrial. Raw textures, exposed brick, metal accents. For warehouse conversions.",
            motion=_m(["center_push","static_hold","left_to_right","gentle_float_up","diagonal_soft","right_to_left","gentle_float_down","center_push"], zoom_min=1.035, zoom_max=1.082, zoom_step=0.00040, use_static=True, static_every=5),
            transition=_t(["wipeleft","dissolve","wiperight","rectcrop","wipeup","wipedown","smoothleft","smoothright"], gap=4, dur_base=0.30, dur_lo=0.14, dur_hi=0.40),
            cut_rhythm=_c(1.4,2.4, 3.8,6.2, 5.5,8.0, 4.5,7.0),
            color=_g("eq=contrast=1.045:saturation=1.018:brightness=-0.003", -0.03, 0.022, 0.014, 0.13),
            animation=_a(["hook_punch","left_drift","right_drift","diagonal_soft","slow_push","soft_reveal","diagonal_reverse","subtle_zoom_in"]),
            audio=_au(1.50, 0.138, 0.065, duck=0.22), variation_seed=4200),
        EditingPreset(preset_id=f"{niche}_preset_3", preset_number=3, niche=niche, label="Japandi",
            description="Japanese-Scandinavian fusion. Warm wood, wabi-sabi, zen spaces. For serene home environments.",
            motion=_m(["gentle_float_up","slow_pan_right","static_hold","center_push","left_to_right","gentle_float_down","diagonal_soft","slow_pan_left"], zoom_min=1.025, zoom_max=1.068, zoom_step=0.00030, use_static=True, static_every=4),
            transition=_t(["dissolve","fade","dissolve","fade","dissolve","circleopen","dissolve","fade"], gap=3, dur_base=0.40, dur_lo=0.22, dur_hi=0.52),
            cut_rhythm=_c(2.0,3.2, 5.0,7.5, 7.5,10.0, 6.0,8.5),
            color=_g("eq=contrast=1.022:saturation=1.020:brightness=0.005", 0.04, 0.014, 0.010, 0.11),
            animation=_a(["soft_reveal","subtle_zoom_in","documentary_hold","premium_float","left_drift","slow_push","static_hold","diagonal_soft"]),
            audio=_au(1.58, 0.112, 0.042, duck=0.13), variation_seed=4300),
        EditingPreset(preset_id=f"{niche}_preset_4", preset_number=4, niche=niche, label="Maximalist",
            description="Bold maximalism. Rich colors, layered textures, fast pans. For eclectic/vibrant spaces.",
            motion=_m(["diagonal_reverse","left_to_right","bottom_to_top","center_push","right_to_left","top_to_bottom","diagonal_soft","gentle_float_down"], zoom_min=1.055, zoom_max=1.120, zoom_step=0.00055, use_static=False, static_every=10),
            transition=_t(["fadewhite","wipeleft","slideright","pixelize","wiperight","circleopen","smoothleft","smoothright"], gap=5, dur_base=0.25, dur_lo=0.10, dur_hi=0.35),
            cut_rhythm=_c(0.9,1.8, 3.0,5.2, 5.0,7.5, 3.5,5.5),
            color=_g("eq=contrast=1.055:saturation=1.055:brightness=0.002", -0.05, 0.018, 0.014, 0.12),
            animation=_a(["hook_punch","left_drift","right_drift","up_drift","down_drift","diagonal_reverse","diagonal_soft","premium_float"]),
            audio=_au(1.48, 0.165, 0.090, duck=0.30), variation_seed=4400),
        EditingPreset(preset_id=f"{niche}_preset_5", preset_number=5, niche=niche, label="Before & After",
            description="Renovation reveal style. Split screens, dramatic reveals, contrast emphasis. For makeover videos.",
            motion=_m(["center_push","gentle_float_up","static_hold","left_to_right","slow_pan_right","gentle_float_down","diagonal_soft","center_push"], zoom_min=1.048, zoom_max=1.108, zoom_step=0.00050, use_static=True, static_every=6),
            transition=_t(["wipeleft","wiperight","rectcrop","fadewhite","wipeup","wipedown","circleopen","slideleft"], gap=5, dur_base=0.28, dur_lo=0.12, dur_hi=0.38),
            cut_rhythm=_c(1.0,2.0, 3.2,5.5, 5.0,7.5, 4.0,6.0),
            color=_g("eq=contrast=1.052:saturation=1.042:brightness=0.003", -0.02, 0.020, 0.012, 0.13),
            animation=_a(["hook_punch","soft_reveal","subtle_zoom_in","left_drift","right_drift","diagonal_soft","slow_push","premium_float"]),
            audio=_au(1.50, 0.150, 0.078, duck=0.26), variation_seed=4500),
        EditingPreset(preset_id=f"{niche}_preset_6", preset_number=6, niche=niche, label="Luxury Estate",
            description="High-end real estate. Smooth pans, warm tones, cinematic flow. For luxury property tours.",
            motion=_m(["slow_pan_right","center_push","gentle_float_up","static_hold","left_to_right","slow_pan_left","diagonal_soft","premium_float"], zoom_min=1.032, zoom_max=1.078, zoom_step=0.00036, use_static=True, static_every=5),
            transition=_t(["dissolve","fade","circleopen","dissolve","fade","smoothleft","circleclose","dissolve"], gap=4, dur_base=0.38, dur_lo=0.20, dur_hi=0.50),
            cut_rhythm=_c(1.8,3.0, 4.5,7.5, 7.0,10.0, 5.5,8.5),
            color=_g("eq=contrast=1.038:saturation=1.022:brightness=0.004", 0.03, 0.016, 0.010, 0.13),
            animation=_a(["premium_float","soft_reveal","subtle_zoom_in","documentary_hold","left_drift","slow_push","right_drift","static_hold"]),
            audio=_au(1.55, 0.125, 0.052, duck=0.18), variation_seed=4600),
        EditingPreset(preset_id=f"{niche}_preset_7", preset_number=7, niche=niche, label="Tiny Home",
            description="Small space genius. Warm cozy tones, gentle flows, clever reveals. For apartments/tiny homes.",
            motion=_m(["center_push","gentle_float_up","static_hold","slow_pan_right","left_to_right","gentle_float_down","diagonal_soft","center_push"], zoom_min=1.032, zoom_max=1.078, zoom_step=0.00036, use_static=True, static_every=4),
            transition=_t(["smoothleft","dissolve","smoothright","dissolve","circleopen","smoothleft","fade","dissolve"], gap=3, dur_base=0.36, dur_lo=0.18, dur_hi=0.48),
            cut_rhythm=_c(1.6,2.6, 4.2,6.8, 6.5,9.0, 5.0,7.5),
            color=_g("eq=contrast=1.030:saturation=1.025:brightness=0.004", 0.04, 0.012, 0.008, 0.12),
            animation=_a(["soft_reveal","subtle_zoom_in","documentary_hold","left_drift","slow_push","right_drift","static_hold","premium_float"]),
            audio=_au(1.55, 0.120, 0.045, duck=0.15), variation_seed=4700),
        EditingPreset(preset_id=f"{niche}_preset_8", preset_number=8, niche=niche, label="Architectural",
            description="Clean architectural lines. Straight pans, geometric cuts, structure emphasis. For design docs.",
            motion=_m(["left_to_right","center_push","right_to_left","top_to_bottom","bottom_to_top","static_hold","diagonal_soft","slow_pan_right"], zoom_min=1.038, zoom_max=1.088, zoom_step=0.00042, use_static=True, static_every=5),
            transition=_t(["rectcrop","wipeleft","wiperight","slideleft","slideright","smoothleft","smoothright","rectcrop"], gap=5, dur_base=0.28, dur_lo=0.14, dur_hi=0.38),
            cut_rhythm=_c(1.2,2.2, 3.5,6.0, 5.5,8.0, 4.0,6.5),
            color=_g("eq=contrast=1.045:saturation=1.012:brightness=0.000", -0.02, 0.018, 0.010, 0.15),
            animation=_a(["left_drift","right_drift","up_drift","down_drift","diagonal_soft","hook_punch","slow_push","soft_reveal"]),
            audio=_au(1.52, 0.132, 0.058, duck=0.22), variation_seed=4800),
    ]


def _build_finance_simulation_presets() -> List[EditingPreset]:
    niche = "finance_simulation"
    return [
        EditingPreset(preset_id=f"{niche}_preset_1", preset_number=1, niche=niche, label="Wall Street",
            description="NYC trading floor energy. Fast cuts, data flow, high contrast. For stock market/news.",
            motion=_m(["diagonal_reverse","left_to_right","bottom_to_top","center_push","right_to_left","top_to_bottom","diagonal_soft","gentle_float_down"], zoom_min=1.065, zoom_max=1.135, zoom_step=0.00062, use_static=False, static_every=10),
            transition=_t(["wipeleft","wiperight","slideright","pixelize","wipeup","wipedown","fadewhite","smoothleft"], gap=5, dur_base=0.22, dur_lo=0.08, dur_hi=0.32),
            cut_rhythm=_c(0.7,1.4, 2.4,4.5, 4.0,6.5, 3.0,5.0),
            color=_g("eq=contrast=1.060:saturation=1.045:brightness=-0.002", -0.05, 0.015, 0.012, 0.15),
            animation=_a(["hook_punch","left_drift","right_drift","up_drift","down_drift","diagonal_reverse","diagonal_soft","subtle_zoom_in"]),
            audio=_au(1.48, 0.175, 0.098, duck=0.32), variation_seed=5100),
        EditingPreset(preset_id=f"{niche}_preset_2", preset_number=2, niche=niche, label="Buffett Style",
            description="Warren Buffett calm. Steady pacing, wise dissolves, timeless feel. For value investing content.",
            motion=_m(["slow_pan_right","center_push","static_hold","gentle_float_up","left_to_right","gentle_float_down","diagonal_soft","slow_pan_left"], zoom_min=1.030, zoom_max=1.075, zoom_step=0.00033, use_static=True, static_every=4),
            transition=_t(["dissolve","fade","dissolve","fade","dissolve","circleopen","dissolve","fade"], gap=3, dur_base=0.40, dur_lo=0.22, dur_hi=0.52),
            cut_rhythm=_c(1.8,3.0, 4.8,7.5, 7.5,10.5, 6.0,8.5),
            color=_g("eq=contrast=1.030:saturation=1.015:brightness=0.005", 0.03, 0.015, 0.010, 0.12),
            animation=_a(["documentary_hold","subtle_zoom_in","soft_reveal","premium_float","left_drift","slow_push","right_drift","static_hold"]),
            audio=_au(1.55, 0.122, 0.048, duck=0.16), variation_seed=5200),
        EditingPreset(preset_id=f"{niche}_preset_3", preset_number=3, niche=niche, label="Crypto",
            description="Crypto/web3 energy. Neon, glitch, ultra-fast. For crypto/NFT/blockchain content.",
            motion=_m(["diagonal_reverse","bottom_to_top","left_to_right","center_push","right_to_left","diagonal_soft","top_to_bottom","gentle_float_up"], zoom_min=1.072, zoom_max=1.145, zoom_step=0.00072, use_static=False, static_every=12),
            transition=_t(["pixelize","rectcrop","fadewhite","wipeleft","wiperight","pixelize","slideright","circleopen"], gap=6, dur_base=0.18, dur_lo=0.06, dur_hi=0.28),
            cut_rhythm=_c(0.5,1.2, 2.0,4.0, 3.5,6.0, 2.5,4.5),
            color=_g("eq=contrast=1.065:saturation=1.060:brightness=0.000", -0.08, 0.020, 0.014, 0.16),
            animation=_a(["hook_punch","mystery_creep","left_drift","right_drift","up_drift","down_drift","diagonal_reverse","diagonal_soft"]),
            audio=_au(1.45, 0.180, 0.105, duck=0.36), variation_seed=5300),
        EditingPreset(preset_id=f"{niche}_preset_4", preset_number=4, niche=niche, label="Real Estate",
            description="Property investment. Clean, professional, ROI focused. For real estate/rental content.",
            motion=_m(["center_push","slow_pan_right","gentle_float_up","static_hold","left_to_right","gentle_float_down","diagonal_soft","slow_pan_left"], zoom_min=1.035, zoom_max=1.082, zoom_step=0.00038, use_static=True, static_every=5),
            transition=_t(["smoothleft","dissolve","smoothright","dissolve","circleopen","smoothleft","fade","dissolve"], gap=4, dur_base=0.35, dur_lo=0.18, dur_hi=0.45),
            cut_rhythm=_c(1.6,2.6, 4.2,6.8, 6.5,9.0, 5.0,7.5),
            color=_g("eq=contrast=1.038:saturation=1.022:brightness=0.004", 0.02, 0.018, 0.010, 0.14),
            animation=_a(["soft_reveal","subtle_zoom_in","documentary_hold","left_drift","slow_push","right_drift","static_hold","premium_float"]),
            audio=_au(1.52, 0.128, 0.055, duck=0.20), variation_seed=5400),
        EditingPreset(preset_id=f"{niche}_preset_5", preset_number=5, niche=niche, label="Frugal Living",
            description="Budget/saving focus. Warm, relatable, down-to-earth. For frugal life/financial tips.",
            motion=_m(["gentle_float_up","center_push","static_hold","slow_pan_right","left_to_right","gentle_float_down","diagonal_soft","slow_pan_left"], zoom_min=1.028, zoom_max=1.070, zoom_step=0.00030, use_static=True, static_every=4),
            transition=_t(["dissolve","fade","dissolve","fade","dissolve","circleclose","fade","dissolve"], gap=3, dur_base=0.38, dur_lo=0.20, dur_hi=0.50),
            cut_rhythm=_c(1.8,2.8, 4.5,7.0, 7.0,10.0, 5.5,8.0),
            color=_g("eq=contrast=1.025:saturation=1.018:brightness=0.006", 0.05, 0.012, 0.008, 0.11),
            animation=_a(["soft_reveal","subtle_zoom_in","documentary_hold","premium_float","left_drift","slow_push","right_drift","static_hold"]),
            audio=_au(1.55, 0.118, 0.045, duck=0.15), variation_seed=5500),
        EditingPreset(preset_id=f"{niche}_preset_6", preset_number=6, niche=niche, label="IPO / Launch",
            description="Big announcement energy. Bold reveals, dramatic cuts, celebration vibe. For launches/milestones.",
            motion=_m(["center_push","diagonal_reverse","left_to_right","bottom_to_top","right_to_left","top_to_bottom","diagonal_soft","gentle_float_up"], zoom_min=1.055, zoom_max=1.125, zoom_step=0.00058, use_static=False, static_every=11),
            transition=_t(["fadewhite","circleopen","wipeleft","wiperight","slideright","fadewhite","circleclose","pixelize"], gap=5, dur_base=0.25, dur_lo=0.10, dur_hi=0.35),
            cut_rhythm=_c(0.8,1.6, 2.8,5.0, 4.5,7.0, 3.2,5.2),
            color=_g("eq=contrast=1.058:saturation=1.050:brightness=0.003", -0.06, 0.018, 0.012, 0.13),
            animation=_a(["hook_punch","premium_float","left_drift","right_drift","up_drift","down_drift","diagonal_reverse","diagonal_soft"]),
            audio=_au(1.46, 0.172, 0.098, duck=0.32), variation_seed=5600),
        EditingPreset(preset_id=f"{niche}_preset_7", preset_number=7, niche=niche, label="Passive Income",
            description="Financial freedom vibe. Relaxed, aspirational, lifestyle-focused. For passive income content.",
            motion=_m(["slow_pan_right","gentle_float_up","center_push","static_hold","left_to_right","gentle_float_down","diagonal_soft","slow_pan_left"], zoom_min=1.030, zoom_max=1.075, zoom_step=0.00033, use_static=True, static_every=5),
            transition=_t(["dissolve","fade","smoothleft","dissolve","fade","smoothright","circleopen","dissolve"], gap=3, dur_base=0.38, dur_lo=0.20, dur_hi=0.50),
            cut_rhythm=_c(1.8,3.0, 4.8,7.5, 7.5,10.5, 6.0,8.5),
            color=_g("eq=contrast=1.028:saturation=1.022:brightness=0.005", 0.06, 0.014, 0.008, 0.11),
            animation=_a(["premium_float","soft_reveal","subtle_zoom_in","documentary_hold","left_drift","slow_push","right_drift","static_hold"]),
            audio=_au(1.55, 0.120, 0.048, duck=0.16), variation_seed=5700),
        EditingPreset(preset_id=f"{niche}_preset_8", preset_number=8, niche=niche, label="Market Crash",
            description="Bear market energy. Red tones, fast cuts, urgency feel. For market drops/financial crisis.",
            motion=_m(["diagonal_reverse","right_to_left","bottom_to_top","center_push","left_to_right","top_to_bottom","diagonal_soft","gentle_float_down"], zoom_min=1.062, zoom_max=1.132, zoom_step=0.00062, use_static=False, static_every=11),
            transition=_t(["wipeleft","wiperight","pixelize","rectcrop","slideright","wipeup","wipedown","fadewhite"], gap=5, dur_base=0.20, dur_lo=0.08, dur_hi=0.30),
            cut_rhythm=_c(0.6,1.3, 2.2,4.2, 3.5,6.0, 2.5,4.5),
            color=_g("eq=contrast=1.065:saturation=1.048:brightness=-0.008", -0.04, 0.025, 0.016, 0.15),
            animation=_a(["hook_punch","left_drift","right_drift","up_drift","down_drift","diagonal_reverse","diagonal_soft","mystery_creep"]),
            audio=_au(1.48, 0.178, 0.102, duck=0.34), variation_seed=5800),
    ]


def _build_default_presets() -> List[EditingPreset]:
    niche = "default"
    return [
        EditingPreset(preset_id=f"{niche}_preset_1", preset_number=1, niche=niche, label="Balanced",
            description="All-purpose balanced preset. Medium pacing, simple dissolves, neutral colors. Works for everything.",
            motion=_m(["slow_pan_right","center_push","gentle_float_up","static_hold","left_to_right","gentle_float_down","diagonal_soft","slow_pan_left"], zoom_min=1.035, zoom_max=1.085, zoom_step=0.00040, use_static=True, static_every=5),
            transition=_t(["dissolve","fade","dissolve","fade","dissolve","smoothleft","dissolve","fade"], gap=3, dur_base=0.35, dur_lo=0.18, dur_hi=0.48),
            cut_rhythm=_c(1.5,2.5, 4.0,7.0, 6.5,9.5, 5.5,8.0),
            color=_g("eq=contrast=1.035:saturation=1.020:brightness=0.002", 0.00, 0.015, 0.010, 0.12),
            animation=_a(["soft_reveal","subtle_zoom_in","documentary_hold","left_drift","slow_push","right_drift","premium_float","hook_punch"]),
            audio=_au(1.52, 0.135, 0.060, duck=0.22), variation_seed=6100),
        EditingPreset(preset_id=f"{niche}_preset_2", preset_number=2, niche=niche, label="Fast",
            description="Quick, energetic, social-media ready. Fast cuts, bold motion. For TikTok/Reels/Shorts.",
            motion=_m(["diagonal_reverse","left_to_right","bottom_to_top","center_push","right_to_left","top_to_bottom","diagonal_soft","gentle_float_down"], zoom_min=1.058, zoom_max=1.128, zoom_step=0.00058, use_static=False, static_every=12),
            transition=_t(["wipeleft","wiperight","slideright","pixelize","wipeup","wipedown","fadewhite","smoothleft"], gap=5, dur_base=0.22, dur_lo=0.08, dur_hi=0.32),
            cut_rhythm=_c(0.7,1.5, 2.4,4.5, 4.0,6.5, 3.0,5.0),
            color=_g("eq=contrast=1.055:saturation=1.045:brightness=0.000", -0.04, 0.018, 0.012, 0.14),
            animation=_a(["hook_punch","left_drift","right_drift","up_drift","down_drift","diagonal_reverse","diagonal_soft","subtle_zoom_out"]),
            audio=_au(1.46, 0.168, 0.095, duck=0.30), variation_seed=6200),
        EditingPreset(preset_id=f"{niche}_preset_3", preset_number=3, niche=niche, label="Slow Cinema",
            description="Slow, deliberate, cinematic. Long takes, minimal cuts. For documentary/art film style.",
            motion=_m(["slow_pan_right","static_hold","gentle_float_up","center_push","left_to_right","gentle_float_down","slow_pan_left","static_hold"], zoom_min=1.025, zoom_max=1.065, zoom_step=0.00028, use_static=True, static_every=3),
            transition=_t(["dissolve","fade","dissolve","fade","blur","dissolve","fade","dissolve"], gap=2, dur_base=0.48, dur_lo=0.28, dur_hi=0.62),
            cut_rhythm=_c(2.5,4.0, 6.0,9.0, 10.0,14.0, 8.0,11.0),
            color=_g("eq=contrast=1.028:saturation=1.012:brightness=0.004", 0.02, 0.020, 0.015, 0.10),
            animation=_a(["soft_reveal","subtle_zoom_in","documentary_hold","left_drift","slow_push","right_drift","static_hold","premium_float"]),
            audio=_au(1.60, 0.105, 0.040, duck=0.12), variation_seed=6300),
        EditingPreset(preset_id=f"{niche}_preset_4", preset_number=4, niche=niche, label="Vlog",
            description="Casual vlog style. Natural, conversational, warm. For daily vlogs/lifestyle.",
            motion=_m(["center_push","gentle_float_up","static_hold","slow_pan_right","left_to_right","gentle_float_down","diagonal_soft","center_push"], zoom_min=1.032, zoom_max=1.078, zoom_step=0.00036, use_static=True, static_every=4),
            transition=_t(["dissolve","fade","smoothleft","dissolve","fade","smoothright","circleopen","dissolve"], gap=3, dur_base=0.35, dur_lo=0.18, dur_hi=0.45),
            cut_rhythm=_c(1.4,2.4, 3.8,6.5, 6.0,9.0, 5.0,7.5),
            color=_g("eq=contrast=1.030:saturation=1.025:brightness=0.004", 0.04, 0.012, 0.008, 0.12),
            animation=_a(["soft_reveal","subtle_zoom_in","documentary_hold","left_drift","slow_push","right_drift","static_hold","premium_float"]),
            audio=_au(1.52, 0.130, 0.058, duck=0.20), variation_seed=6400),
        EditingPreset(preset_id=f"{niche}_preset_5", preset_number=5, niche=niche, label="Tutorial",
            description="Educational focus. Clean, clear, step-by-step. For how-to/explainer videos.",
            motion=_m(["static_hold","center_push","static_hold","slow_pan_right","left_to_right","static_hold","gentle_float_up","center_push"], zoom_min=1.025, zoom_max=1.068, zoom_step=0.00030, use_static=True, static_every=3),
            transition=_t(["smoothleft","dissolve","smoothright","dissolve","rectcrop","smoothleft","fade","dissolve"], gap=3, dur_base=0.32, dur_lo=0.16, dur_hi=0.42),
            cut_rhythm=_c(1.6,2.6, 4.2,7.0, 6.5,9.5, 5.5,8.0),
            color=_g("eq=contrast=1.032:saturation=1.015:brightness=0.005", 0.01, 0.010, 0.006, 0.14),
            animation=_a(["documentary_hold","subtle_zoom_in","soft_reveal","left_drift","slow_push","right_drift","static_hold","premium_float"]),
            audio=_au(1.55, 0.122, 0.050, duck=0.18), variation_seed=6500),
        EditingPreset(preset_id=f"{niche}_preset_6", preset_number=6, niche=niche, label="Product Review",
            description="Review/unboxing style. Detail shots, comparison cuts. For tech/product reviews.",
            motion=_m(["center_push","left_to_right","gentle_float_up","static_hold","right_to_left","gentle_float_down","diagonal_soft","center_push"], zoom_min=1.045, zoom_max=1.105, zoom_step=0.00050, use_static=True, static_every=6),
            transition=_t(["wipeleft","wiperight","rectcrop","smoothleft","smoothright","circleopen","circleclose","dissolve"], gap=4, dur_base=0.28, dur_lo=0.12, dur_hi=0.38),
            cut_rhythm=_c(1.0,2.0, 3.2,5.5, 5.0,7.5, 4.0,6.0),
            color=_g("eq=contrast=1.045:saturation=1.032:brightness=0.002", -0.02, 0.014, 0.010, 0.14),
            animation=_a(["hook_punch","subtle_zoom_in","soft_reveal","left_drift","right_drift","diagonal_soft","slow_push","premium_float"]),
            audio=_au(1.50, 0.142, 0.072, duck=0.24), variation_seed=6600),
        EditingPreset(preset_id=f"{niche}_preset_7", preset_number=7, niche=niche, label="Cinematic",
            description="Hollywood cinematic. Letterbox, film grade, dramatic. For short films/trailers.",
            motion=_m(["slow_pan_right","center_push","gentle_float_up","static_hold","left_to_right","gentle_float_down","diagonal_soft","premium_float"], zoom_min=1.038, zoom_max=1.092, zoom_step=0.00045, use_static=True, static_every=5),
            transition=_t(["dissolve","fade","blur","dissolve","fadewhite","circleopen","dissolve","circleclose"], gap=4, dur_base=0.42, dur_lo=0.22, dur_hi=0.55),
            cut_rhythm=_c(2.0,3.2, 5.0,8.0, 8.0,11.0, 6.0,9.0),
            color=_g("eq=contrast=1.042:saturation=1.018:brightness=-0.004", 0.00, 0.025, 0.018, 0.11),
            animation=_a(["premium_float","soft_reveal","subtle_zoom_in","documentary_hold","left_drift","slow_push","right_drift","static_hold"]),
            audio=_au(1.58, 0.118, 0.048, duck=0.15), variation_seed=6700),
        EditingPreset(preset_id=f"{niche}_preset_8", preset_number=8, niche=niche, label="Memes",
            description="Meme/comedy editing. Random cuts, zooms, fast pace. For humor/viral content.",
            motion=_m(["diagonal_reverse","center_push","left_to_right","bottom_to_top","right_to_left","top_to_bottom","gentle_float_down","diagonal_soft"], zoom_min=1.068, zoom_max=1.142, zoom_step=0.00068, use_static=False, static_every=14),
            transition=_t(["pixelize","wipeleft","wiperight","rectcrop","fadewhite","pixelize","slideright","circleopen"], gap=6, dur_base=0.18, dur_lo=0.06, dur_hi=0.28),
            cut_rhythm=_c(0.5,1.2, 2.0,3.8, 3.0,5.5, 2.2,4.0),
            color=_g("eq=contrast=1.058:saturation=1.058:brightness=0.002", -0.06, 0.022, 0.015, 0.12),
            animation=_a(["hook_punch","mystery_creep","left_drift","right_drift","up_drift","down_drift","diagonal_reverse","diagonal_soft"]),
            audio=_au(1.42, 0.182, 0.108, duck=0.38), variation_seed=6800),
    ]


# ============================================================
# PRESET REGISTRY
# ============================================================

_ALL_PRESETS: Dict[str, List[EditingPreset]] = {}
_PRESET_INDEX: Dict[str, EditingPreset] = {}


def _register_all_presets():
    """Build preset registry from all niche builders."""
    global _ALL_PRESETS, _PRESET_INDEX

    builders = [
        ("luxury_lifestyle", _build_luxury_lifestyle_presets),
        ("quantum_future", _build_future_tech_presets),
        ("mystery", _build_mystery_presets),
        ("stoic_wisdom", _build_stoic_wisdom_presets),
        ("interior_design", _build_interior_design_presets),
        ("finance_simulation", _build_finance_simulation_presets),
        ("default", _build_default_presets),
    ]

    _ALL_PRESETS.clear()
    _PRESET_INDEX.clear()

    for niche_name, builder in builders:
        presets = builder()
        _ALL_PRESETS[niche_name] = presets
        for preset in presets:
            _PRESET_INDEX[preset.preset_id] = preset


# Auto-register on import
_register_all_presets()


# ============================================================
# PUBLIC API
# ============================================================

def get_all_niches() -> List[str]:
    """Return all registered niche names."""
    return list(_ALL_PRESETS.keys())


def get_presets_for_niche(niche: str) -> List[EditingPreset]:
    """Get all 8 presets for a specific niche."""
    if niche not in _ALL_PRESETS:
        raise ValueError(f"Unknown niche: {niche}. Available: {get_all_niches()}")
    return list(_ALL_PRESETS[niche])


def get_preset_by_id(preset_id: str) -> EditingPreset:
    """Get a single preset by its ID."""
    if preset_id not in _PRESET_INDEX:
        raise KeyError(f"Unknown preset ID: {preset_id}")
    return _PRESET_INDEX[preset_id]


def get_preset(niche: str, preset_number: int) -> EditingPreset:
    presets = get_presets_for_niche(niche)
    for p in presets:
        if p.preset_number == preset_number:
            return p
    return presets[0]  # fallback

def get_preset_by_number(preset_number: int, niche: str = "default"):
    # Return preset by number (1-8). Falls back to default niche.
    try:
        if niche == "auto":
            niche = "default"
        return get_preset(niche, preset_number)
    except Exception:
        presets = get_presets_for_niche("default")
        for p in presets:
            if p.preset_number == preset_number:
                return p
        return presets[0] if presets else None

def get_preset_labels(niche: str = "default"):
    # Return list of labels for given niche's 8 presets.
    presets = get_presets_for_niche(niche)
    return [p.label for p in presets[:8]]

def list_all_niches_with_presets():
    # Return {niche_name: [(1, label), (2, label), ...]}
    result = {}
    for niche_name, presets in _ALL_PRESETS.items():
        result[niche_name] = [(p.preset_number, p.label) for p in presets[:8]]
    return result
def get_all_presets() -> Dict[str, List[EditingPreset]]:
    """Get complete preset registry."""
    return dict(_ALL_PRESETS)


def get_total_preset_count() -> int:
    """Total number of presets across all niches."""
    return sum(len(presets) for presets in _ALL_PRESETS.values())


def get_niche_display_name(niche: str) -> str:
    """Human-readable niche name."""
    return NICHE_DISPLAY_NAMES.get(niche, niche.replace("_", " ").title())


def get_niche_family(niche: str) -> str:
    """Get niche family for category grouping."""
    return NICHE_FAMILY_MAP.get(niche, "general")


# ============================================================
# VARIATION ENGINE
# ============================================================

def apply_variation(preset: EditingPreset, clip_index: int, render_count: int = 0) -> Tuple[str, float, float, str, str]:
    """
    Generate per-clip variation from a preset.
    
    Returns: (motion_direction, zoom_val, transition_duration, transition_type, animation_style)
    """
    # Combine seeds for deterministic but varied output
    combined_seed = preset.variation_seed + clip_index * 37 + render_count * 101
    rng = random.Random(combined_seed)

    # Motion
    motion_dir = rng.choice(preset.motion.directions)
    
    # Zoom
    zoom = preset.motion.zoom_min + rng.random() * (preset.motion.zoom_max - preset.motion.zoom_min)
    zoom = round(zoom, 4)

    # Transition
    trans_type = rng.choice(preset.transition.types)
    trans_dur = preset.transition.duration_range[0] + rng.random() * (
        preset.transition.duration_range[1] - preset.transition.duration_range[0]
    )
    trans_dur = round(trans_dur, 3)

    # Animation
    anim_style = rng.choice(preset.animation.styles)

    return motion_dir, zoom, trans_dur, trans_type, anim_style


def get_clip_motion(preset: EditingPreset, clip_index: int, render_count: int = 0) -> Tuple[str, float]:
    """Get per-clip motion direction + zoom."""
    direction, zoom, _, _, _ = apply_variation(preset, clip_index, render_count)
    return direction, zoom


def get_clip_transition(preset: EditingPreset, clip_index: int, render_count: int = 0) -> Tuple[str, float]:
    """Get per-clip transition type + duration."""
    _, _, duration, trans_type, _ = apply_variation(preset, clip_index, render_count)
    return trans_type, duration


def get_clip_animation(preset: EditingPreset, clip_index: int, render_count: int = 0) -> str:
    """Get per-clip animation style."""
    _, _, _, _, anim_style = apply_variation(preset, clip_index, render_count)
    return anim_style


# ============================================================
# FFMPEG FILTER GENERATORS
# ============================================================

def build_ffmpeg_color_filter(preset: EditingPreset) -> str:
    """Build FFmpeg color grade filter string from preset."""
    parts = [preset.color.grade_filter]
    
    if preset.color.vignette_strength > 0:
        parts.append(f"vignette=PI/4:mode=multiply:eval=frame:angle=PI/5")
    
    if preset.color.sharpness > 0:
        parts.append(f"unsharp=5:5:{preset.color.sharpness}:3:3:{preset.color.sharpness * 0.2}")
    
    if preset.color.film_grain_opacity > 0:
        parts.append(f"noise=c0s={int(preset.color.film_grain_opacity * 100)}:all_seed=42")
    
    return ",".join(parts)


def build_ffmpeg_motion_filter(direction: str, zoom_val: float, 
                                 width: int = 1920, height: int = 1080) -> str:
    """Build FFmpeg zoompan filter string for a motion direction."""
    # Base zoompan with direction-based pan offsets
    pan_map = {
        "static_hold": (0, 0),
        "slow_pan_right": (2, 0),
        "slow_pan_left": (-2, 0),
        "gentle_float_up": (0, -1),
        "gentle_float_down": (0, 1),
        "left_to_right": (4, 0),
        "right_to_left": (-4, 0),
        "top_to_bottom": (0, 3),
        "bottom_to_top": (0, -3),
        "center_push": (0, 0),
        "diagonal_soft": (1, -1),
        "diagonal_reverse": (-1, 1),
        "slow_push": (0, 0),
        "premium_float": (0, -2),
    }
    
    px, py = pan_map.get(direction, (0, 0))
    
    return (
        f"zoompan=z='min({zoom_val},2.0)':"
        f"d=1:x='iw/2-(iw/zoom/2)+{px}':"
        f"y='ih/2-(ih/zoom/2)+{py}':s={width}x{height}"
    )


def build_ffmpeg_transition_filter(trans_type: str, duration: float) -> str:
    """Build FFmpeg transition filter (xfade) string."""
    valid_transitions = {
        "dissolve", "fade", "fadewhite", "wipeleft", "wiperight", "wipeup", "wipedown",
        "smoothleft", "smoothright", "slideright", "slideleft", "circleopen", "circleclose",
        "rectcrop", "pixelize", "blur"
    }
    
    if trans_type not in valid_transitions:
        trans_type = "dissolve"
    
    return f"{trans_type}:duration={duration}"


def build_ffmpeg_audio_filter(preset: EditingPreset) -> str:
    """Build FFmpeg audio filter for mixing voice + music + SFX."""
    parts = []
    
    # Voice volume
    parts.append(f"[1:a]volume={preset.audio.voice_volume}[voice]")
    
    # Music ducking
    if preset.audio.ducking_strength > 0:
        parts.append(
            f"[2:a]volume={preset.audio.music_volume},"
            f"sidechaincompress=threshold=0.06:ratio={int(preset.audio.ducking_strength * 100)}:"
            f"attack=5:release=150[music]"
        )
    else:
        parts.append(f"[2:a]volume={preset.audio.music_volume}[music]")
    
    # SFX
    parts.append(f"[3:a]volume={preset.audio.sfx_volume}[sfx]")
    
    # Mix
    parts.append("[voice][music][sfx]amix=3:duration=first:weights=1 1 0.7[mixed]")
    
    # Loudness normalization
    parts.append(f"[mixed]loudnorm=I={preset.audio.target_lufs}:TP=-1.5:LRA=11[out]")
    
    return ";".join(parts)


# ============================================================
# UI / SUMMARIZATION HELPERS
# ============================================================

def get_preset_summary(preset: EditingPreset) -> Dict[str, Any]:
    """Get a concise summary of a preset for UI display."""
    d = preset.to_dict()
    # Simplify for frontend
    d.pop("motion", None)
    d.pop("transition", None)
    d.pop("cut_rhythm", None)
    d.pop("color", None)
    d.pop("animation", None)
    d.pop("audio", None)
    d["niche_display"] = get_niche_display_name(preset.niche)
    d["niche_family"] = get_niche_family(preset.niche)
    return d


def list_all_presets_summary() -> List[Dict[str, Any]]:
    """List all presets with simplified summaries (for UI dropdowns etc)."""
    summaries = []
    for niche in _ALL_PRESETS:
        for preset in _ALL_PRESETS[niche]:
            summaries.append(get_preset_summary(preset))
    return summaries


def get_niches_with_presets() -> List[Dict[str, Any]]:
    """Get all niches with their 8 preset summaries."""
    result = []
    for niche_name in get_all_niches():
        presets = get_presets_for_niche(niche_name)
        result.append({
            "niche": niche_name,
            "display_name": get_niche_display_name(niche_name),
            "family": get_niche_family(niche_name),
            "preset_count": len(presets),
            "presets": [get_preset_summary(p) for p in presets],
        })
    return result


# ============================================================
# MODULE INITIALIZATION
# ============================================================

_total = get_total_preset_count()
_niches = len(get_all_niches())


if __name__ == "__main__":
    """Quick validation when run directly."""
    print(f"niche_editing_presets.py — Loaded: {_total} presets across {_niches} niches")
    print()
    for niche in get_all_niches():
        presets = get_presets_for_niche(niche)
        print(f"  {get_niche_display_name(niche):25s} → {len(presets)} presets")
    print()
    print("Preset Index:")
    for pid in sorted(_PRESET_INDEX.keys()):
        print(f"  {pid}")
    print()
    print("All presets compile OK.")
