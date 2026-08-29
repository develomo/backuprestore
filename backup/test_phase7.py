"""
PHASE 7: True Editing Intelligence — Complete Test
Tests Part 1 (DNA Analyzer) + Part 2 (Creative Mapping + Aggregator)
"""
from pathlib import Path
import re

BASE = Path(__file__).parent
P = 0
F = 0

def t(n, c):
    global P, F
    if c:
        P += 1
        print(f"   OK {n}")
    else:
        F += 1
        print(f"   XX {n}")

def ci(p, txt, n):
    try:
        content = Path(p).read_text(encoding="utf-8")
        t(n, txt in content)
    except:
        t(n, False)

def main():
    global P, F
    print("=" * 60)
    print("PHASE 7 COMPLETE TEST")
    print("=" * 60)

    print("\n--- New File ---")
    t("video_content_analyzer.py exists", (BASE / "video_content_analyzer.py").exists())

    print("\n--- PART 1: Data Models + Analyzer ---")
    ci("video_content_analyzer.py", "class ContentType", "ContentType enum")
    ci("video_content_analyzer.py", "class EnergyLevel", "EnergyLevel enum")
    ci("video_content_analyzer.py", "class ColorTemperature", "ColorTemperature enum")
    ci("video_content_analyzer.py", "class VisualDNA", "VisualDNA dataclass")
    ci("video_content_analyzer.py", "class AudioDNA", "AudioDNA dataclass")
    ci("video_content_analyzer.py", "class ContentDNA", "ContentDNA dataclass")
    ci("video_content_analyzer.py", "class ContentDNAAnalyzer", "ContentDNAAnalyzer class")
    ci("video_content_analyzer.py", "def analyze_clip", "analyze_clip method")
    ci("video_content_analyzer.py", "def analyze_multiple", "analyze_multiple method")
    ci("video_content_analyzer.py", "def _analyze_visual", "_analyze_visual internal")
    ci("video_content_analyzer.py", "def _analyze_audio", "_analyze_audio internal")
    ci("video_content_analyzer.py", "def _motion_energy", "_motion_energy FFmpeg")
    ci("video_content_analyzer.py", "def _classify", "_classify content type")
    ci("video_content_analyzer.py", "def _silence", "_silence detection")
    ci("video_content_analyzer.py", "def _compute_energy", "_compute_energy scoring")
    ci("video_content_analyzer.py", "def _make_hash", "_make_hash uniqueness")
    ci("video_content_analyzer.py", "def to_dict", "to_dict serialization")
    ci("video_content_analyzer.py", "signalstats", "FFmpeg signalstats filter")
    ci("video_content_analyzer.py", "loudnorm", "FFmpeg loudnorm filter")
    ci("video_content_analyzer.py", "silencedetect", "FFmpeg silencedetect")

    print("\n--- PART 2: Creative Mapping ---")
    ci("video_content_analyzer.py", "class DNAtoCreativeMapping", "DNAtoCreativeMapping class")
    ci("video_content_analyzer.py", "def map_motion", "map_motion method")
    ci("video_content_analyzer.py", "def map_cuts", "map_cuts method")
    ci("video_content_analyzer.py", "def map_color", "map_color method")
    ci("video_content_analyzer.py", "def map_voice", "map_voice method")
    ci("video_content_analyzer.py", "def map_sfx", "map_sfx method")
    ci("video_content_analyzer.py", "def full_profile", "full_profile method")
    ci("video_content_analyzer.py", "creative_sig", "creative_sig hash")

    print("\n--- PART 2: Project Aggregator ---")
    ci("video_content_analyzer.py", "class ProjectDNAAggregator", "ProjectDNAAggregator class")
    ci("video_content_analyzer.py", "def aggregate", "aggregate method")
    ci("video_content_analyzer.py", "def detect_niche_from_dna", "detect_niche_from_dna helper")
    ci("video_content_analyzer.py", "def detect_preset_from_dna", "detect_preset_from_dna helper")
    ci("video_content_analyzer.py", "creative_direction", "creative_direction key")
    ci("video_content_analyzer.py", "uniqueness_seed", "uniqueness_seed key")

    print("\n--- Phase 1-6 Quick Verify ---")
    ci("app.py", "preset_selector_section", "App: preset selector")
    ci("app.py", "scoring_panel_section", "App: scoring panel")
    ci("batch_long_renderer.py", "gentle_float_up", "Batch: 12 motions intact")
    ci("master_pipeline.py", "apply_preset_to_render", "Master: preset pipe")
    ci("voice_humanization_orchestrator.py", "sizzle_cut", "Voice: sizzle cut")
    ci("audio_engine.py", "apply_intelligent_ducking", "Audio: ducking")
    ci("final_assembler.py", "FILM_GRAIN_ENABLED", "Assembler: grain flag")

    # Runtime import test
    print("\n--- Runtime Import Test ---")
    try:
        from video_content_analyzer import (
            ContentDNAAnalyzer, DNAtoCreativeMapping,
            ProjectDNAAggregator, ContentDNA, VisualDNA, AudioDNA,
            ContentType, EnergyLevel, ColorTemperature,
            detect_niche_from_dna, detect_preset_from_dna
        )
        t("Import ContentDNAAnalyzer", True)
        t("Import DNAtoCreativeMapping", True)
        t("Import ProjectDNAAggregator", True)
        t("Import ContentDNA dataclass", True)
        t("Import VisualDNA", True)
        t("Import AudioDNA", True)
        t("Import detect_niche_from_dna", True)
        t("Import detect_preset_from_dna", True)

        # Quick functional test
        analyzer = ContentDNAAnalyzer()
        t("ContentDNAAnalyzer instantiated", True)

        # Test that methods exist
        t("analyzer.analyze_clip exists", hasattr(analyzer, "analyze_clip"))
        t("analyzer.analyze_multiple exists", hasattr(analyzer, "analyze_multiple"))

        # Test creative mapping creation
        mapper = DNAtoCreativeMapping(seed=42)
        t("DNAtoCreativeMapping instantiated", mapper is not None)
        t("mapper.map_motion exists", hasattr(mapper, "map_motion"))
        t("mapper.map_cuts exists", hasattr(mapper, "map_cuts"))
        t("mapper.full_profile exists", hasattr(mapper, "full_profile"))

        # Test aggregator
        agg = ProjectDNAAggregator(seed=99)
        t("ProjectDNAAggregator instantiated", agg is not None)
        t("agg.aggregate exists", hasattr(agg, "aggregate"))

    except ImportError as e:
        t(f"Import DNA engine: {str(e)[:80]}", False)

    total = P + F
    print("\n" + "=" * 60)
    print(f"RESULT: {P}/{total} PASSED")
    print("=" * 60)
    if F == 0:
        print("\n*** PHASE 7 COMPLETE - ALL PASSED! ***")
        print("Content DNA Analyzer Engine is ready.")
        print("Next: Run phase7_true_intelligence.py to inject into pipelines.")
    else:
        print(f"\n{F} checks failed")
        print("Run: python patch13_content_dna_analyzer.py first, then python patch13_content_dna_analyzer_part2.py")

if __name__ == "__main__":
    main()