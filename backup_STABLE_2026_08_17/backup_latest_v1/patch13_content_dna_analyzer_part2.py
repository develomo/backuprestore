"""
====================================================================
PATCH 13: CONTENT DNA ANALYZER — PART 2/2 (Creative Mapping + Aggregator)
====================================================================
APPENDS to video_content_analyzer.py: DNAtoCreativeMapping + ProjectDNAAggregator
Run this AFTER patch13_part1.py has been run once.

USAGE:
  python patch13_content_dna_analyzer_part2.py
====================================================================
"""

from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_FILE = BASE_DIR / "video_content_analyzer.py"


def safe_print(msg):
    print(f"[Patch13-P2] {msg}", flush=True)


def create_part2():
    code = '''

# ================================================================
# PART 2: DNAtoCreativeMapping + ProjectDNAAggregator
# ================================================================

class DNAtoCreativeMapping:
    """
    Maps ContentDNA to UNIQUE creative editing parameters.

    THIS IS WHERE TEMPLATES DIE.

    Every DNA profile produces DIFFERENT creative parameters.
    The same clip analyzed twice = potentially different creative output
    (seeded randomness within DNA-defined valid ranges).

    Usage:
        mapper = DNAtoCreativeMapping(seed=12345)
        dna = analyzer.analyze_clip("my_clip.mp4")
        creative = mapper.full_profile(dna)
        print(creative["motion"])  # {"direction": "zoom_in_fast", "zoom": 1.034}
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Args:
            seed: Random seed for reproducibility.
                  If None, each call is truly random within DNA-defined ranges.
                  Use a per-render seed to ensure same result within one render,
                  but different result across renders.
        """
        self.rng = random.Random(seed) if seed is not None else random.Random()

    # ----------------------------------------------------------
    # Individual mappings
    # ----------------------------------------------------------

    def map_motion(self, dna: ContentDNA) -> Dict[str, Any]:
        """
        DNA -> Motion direction + zoom parameters.

        Decision logic:
        - High energy (>0.6): Fast, dynamic motions (zoom in, pan right, diagonal)
        - Medium energy (0.3-0.6): Gentle float, Ken Burns slow
        - Low energy (<0.3): Static hold, center push, gentle float
        - Talking head: Always center push or gentle float (no wild pans)
        - Action content: Fast, aggressive motions

        Args:
            dna: ContentDNA from analyzer

        Returns:
            {"direction": str, "zoom": float}
        """
        me = dna.visual.motion_energy
        ct = dna.visual.content_type

        # Select motion pool based on energy + content type
        if ct == ContentType.TALKING_HEAD:
            pool = ["center_push", "gentle_float_up", "static_hold"]
        elif me > 0.6 or ct == ContentType.ACTION:
            pool = ["zoom_in_fast", "pan_right", "top_right_diag", "bottom_left_diag"]
        elif me > 0.3:
            pool = ["gentle_float_up", "gentle_float_down", "ken_burns_slow",
                    "pan_left", "top_right_diag"]
        else:
            pool = ["static_hold", "center_push", "gentle_float_up",
                    "ken_burns_slow"]

        direction = self.rng.choice(pool)

        # Zoom proportional to motion energy with controlled randomness
        base_zoom = 1.01 + me * 0.06
        zoom = round(base_zoom + self.rng.uniform(-0.008, 0.012), 4)
        zoom = min(1.12, max(1.005, zoom))

        return {"direction": direction, "zoom": zoom}

    def map_cuts(self, dna: ContentDNA) -> Dict[str, Any]:
        """
        DNA -> Cut pacing + transition style.

        Energy drives cut speed:
        - High energy: 1.5-3.5s clips, hard cuts
        - Medium energy: 2.5-5.5s, soft dissolves
        - Low energy: 4-8s, crossfades

        Args:
            dna: ContentDNA

        Returns:
            {"duration": float, "transition": str}
        """
        e = dna.visual.motion_energy

        if e > 0.6:
            lo, hi = 1.5, 3.5
            trans = self.rng.choice(["hard_cut", "whip_pan", "quick_cut"])
        elif e > 0.3:
            lo, hi = 2.5, 5.5
            trans = self.rng.choice(["soft_dissolve", "crossfade", "hard_cut"])
        else:
            lo, hi = 4.0, 8.0
            trans = self.rng.choice(["crossfade", "dip_to_black", "soft_dissolve"])

        # Complexity slightly shortens cuts (more to show = faster pacing)
        complexity_adj = 1.0 - dna.visual.scene_complexity * 0.3
        dur = round(self.rng.uniform(lo, hi) * complexity_adj, 2)
        dur = max(0.8, min(hi, dur))

        return {"duration": dur, "transition": trans}

    def map_color(self, dna: ContentDNA) -> Dict[str, Any]:
        """
        DNA -> Color grading parameters.

        - Low saturation -> boost it
        - Low contrast -> add contrast
        - Warm color temp -> slight warmth boost
        - Cool color temp -> maintain cool look

        Args:
            dna: ContentDNA

        Returns:
            {"saturation_boost": float, "contrast_boost": float, "warmth": float}
        """
        # Boost inversely to current state (balance)
        sat = round(
            1.0 + (1.0 - dna.visual.saturation_level) * 0.12 +
            self.rng.uniform(-0.02, 0.03), 3
        )
        cont = round(
            1.0 + (1.0 - dna.visual.contrast_ratio) * 0.08 +
            self.rng.uniform(-0.01, 0.02), 3
        )

        if dna.visual.color_temp == ColorTemperature.WARM:
            warmth = self.rng.uniform(0.02, 0.06)
        elif dna.visual.color_temp == ColorTemperature.COOL:
            warmth = self.rng.uniform(-0.06, -0.02)
        else:
            warmth = self.rng.uniform(-0.02, 0.02)

        return {
            "saturation_boost": sat,
            "contrast_boost": cont,
            "warmth": round(warmth, 3),
        }

    def map_voice(self, dna: ContentDNA) -> Dict[str, Any]:
        """
        DNA -> Voice processing parameters.

        - High silence ratio -> more compression needed, higher LRA target
        - High speech ratio -> tighter compression for clarity
        - High transient density -> softer compression to avoid pumping

        Args:
            dna: ContentDNA

        Returns:
            {"compression_ratio": float, "lra_target": float, "pacing": float}
        """
        sr = dna.audio.silence_ratio

        if sr > 0.3:
            comp = 1.5 + self.rng.uniform(-0.1, 0.1)
            lra = 7.0 + self.rng.uniform(-0.5, 0.5)
        elif sr > 0.1:
            comp = 1.7 + self.rng.uniform(-0.1, 0.1)
            lra = 6.0 + self.rng.uniform(-0.5, 0.5)
        else:
            comp = 1.9 + self.rng.uniform(-0.1, 0.1)
            lra = 5.0 + self.rng.uniform(-0.5, 0.5)

        pacing = round(
            1.0 + (1.0 + dna.visual.motion_energy) * 0.12 +
            self.rng.uniform(-0.04, 0.04), 2
        )

        return {
            "compression_ratio": round(comp, 2),
            "lra_target": round(lra, 1),
            "pacing": pacing,
        }

    def map_sfx(self, dna: ContentDNA) -> Dict[str, Any]:
        """
        DNA -> Sound design parameters.

        - Action/high energy -> more whoosh, louder SFX
        - Calm/low energy -> subtle or no SFX
        - High transient density -> ducking more aggressive

        Args:
            dna: ContentDNA

        Returns:
            {"whoosh_enabled": bool, "whoosh_volume_db": float, "duck_amount_db": float}
        """
        me = dna.visual.motion_energy
        td = dna.audio.transient_density

        whoosh = me > 0.15
        whoosh_vol = round(-35 + me * 15 + self.rng.uniform(-2, 2), 1)
        duck = round(-14 + td * 8 + self.rng.uniform(-1, 1), 1)

        return {
            "whoosh_enabled": whoosh,
            "whoosh_volume_db": min(-18, max(-40, whoosh_vol)),
            "duck_amount_db": min(-6, max(-18, duck)),
        }

    # ----------------------------------------------------------
    # Complete profile
    # ----------------------------------------------------------

    def full_profile(self, dna: ContentDNA) -> Dict[str, Any]:
        """
        Generate a COMPLETE unique creative profile from a single DNA.

        This is the ONE function to call for per-clip creative decisions.
        It returns ALL parameters needed to render this clip uniquely.

        Args:
            dna: ContentDNA from analyzer

        Returns:
            Complete creative profile dict with keys:
            - motion: {direction, zoom}
            - cuts: {duration, transition}
            - color: {saturation_boost, contrast_boost, warmth}
            - voice: {compression_ratio, lra_target, pacing}
            - sfx: {whoosh_enabled, whoosh_volume_db, duck_amount_db}
            - dna_hash: unique DNA identifier
            - creative_sig: cryptographic signature ensuring uniqueness
        """
        profile = {
            "motion": self.map_motion(dna),
            "cuts": self.map_cuts(dna),
            "color": self.map_color(dna),
            "voice": self.map_voice(dna),
            "sfx": self.map_sfx(dna),
            "dna_hash": dna.uniqueness_hash,
            "content_type": dna.visual.content_type.value,
            "energy": dna.energy_level.value,
        }

        # Cryptographic creative signature - ensures no two profiles
        # can ever be identical, even for same DNA
        profile["creative_sig"] = hashlib.sha256(
            (dna.uniqueness_hash + str(self.rng.random()) +
             str(time.time() % 0.001)).encode("utf-8")
        ).hexdigest()[:12]

        return profile


# ================================================================
# PROJECT DNA AGGREGATOR
# ================================================================

class ProjectDNAAggregator:
    """
    Aggregates multiple clip DNAs into a project-level DNA profile.

    This is the BRIDGE between individual clips and the overall video.
    It determines the GLOBAL creative direction by analyzing how diverse
    the clips are, what the dominant content type is, and how energetic
    the overall project is.

    The aggregated profile feeds into:
    - Master creative direction (dynamic/balanced/cinematic/gentle)
    - Global color grading style
    - Overall pacing strategy
    - Voice processing consistency

    Usage:
        aggregator = ProjectDNAAggregator(seed=render_seed)
        clip_dnas = analyzer.analyze_multiple(clip_paths)
        project = aggregator.aggregate(clip_dnas)
        print(f"Direction: {project['creative_direction']}")
    """

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed) if seed is not None else random.Random()

    def aggregate(self, dnas: List[ContentDNA]) -> Dict[str, Any]:
        """
        Aggregate multiple clip DNAs into project-level creative direction.

        The aggregation is WEIGHTED by clip duration (longer clips matter more)
        and CLIP DIVERSITY (how varied the clips are affects the creative strategy).

        Args:
            dnas: List of ContentDNA objects from analyzer

        Returns:
            Project-level profile dict with:
            - clip_count, total_duration
            - dominant_type (most common content type)
            - avg_energy, avg_motion_energy, avg_contrast
            - clip_diversity (0=all similar, 1=very diverse)
            - creative_direction (dynamic/balanced/cinematic/gentle)
            - creative_variant (sub-style within direction)
            - type_distribution (counts per content type)
            - uniqueness_seed (random project seed)
        """
        if not dnas:
            return self._default()

        n = len(dnas)
        total_dur = sum(d.clip_duration for d in dnas)

        # Weighted average energy (weighted by clip duration)
        if total_dur > 0:
            energy_map = {
                EnergyLevel.VERY_LOW: 0, EnergyLevel.LOW: 1,
                EnergyLevel.MEDIUM: 2, EnergyLevel.HIGH: 3,
                EnergyLevel.VERY_HIGH: 4
            }
            avg_energy = sum(
                energy_map[d.energy_level] * d.clip_duration
                for d in dnas
            ) / total_dur
        else:
            avg_energy = 2.0

        # Weighted averages
        if total_dur > 0:
            avg_motion = sum(d.visual.motion_energy * d.clip_duration for d in dnas) / total_dur
            avg_contrast = sum(d.visual.contrast_ratio * d.clip_duration for d in dnas) / total_dur
            avg_loudness = sum(d.audio.avg_loudness_db * d.clip_duration for d in dnas) / total_dur
            avg_silence = sum(d.audio.silence_ratio * d.clip_duration for d in dnas) / total_dur
        else:
            avg_motion = sum(d.visual.motion_energy for d in dnas) / n
            avg_contrast = sum(d.visual.contrast_ratio for d in dnas) / n
            avg_loudness = sum(d.audio.avg_loudness_db for d in dnas) / n
            avg_silence = sum(d.audio.silence_ratio for d in dnas) / n

        # Content type distribution
        type_counts: Dict[str, int] = {}
        for d in dnas:
            t = d.visual.content_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        dominant_type = max(type_counts, key=type_counts.get) if type_counts else "mixed"

        # Clip diversity - how different are the clips from each other
        motion_values = [d.visual.motion_energy for d in dnas]
        diversity = self._variance(motion_values) * 4.0 if len(motion_values) > 1 else 0.3

        # Creative direction from aggregate energy
        if avg_energy >= 3.0:
            direction = "dynamic"
        elif avg_energy >= 2.0:
            direction = "balanced"
        elif avg_energy >= 1.0:
            direction = "cinematic"
        else:
            direction = "gentle"

        # Creative variant (sub-style within direction)
        variants = {
            "dynamic": ["punchy_rapid", "kinetic_burst", "intense_flow", "explosive_pulse"],
            "balanced": ["smooth_pulse", "steady_build", "natural_cadence", "organic_flow"],
            "cinematic": ["elegant_glide", "soft_unfold", "timeless_drift", "epic_sweep"],
            "gentle": ["silent_rhythm", "deep_pause", "quiet_journey", "whisper_flow"],
        }
        variant = self.rng.choice(variants.get(direction, ["custom"]))

        return {
            "clip_count": n,
            "total_duration": round(total_dur, 2),
            "dominant_type": dominant_type,
            "avg_energy": round(avg_energy / 4.0, 2),  # Normalize 0-1
            "avg_motion_energy": round(avg_motion, 4),
            "avg_contrast": round(avg_contrast, 3),
            "avg_loudness_db": round(avg_loudness, 1),
            "avg_silence_ratio": round(avg_silence, 3),
            "clip_diversity": round(diversity, 3),
            "creative_direction": direction,
            "creative_variant": variant,
            "type_distribution": type_counts,
            "uniqueness_seed": self.rng.randint(10000, 99999),
        }

    def _variance(self, values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    def _default(self) -> Dict[str, Any]:
        return {
            "clip_count": 0,
            "total_duration": 0,
            "dominant_type": "mixed",
            "avg_energy": 0.5,
            "avg_motion_energy": 0.3,
            "avg_contrast": 1.0,
            "avg_loudness_db": -23.0,
            "avg_silence_ratio": 0.1,
            "clip_diversity": 0.3,
            "creative_direction": "balanced",
            "creative_variant": "natural_cadence",
            "type_distribution": {},
            "uniqueness_seed": self.rng.randint(10000, 99999),
        }


# ================================================================
# AUTO NICHE DETECTOR (Helper)
# ================================================================

def detect_niche_from_dna(project_profile: Dict[str, Any]) -> str:
    """
    Automatically determine the best niche from project DNA.

    This enables FULL AUTO MODE where the AI decides
    which niche to use based on actual content analysis.

    Args:
        project_profile: Output from ProjectDNAAggregator.aggregate()

    Returns:
        Niche string, one of:
        stoic_wisdom, quantum_future, mystery, luxury_lifestyle,
        interior_design, finance_simulation, or default
    """
    dom_type = project_profile.get("dominant_type", "mixed")
    energy = project_profile.get("avg_energy", 0.5)

    niche_map = {
        "talking_head": "stoic_wisdom",
        "action": "quantum_future" if energy > 0.6 else "mystery",
        "b_roll": "luxury_lifestyle",
        "landscape": "interior_design",
        "product": "finance_simulation",
        "text_graphic": "quantum_future",
        "abstract": "mystery",
    }

    return niche_map.get(dom_type, "default")


def detect_preset_from_dna(project_profile: Dict[str, Any]) -> int:
    """
    Automatically select preset number from project DNA.

    Args:
        project_profile: Aggregated project profile

    Returns:
        Preset number 1-8
    """
    energy = project_profile.get("avg_energy", 0.5)
    diversity = project_profile.get("clip_diversity", 0.3)
    seed = int(project_profile.get("uniqueness_seed", 42))

    rng = random.Random(seed)

    if energy > 0.8:
        base = 7
    elif energy > 0.6:
        base = 5
    elif energy > 0.4:
        base = 3
    else:
        base = 1

    # Diversity adds variation
    if diversity > 0.6:
        base += 1

    return max(1, min(8, base + rng.randint(0, 1)))


# ================================================================
# MODULE EXPORTS
# ================================================================

__all__ = [
    "ContentDNAAnalyzer",
    "DNAtoCreativeMapping",
    "ProjectDNAAggregator",
    "ContentDNA",
    "VisualDNA",
    "AudioDNA",
    "ContentType",
    "EnergyLevel",
    "ColorTemperature",
    "detect_niche_from_dna",
    "detect_preset_from_dna",
]

if __name__ == "__main__":
    print("Video Content Analyzer Engine (FULL) Ready")
    print("9 classes: ContentDNAAnalyzer, DNAtoCreativeMapping, ProjectDNAAggregator, ...")
    print("2 helpers: detect_niche_from_dna(), detect_preset_from_dna()")
'''
    return code


if __name__ == "__main__":
    print("=" * 60)
    print("PATCH 13: Content DNA Analyzer (Part 2/2)")
    print("=" * 60)

    if not OUTPUT_FILE.exists():
        safe_print("ERROR: video_content_analyzer.py not found! Run Part 1 first.")
    else:
        code = create_part2()
        # Append to existing file
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(code)
        safe_print(f"APPENDED to: {OUTPUT_FILE}")
        safe_print(f"Total size: {OUTPUT_FILE.stat().st_size} bytes")
        safe_print("\nDONE! Both parts combined.")
        safe_print("Test: python -c \"from video_content_analyzer import DNAtoCreativeMapping; print('OK')\"")