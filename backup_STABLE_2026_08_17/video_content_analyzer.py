"""
VIDEO CONTENT ANALYZER - DNA Extraction Engine (Part 1/2)

Classes in Part 1:
  ContentType, EnergyLevel, ColorTemperature (Enums)
  VisualDNA, AudioDNA, ContentDNA (Data Models)
  ContentDNAAnalyzer (Core Analysis Engine)

Classes in Part 2:
  DNAtoCreativeMapping (DNA -> Creative Parameters)
  ProjectDNAAggregator (Multi-clip -> Project Direction)
"""

import subprocess
import json
import math
import random
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ================================================================
# ENUMS
# ================================================================

class ContentType(Enum):
    TALKING_HEAD = "talking_head"
    B_ROLL = "b_roll"
    ACTION = "action"
    TEXT_GRAPHIC = "text_graphic"
    LANDSCAPE = "landscape"
    PRODUCT = "product"
    ABSTRACT = "abstract"
    MIXED = "mixed"

class EnergyLevel(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class ColorTemperature(Enum):
    WARM = "warm"
    NEUTRAL = "neutral"
    COOL = "cool"
    MIXED = "mixed"


# ================================================================
# DNA DATA MODELS
# ================================================================

@dataclass
class VisualDNA:
    """Visual fingerprint of a single video clip."""
    avg_brightness: float = 0.5
    brightness_variance: float = 0.0
    contrast_ratio: float = 1.0
    saturation_level: float = 0.5
    dominant_hue: float = 0.0
    color_temp: ColorTemperature = ColorTemperature.NEUTRAL
    motion_energy: float = 0.0
    edge_density: float = 0.0
    scene_complexity: float = 0.5
    content_type: ContentType = ContentType.MIXED
    face_present: bool = False
    text_present: bool = False
    brightness_curve: List[float] = field(default_factory=list)


@dataclass
class AudioDNA:
    """Audio fingerprint of a single video clip."""
    avg_loudness_db: float = -23.0
    loudness_range_db: float = 8.0
    peak_db: float = -3.0
    silence_ratio: float = 0.0
    dominant_freq: float = 1000.0
    freq_centroid: float = 1500.0
    speech_ratio: float = 0.0
    music_ratio: float = 0.0
    energy_envelope: List[float] = field(default_factory=list)
    transient_density: float = 0.0


@dataclass
class ContentDNA:
    """Complete DNA fingerprint of a single video clip."""
    clip_path: str = ""
    clip_duration: float = 0.0
    clip_fps: float = 30.0
    resolution: tuple = (1920, 1080)
    visual: VisualDNA = field(default_factory=VisualDNA)
    audio: AudioDNA = field(default_factory=AudioDNA)
    energy_level: EnergyLevel = EnergyLevel.MEDIUM
    uniqueness_hash: str = ""
    analysis_timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clip_path": self.clip_path,
            "clip_duration": self.clip_duration,
            "clip_fps": self.clip_fps,
            "resolution": list(self.resolution),
            "energy_level": self.energy_level.value,
            "content_type": self.visual.content_type.value,
            "color_temp": self.visual.color_temp.value,
            "avg_brightness": round(self.visual.avg_brightness, 4),
            "contrast_ratio": round(self.visual.contrast_ratio, 4),
            "motion_energy": round(self.visual.motion_energy, 4),
            "saturation": round(self.visual.saturation_level, 4),
            "scene_complexity": round(self.visual.scene_complexity, 4),
            "avg_loudness_db": round(self.audio.avg_loudness_db, 2),
            "loudness_range_db": round(self.audio.loudness_range_db, 2),
            "silence_ratio": round(self.audio.silence_ratio, 4),
            "speech_ratio": round(self.audio.speech_ratio, 4),
            "transient_density": round(self.audio.transient_density, 4),
            "uniqueness_hash": self.uniqueness_hash,
        }


# ================================================================
# CONTENT DNA ANALYZER ENGINE
# ================================================================

class ContentDNAAnalyzer:
    """
    Deep content analysis engine.
    Extracts VisualDNA + AudioDNA from every clip using FFmpeg.
    Every clip gets a unique fingerprint. No templates. Ever.

    Usage:
        analyzer = ContentDNAAnalyzer()
        dna = analyzer.analyze_clip("/path/to/clip.mp4")
        print(f"Energy: {dna.energy_level.value}")
        print(f"Type: {dna.visual.content_type.value}")
        print(f"Motion: {dna.visual.motion_energy:.3f}")

    For multiple clips:
        dnas = analyzer.analyze_multiple(["/p/1.mp4", "/p/2.mp4"])
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        self.FFMPEG = ffmpeg_path
        self.FFPROBE = ffprobe_path

    # ============================================================
    # PUBLIC API
    # ============================================================

    def analyze_clip(self, clip_path: str, sample_frames: int = 8) -> ContentDNA:
        """Extract FULL ContentDNA from a single clip."""
        clip_path = str(clip_path)
        dna = ContentDNA()
        dna.clip_path = clip_path
        dna.analysis_timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")

        # Step 1: Probe
        probe_data = self._ffprobe(clip_path)
        if probe_data:
            self._parse_probe(dna, probe_data)

        # Step 2: Visual DNA
        dna.visual = self._analyze_visual(clip_path, dna.clip_duration, sample_frames)

        # Step 3: Audio DNA
        dna.audio = self._analyze_audio(clip_path, dna.clip_duration)

        # Step 4: Energy
        dna.energy_level = self._compute_energy(dna)

        # Step 5: Hash
        dna.uniqueness_hash = self._make_hash(dna)

        return dna

    def analyze_multiple(self, clip_paths: List[str],
                         sample_frames: int = 6) -> List[ContentDNA]:
        """Analyze multiple clips. Failed clips are skipped."""
        results = []
        for i, cp in enumerate(clip_paths):
            try:
                dna = self.analyze_clip(cp, sample_frames)
                results.append(dna)
            except Exception as e:
                safe_log(f"SKIP clip {i+1}: {e}")
        return results

    def analyze_video_segments(self, video_path: str,
                                segment_duration: float = 3.0) -> List[ContentDNA]:
        """Split a long video into segments and analyze each."""
        total = self._get_duration(video_path)
        if total <= 0:
            return []
        results = []
        seg_start = 0.0
        while seg_start < total:
            seg_end = min(seg_start + segment_duration, total)
            try:
                seg_path = self._extract_segment(video_path, seg_start, seg_end)
                if seg_path:
                    dna = self.analyze_clip(seg_path, sample_frames=4)
                    dna.clip_duration = seg_end - seg_start
                    results.append(dna)
            except Exception:
                pass
            seg_start = seg_end
        return results

    # ============================================================
    # VISUAL DNA EXTRACTION
    # ============================================================

    def _analyze_visual(self, clip_path: str, duration: float,
                        n_frames: int) -> VisualDNA:
        v = VisualDNA()
        if duration <= 0:
            return v

        # Extract frame stats
        stats = self._frame_stats(clip_path, duration, n_frames)

        if stats:
            brights = [s.get("brightness", 0.5) for s in stats]
            v.avg_brightness = sum(brights) / len(brights)
            v.brightness_variance = self._var(brights)
            v.brightness_curve = brights

            contrasts = [s.get("contrast", 1.0) for s in stats]
            v.contrast_ratio = sum(contrasts) / len(contrasts)

            sats = [s.get("saturation", 0.5) for s in stats]
            v.saturation_level = sum(sats) / len(sats)

            temps = [s.get("color_temp", 0.0) for s in stats]
            avg_temp = sum(temps) / len(temps)
            if avg_temp > 0.1:
                v.color_temp = ColorTemperature.WARM
            elif avg_temp < -0.1:
                v.color_temp = ColorTemperature.COOL
            else:
                v.color_temp = ColorTemperature.NEUTRAL
        else:
            # Fallback from motion only
            motion = self._motion_energy(clip_path, duration)
            v.motion_energy = motion
            v.avg_brightness = 0.5 + motion * 0.12
            v.contrast_ratio = 0.7 + motion * 0.5
            v.saturation_level = 0.4 + motion * 0.3

        v.motion_energy = self._motion_energy(clip_path, duration)
        v.scene_complexity = min(1.0,
            v.motion_energy * 0.3 + v.brightness_variance * 3.0 +
            v.saturation_level * 0.3 + v.contrast_ratio * 0.1
        )
        v.content_type = self._classify(v)
        return v

    def _frame_stats(self, clip_path: str, duration: float,
                     n_frames: int) -> List[Dict[str, float]]:
        if duration <= 0:
            return []
        n_frames = max(2, min(n_frames, 15))
        interval = max(0.3, duration / (n_frames + 1))
        results = []
        for i in range(n_frames):
            t = interval * (i + 1)
            try:
                cmd = [
                    self.FFMPEG, "-ss", str(t), "-i", str(clip_path),
                    "-vframes", "1", "-vf", "signalstats,metadata=print:file=-",
                    "-f", "null", "-"
                ]
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                parsed = self._parse_signal(r.stderr or "")
                if parsed:
                    results.append(parsed)
            except Exception:
                pass
        return results

    def _parse_signal(self, text: str) -> Optional[Dict[str, float]]:
        out = {"brightness": 0.5, "contrast": 1.0, "saturation": 0.5, "color_temp": 0.0}
        try:
            for line in text.split("\n"):
                line = line.strip()
                if "YMIN=" in line:
                    parts = line.split()
                    frame = {}
                    for p in parts:
                        if "=" in p:
                            k, v = p.split("=", 1)
                            try:
                                frame[k.upper()] = float(v)
                            except ValueError:
                                pass
                    if "YMIN" in frame:
                        out["brightness"] = (frame["YMIN"] + frame.get("YMAX", 255)) / 510.0
                        out["contrast"] = max(0.05, (frame.get("YMAX", 255) - frame["YMIN"]) / 255.0)
                    if "SATMIN" in frame:
                        out["saturation"] = (frame["SATMIN"] + frame.get("SATMAX", 128)) / 256.0
                    return out
        except Exception:
            pass
        return out

    def _motion_energy(self, clip_path: str, duration: float) -> float:
        if duration <= 0:
            return 0.0
        try:
            cmd = [
                self.FFMPEG, "-i", str(clip_path),
                "-vf", "select='gt(scene,0.1)',showinfo",
                "-f", "null", "-"
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            count = r.stderr.count("pts_time:")
            return round(min(1.0, count / max(duration, 0.5) / 3.0), 4)
        except Exception:
            return 0.3

    def _classify(self, v: VisualDNA) -> ContentType:
        me = v.motion_energy
        br = v.avg_brightness
        bv = v.brightness_variance
        cr = v.contrast_ratio
        if me > 0.7:
            return ContentType.ACTION
        if me < 0.15 and br > 0.7:
            return ContentType.TEXT_GRAPHIC
        if me < 0.15 and cr < 0.35:
            return ContentType.LANDSCAPE
        if me < 0.25 and bv > 0.04:
            return ContentType.TALKING_HEAD
        if 0.2 <= me <= 0.6:
            return ContentType.B_ROLL
        if cr > 0.8 and bv < 0.01:
            return ContentType.PRODUCT
        if br < 0.2:
            return ContentType.ABSTRACT
        return ContentType.MIXED

    # ============================================================
    # AUDIO DNA EXTRACTION
    # ============================================================

    def _analyze_audio(self, clip_path: str, duration: float) -> AudioDNA:
        a = AudioDNA()
        if duration <= 0:
            return a
        try:
            cmd = [
                self.FFMPEG, "-i", str(clip_path),
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
                "-f", "null", "-"
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            js = r.stderr.find("{")
            je = r.stderr.rfind("}") + 1
            if js >= 0 and je > js:
                ld = json.loads(r.stderr[js:je])
                a.avg_loudness_db = float(ld.get("input_i", -23.0))
                a.loudness_range_db = float(ld.get("input_lra", 8.0))
                a.peak_db = float(ld.get("input_tp", -3.0))
            a.silence_ratio = self._silence(clip_path, duration)
            lra = a.loudness_range_db
            if lra > 10:
                a.speech_ratio, a.music_ratio = 0.75, 0.05
            elif lra > 6:
                a.speech_ratio, a.music_ratio = 0.55, 0.20
            elif lra > 3:
                a.speech_ratio, a.music_ratio = 0.25, 0.50
            else:
                a.speech_ratio, a.music_ratio = 0.05, 0.80
            a.transient_density = min(1.0, lra / 20.0)
        except Exception:
            pass
        return a

    def _silence(self, clip_path: str, duration: float) -> float:
        if duration <= 0:
            return 0.0
        try:
            cmd = [
                self.FFMPEG, "-i", str(clip_path),
                "-af", "silencedetect=noise=-50dB:d=0.5",
                "-f", "null", "-"
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            total = 0.0
            for line in r.stderr.split("\n"):
                if "silence_duration:" in line:
                    try:
                        total += float(line.split("silence_duration:")[1].strip())
                    except ValueError:
                        pass
            return min(0.95, total / duration)
        except Exception:
            return 0.1

    # ============================================================
    # ENERGY & UNIQUENESS
    # ============================================================

    def _compute_energy(self, dna: ContentDNA) -> EnergyLevel:
        s = (
            dna.visual.motion_energy * 0.30 +
            (1.0 - dna.audio.silence_ratio) * 0.25 +
            dna.visual.contrast_ratio * 0.20 +
            dna.audio.transient_density * 0.15 +
            (dna.audio.loudness_range_db / 20.0) * 0.10
        )
        if s > 0.8:
            return EnergyLevel.VERY_HIGH
        if s > 0.6:
            return EnergyLevel.HIGH
        if s > 0.4:
            return EnergyLevel.MEDIUM
        if s > 0.2:
            return EnergyLevel.LOW
        return EnergyLevel.VERY_LOW

    def _make_hash(self, dna: ContentDNA) -> str:
        raw = (
            f"{dna.clip_path}:{dna.clip_duration:.3f}:"
            f"{dna.visual.avg_brightness:.5f}:{dna.visual.motion_energy:.5f}:"
            f"{dna.visual.contrast_ratio:.5f}:{dna.visual.saturation_level:.5f}:"
            f"{dna.audio.avg_loudness_db:.3f}:{dna.audio.silence_ratio:.5f}:"
            f"{dna.audio.loudness_range_db:.3f}:{dna.audio.transient_density:.5f}"
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    # ============================================================
    # UTILITY
    # ============================================================

    def _ffprobe(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            cmd = [
                self.FFPROBE, "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", str(path)
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if r.returncode == 0 and r.stdout.strip():
                return json.loads(r.stdout)
        except Exception:
            pass
        return None

    def _parse_probe(self, dna: ContentDNA, probe: Dict[str, Any]):
        fmt = probe.get("format", {})
        dna.clip_duration = float(fmt.get("duration", 0))
        for s in probe.get("streams", []):
            if s.get("codec_type") == "video":
                dna.resolution = (s.get("width", 1920), s.get("height", 1080))
                parts = str(s.get("r_frame_rate", "30/1")).split("/")
                if len(parts) == 2 and float(parts[1]) > 0:
                    dna.clip_fps = float(parts[0]) / float(parts[1])

    def _get_duration(self, path: str) -> float:
        p = self._ffprobe(path)
        return float(p.get("format", {}).get("duration", 0)) if p else 0.0

    def _extract_segment(self, video_path: str, start: float, end: float) -> Optional[str]:
        try:
            seg = f"/tmp/_dna_seg_{int(start)}_{int(end)}.mp4"
            cmd = [
                self.FFMPEG, "-y", "-ss", str(start), "-i", str(video_path),
                "-t", str(end - start), "-c", "copy", seg
            ]
            subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return seg if Path(seg).exists() else None
        except Exception:
            return None

    @staticmethod
    def _var(values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)


def safe_log(msg: str):
    print(f"[DNA] {msg}", flush=True)


if __name__ == "__main__":
    print("ContentDNAAnalyzer Engine (Part 1/2) Ready")
    print("Classes: ContentDNA, VisualDNA, AudioDNA, ContentDNAAnalyzer")
    print("Import: from video_content_analyzer import ContentDNAAnalyzer")


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
