# ============================================================
# PHASE 3 — FILE 3: content_analyzer.py (PART 2/2)
# ============================================================
# Isse Part 1 ke neeche paste karna hai.

import re
import math
import logging
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter

logger = logging.getLogger("ContentAnalyzerEngine")


# ============================================================
# SECTION 6: MAIN CONTENT ANALYZER ENGINE
# ============================================================

class ContentAnalyzerEngine:
    """
    MAIN CONTENT ANALYZER ENGINE.
    Full pipeline: text → structure, emotion, pacing, keywords, readability.
    
    Usage:
        engine = ContentAnalyzerEngine()
        report = engine.analyze("Your full video script here...")
        print(report.summary())
    """

    def __init__(self):
        self.lang_utils = LanguageUtils()
        self.readability = ReadabilityAnalyzer()
        self.emotion_detector = EmotionDetector()
        self.pacing_detector = PacingDetector()
        self.structure_detector = StructureDetector()
        logger.info("ContentAnalyzerEngine initialized")

    def analyze(self, text: str) -> ContentReport:
        """COMPLETE CONTENT ANALYSIS."""
        if not text or not text.strip():
            return self._empty_report()

        text_clean = text.strip()
        lang = self.lang_utils.detect_language(text_clean)

        raw_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text_clean) if s.strip()]
        if not raw_sentences:
            return self._empty_report()

        total_sentences = len(raw_sentences)
        all_words = re.findall(r'\b\w+\b', text_clean.lower())
        total_words = len(all_words)

        sentences: List[SentenceAnalysis] = []
        keyword_counter: Counter = Counter()
        all_emotions: List[EmotionLabel] = []
        all_emotion_scores: List[float] = []
        energy_curve: List[float] = []
        pacing_map: List[PacingType] = []

        for i, sent_text in enumerate(raw_sentences):
            words_in_sent = re.findall(r'\b\w+\b', sent_text.lower())
            wc = len(words_in_sent)
            cc = len(sent_text)
            duration = self.lang_utils.estimate_speaking_duration(wc, lang)
            emotion, emotion_conf = self.emotion_detector.detect_emotion(sent_text)
            section = self.structure_detector.classify_sentence(sent_text, i, total_sentences, wc)
            is_critical = section in (ScriptSection.HOOK, ScriptSection.CLIMAX, ScriptSection.CTA)
            pacing = self.pacing_detector.determine_pacing(sent_text, emotion, wc, is_critical)

            significant_words = [w for w in words_in_sent
                                 if w not in self.lang_utils.STOPWORDS and len(w) > 2]
            for sw in significant_words:
                keyword_counter[sw] += 1

            emphasis = self.lang_utils.extract_emphasis_words(sent_text)
            ease = self.readability.flesch_reading_ease(sent_text)

            # Energy score
            energy = 0.5
            if emotion in (EmotionLabel.EXCITED, EmotionLabel.URGENT, EmotionLabel.SHOCKING):
                energy = 0.75 + emotion_conf * 0.2
            elif emotion in (EmotionLabel.CALM, EmotionLabel.SAD):
                energy = 0.15 + emotion_conf * 0.2
            elif emotion == EmotionLabel.INSPIRING:
                energy = 0.55 + emotion_conf * 0.2
            else:
                energy = 0.45 + emotion_conf * 0.1
            energy = min(1.0, max(0.0, energy))

            sa = SentenceAnalysis(
                index=i, text=sent_text, word_count=wc, char_count=cc,
                estimated_duration=round(duration, 2), emotion=emotion,
                section=section, pacing=pacing, keywords=significant_words[:10],
                emphasis_words=emphasis, reading_ease=round(ease, 1),
                energy_score=round(energy, 3),
                is_question=self.lang_utils.is_question(sent_text),
                is_exclamation=self.lang_utils.is_exclamation(sent_text),
                has_power_word=self.lang_utils.has_power_word(sent_text),
            )
            sentences.append(sa)
            all_emotions.append(emotion)
            all_emotion_scores.append(emotion_conf)
            energy_curve.append(energy)
            pacing_map.append(pacing)

        # Keywords
        total_sig = sum(keyword_counter.values())
        top_keywords: List[KeywordExtraction] = []
        for word, freq in keyword_counter.most_common(30):
            imp = freq / max(1, total_sig) * (1 + math.log(freq + 1) * 0.3)
            first_pos = next((i for i, sa in enumerate(sentences) if word in sa.text.lower()), 0)
            top_keywords.append(KeywordExtraction(
                word=word, importance=round(min(1.0, imp), 4),
                frequency=freq, is_title_case=word[0].isupper(),
                position_first=first_pos,
            ))

        # Emotion arc
        emotion_counts = Counter(e for e in all_emotions)
        dominant = max(emotion_counts, key=emotion_counts.get) if emotion_counts else EmotionLabel.NEUTRAL
        emotion_variance = len(set(all_emotions)) / max(1, len(all_emotions))
        peak_idx = energy_curve.index(max(energy_curve)) if energy_curve else 0
        valley_idx = energy_curve.index(min(energy_curve)) if energy_curve else 0

        emotion_arc = EmotionArc(
            labels=all_emotions, scores=all_emotion_scores,
            dominant_emotion=dominant,
            emotion_variance=round(emotion_variance, 3),
            peak_sentence_index=peak_idx,
            valley_sentence_index=valley_idx,
        )

        section_map = self.structure_detector.build_section_map(sentences)
        flesch = self.readability.flesch_reading_ease(text_clean)
        grade = self.readability.grade_level(text_clean)
        vocab_div = self.readability.vocabulary_diversity(text_clean)
        total_duration = sum(s.estimated_duration for s in sentences)

        avg_energy = sum(energy_curve) / max(1, len(energy_curve))
        if avg_energy > 0.65: recommended_bpm = 120
        elif avg_energy > 0.45: recommended_bpm = 100
        elif avg_energy > 0.3: recommended_bpm = 85
        else: recommended_bpm = 70

        # Warnings
        warnings: List[str] = []
        if total_words < 30:
            warnings.append("Script is very short (<30 words). May need more content.")
        if total_sentences == 1:
            warnings.append("Only one sentence — script may lack structure.")
        if vocab_div < 0.3 and total_words > 50:
            warnings.append("Low vocabulary diversity. Consider varying word choice.")
        if emotion_variance < 0.2 and total_sentences > 5:
            warnings.append("Low emotion variance — script may feel monotone.")
        if flesch < 30:
            warnings.append(f"Very complex text (Flesch={flesch:.0f}). Simplify for wider audience.")
        if not section_map.get(ScriptSection.HOOK):
            warnings.append("No clear hook detected — first sentence should grab attention.")
        if not section_map.get(ScriptSection.CTA) and total_sentences > 3:
            warnings.append("No call-to-action detected. Consider adding a CTA.")

        # Editing tips
        editing_tips: List[str] = []
        if energy_curve:
            max_s = sentences[peak_idx]
            editing_tips.append(
                f"Catch climax at sentence #{peak_idx+1}: "
                f"'{max_s.text[:60]}...' — use bold transitions here."
            )
        if section_map.get(ScriptSection.HOOK):
            editing_tips.append("Hook detected — fast cut + punchy animation for first 3 seconds.")
        if avg_energy > 0.6:
            editing_tips.append("High energy script — fast pacing & dynamic transitions.")
        if pacing_map:
            slow_count = sum(1 for p in pacing_map if p == PacingType.SLOW)
            if slow_count > len(pacing_map) * 0.3:
                editing_tips.append("Many slow-pacing sentences — use longer clip durations.")
        if vocab_div > 0.7 and total_words > 100:
            editing_tips.append("Rich vocabulary — use sophisticated color grading to match.")

        return ContentReport(
            total_words=total_words, total_sentences=total_sentences,
            total_duration_estimate=round(total_duration, 1),
            avg_words_per_sentence=round(total_words / max(1, total_sentences), 1),
            avg_chars_per_word=round(sum(len(w) for w in all_words) / max(1, total_words), 1),
            sentences=sentences, section_map=section_map,
            top_keywords=top_keywords, niche_signals={},
            emotion_arc=emotion_arc, flesch_reading_ease=round(flesch, 1),
            grade_level=round(grade, 1), vocabulary_diversity=round(vocab_div, 3),
            pacing_map=pacing_map, recommended_bpm=recommended_bpm,
            energy_curve=[round(e, 3) for e in energy_curve],
            warnings=warnings, editing_tips=editing_tips,
        )

    def _empty_report(self) -> ContentReport:
        return ContentReport(
            total_words=0, total_sentences=0, total_duration_estimate=0.0,
            avg_words_per_sentence=0.0, avg_chars_per_word=0.0,
            sentences=[], section_map={}, top_keywords=[], niche_signals={},
            emotion_arc=EmotionArc(
                labels=[], scores=[], dominant_emotion=EmotionLabel.NEUTRAL,
                emotion_variance=0.0, peak_sentence_index=0, valley_sentence_index=0,
            ),
            flesch_reading_ease=50.0, grade_level=6.0,
            vocabulary_diversity=0.0, pacing_map=[],
            recommended_bpm=90, energy_curve=[],
            warnings=["Empty script — no content to analyze."],
        )

    def quick_analyze(self, text: str) -> Dict[str, Any]:
        """Lightweight analysis — returns summary dict only."""
        report = self.analyze(text)
        return report.summary()


# ============================================================
# SECTION 7: EXPORT FUNCTIONS
# ============================================================

def analyze_script(script_text: str) -> Dict[str, Any]:
    """Quick one-liner: analyze script → summary dict."""
    engine = ContentAnalyzerEngine()
    return engine.quick_analyze(script_text)


def analyze_script_deep(script_text: str) -> ContentReport:
    """Full deep analysis → ContentReport object."""
    engine = ContentAnalyzerEngine()
    return engine.analyze(script_text)


def get_sentence_pacing(script_text: str) -> List[Dict[str, Any]]:
    """Get per-sentence pacing recommendations."""
    engine = ContentAnalyzerEngine()
    report = engine.analyze(script_text)
    return [
        {
            "index": s.index, "text": s.text[:80],
            "pacing": s.pacing.value, "emotion": s.emotion.value,
            "energy": s.energy_score, "duration_est": s.estimated_duration,
            "section": s.section.value,
        }
        for s in report.sentences
    ]


def get_emotion_arc(script_text: str) -> List[Dict[str, Any]]:
    """Get emotion arc data for visualization."""
    engine = ContentAnalyzerEngine()
    report = engine.analyze(script_text)
    return [
        {"index": i, "emotion": e.value, "energy": v,
         "dominant_emotion": report.emotion_arc.dominant_emotion.value}
        for i, (e, v) in enumerate(zip(report.emotion_arc.labels, report.energy_curve))
    ]


# ============================================================
# SECTION 8: SELF-TEST
# ============================================================

def run_self_test():
    print("=" * 60)
    print("  CONTENT ANALYZER ENGINE — SELF TEST")
    print("=" * 60)

    engine = ContentAnalyzerEngine()

    test_script = """
    Discover the hidden truth about luxury lifestyles! These millionaire secrets
    will completely change how you think about wealth. Imagine waking up in your
    private villa overlooking the ocean — that's the reality for those who know
    these exclusive strategies.

    But here's the thing — most people don't know about this incredible investment
    opportunity that's been kept secret for decades. The wealthy elite have been
    using this simple method to build massive fortunes.

    Now let's talk about the most powerful mindset shift you need to achieve
    financial freedom. It's not about working harder — it's about working smarter
    with these proven techniques.

    Don't forget to subscribe and hit the bell icon for more life-changing content!
    """

    print("\n📝 Test Script Preview:")
    print(f"   Words: {len(re.findall(r'\\b\\w+\\b', test_script))}")
    print(f"   Sentences: {len([s for s in re.split(r'[.!?]+', test_script) if s.strip()])}")
    print()

    print("🔍 Running full analysis...")
    report = engine.analyze(test_script)

    print(f"\n📊 BASIC STATS:")
    print(f"   Total words:          {report.total_words}")
    print(f"   Total sentences:      {report.total_sentences}")
    print(f"   Est. duration:        {report.total_duration_estimate}s")
    print(f"   Avg words/sentence:   {report.avg_words_per_sentence}")
    print(f"   Avg chars/word:       {report.avg_chars_per_word}")

    print(f"\n📖 READABILITY:")
    print(f"   Flesch Reading Ease:  {report.flesch_reading_ease}/100")
    print(f"   Grade Level:          {report.grade_level}")
    print(f"   Vocabulary Diversity: {report.vocabulary_diversity}")

    print(f"\n🎭 EMOTION ARC:")
    print(f"   Dominant emotion:     {report.emotion_arc.dominant_emotion.value}")
    print(f"   Emotion variance:     {report.emotion_arc.emotion_variance}")
    print(f"   Peak at sentence:     #{report.emotion_arc.peak_sentence_index + 1}")
    print(f"   Valley at sentence:   #{report.emotion_arc.valley_sentence_index + 1}")

    print(f"\n📂 STRUCTURE:")
    for section, indices in sorted(report.section_map.items(), key=lambda x: min(x[1]) if x[1] else 0):
        print(f"   {section.value:<12}: {len(indices)} sentences (indices: {indices})")

    print(f"\n🔑 TOP KEYWORDS:")
    for kw in report.top_keywords[:10]:
        print(f"   {kw.word:<20} freq={kw.frequency:<3} importance={kw.importance:.3f}")

    print(f"\n📈 SENTENCE DETAILS:")
    for s in report.sentences:
        emoji = {"excited":"🔥","curious":"🤔","serious":"⚡","calm":"🌊",
                 "urgent":"🚨","inspiring":"✨","shocking":"💥","neutral":"➖",
                 "sad":"😢","humorous":"😂"}.get(s.emotion.value,"")
        print(f"   #{s.index+1:<2} [{s.section.value:<10}] [{s.pacing.value:<6}] "
              f"[E={s.energy_score:.2f}] {emoji} {s.text[:70]}...")

    print(f"\n⚙️  PACING MAP:")
    pacing_counts = Counter(p.value for p in report.pacing_map)
    for pt, cnt in pacing_counts.most_common():
        bar = "█" * cnt
        print(f"   {pt:<7}: {bar} ({cnt})")

    print(f"\n🎵 Recommended BGM BPM: {report.recommended_bpm}")

    print(f"\n⚠️  WARNINGS:")
    for w in report.warnings:
        print(f"   - {w}")

    print(f"\n💡 EDITING TIPS:")
    for t in report.editing_tips:
        print(f"   - {t}")

    print(f"\n📋 QUICK SUMMARY:")
    for k, v in report.summary().items():
        print(f"   {k}: {v}")

    # Test empty input
    print(f"\n🧪 Empty input test...")
    empty = engine.analyze("")
    assert empty.total_words == 0
    print(f"   ✅ Empty input handled correctly (warnings: {len(empty.warnings)})")

    print(f"\n{'='*60}")
    print("  ✅ ALL TESTS PASSED — Content Analyzer Engine Ready!")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_self_test()