# ============================================================
# PHASE 3 — FILE 3: content_analyzer.py (PART 1/2)
# ============================================================
# Purpose:
#   - Advanced script/NLP content analysis for auto-edit intelligence
#   - Sentence-by-sentence pacing, emotion, and energy mapping
#   - Keyword extraction with weighted importance scoring
#   - Readability & complexity grading (Flesch-Kincaid style)
#   - Content structure detection (hook/body/CTA segmentation)
#   - Emotion arc mapping across the script timeline
#
# Usage:
#   from content_analyzer import ContentAnalyzerEngine
#   engine = ContentAnalyzerEngine()
#   result = engine.analyze("Your full video script here...")
#   print(result.summary())
#
# Dependencies: None (pure Python — no external NLP libs)
# ============================================================

import re
import math
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter, defaultdict

logger = logging.getLogger("ContentAnalyzerEngine")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] [ContentAnalyzer] %(message)s", datefmt="%H:%M:%S"
    ))
    logger.addHandler(h)


# ============================================================
# SECTION 1: DATA STRUCTURES
# ============================================================

class ScriptSection(Enum):
    HOOK = "hook"
    INTRO = "intro"
    BODY = "body"
    TRANSITION = "transition"
    CLIMAX = "climax"
    CTA = "cta"
    OUTRO = "outro"
    UNKNOWN = "unknown"


class EmotionLabel(Enum):
    EXCITED = "excited"
    CURIOUS = "curious"
    SERIOUS = "serious"
    CALM = "calm"
    URGENT = "urgent"
    INSPIRING = "inspiring"
    SHOCKING = "shocking"
    NEUTRAL = "neutral"
    SAD = "sad"
    HUMOROUS = "humorous"


class PacingType(Enum):
    FAST = "fast"
    NORMAL = "normal"
    SLOW = "slow"
    PAUSE = "pause"


@dataclass
class SentenceAnalysis:
    index: int
    text: str
    word_count: int
    char_count: int
    estimated_duration: float
    emotion: EmotionLabel
    section: ScriptSection
    pacing: PacingType
    keywords: List[str] = field(default_factory=list)
    emphasis_words: List[str] = field(default_factory=list)
    reading_ease: float = 0.0
    energy_score: float = 0.5
    is_question: bool = False
    is_exclamation: bool = False
    has_power_word: bool = False


@dataclass
class KeywordExtraction:
    word: str
    importance: float
    frequency: int
    is_title_case: bool = False
    is_niche_signal: bool = False
    position_first: int = 0


@dataclass
class EmotionArc:
    labels: List[EmotionLabel]
    scores: List[float]
    dominant_emotion: EmotionLabel
    emotion_variance: float
    peak_sentence_index: int
    valley_sentence_index: int


@dataclass
class ContentReport:
    total_words: int
    total_sentences: int
    total_duration_estimate: float
    avg_words_per_sentence: float
    avg_chars_per_word: float
    sentences: List[SentenceAnalysis]
    section_map: Dict[ScriptSection, List[int]]
    top_keywords: List[KeywordExtraction]
    niche_signals: Dict[str, float]
    emotion_arc: EmotionArc
    flesch_reading_ease: float
    grade_level: float
    vocabulary_diversity: float
    pacing_map: List[PacingType]
    recommended_bpm: int
    energy_curve: List[float]
    warnings: List[str] = field(default_factory=list)
    editing_tips: List[str] = field(default_factory=list)

    def summary(self) -> Dict[str, Any]:
        return {
            "words": self.total_words,
            "sentences": self.total_sentences,
            "duration_est": round(self.total_duration_estimate, 1),
            "dominant_emotion": self.emotion_arc.dominant_emotion.value,
            "emotion_variance": round(self.emotion_arc.emotion_variance, 2),
            "reading_ease": round(self.flesch_reading_ease, 1),
            "grade_level": round(self.grade_level, 1),
            "vocabulary_diversity": round(self.vocabulary_diversity, 3),
            "recommended_bpm": self.recommended_bpm,
            "sections": {k.value: len(v) for k, v in self.section_map.items()},
            "warnings": self.warnings[:5],
            "tips": self.editing_tips[:5],
        }


# ============================================================
# SECTION 2: LANGUAGE UTILITIES
# ============================================================

class LanguageUtils:
    WPS_BY_LANG = {"en": 2.5, "ur": 2.2, "hi": 2.3, "mixed": 2.4}

    STOPWORDS = {
        "the","a","an","is","are","was","were","be","been",
        "in","on","at","to","for","of","and","or","but",
        "it","this","that","these","those","with","from","by",
        "as","so","if","then","than","also","just","now",
        "very","really","about","into","over","after","before",
        "has","have","had","do","does","did","will","would",
        "can","could","should","may","might","not","no",
        "main","hai","hain","ho","tha","thi","thay",
        "aur","ya","par","mein","se","ko","ka","ki","ke",
        "kya","kyun","kaise","kab","kahan","kon",
        "yeh","woh","hum","tum","aap","mera","tumhara",
    }

    POWER_WORDS = {
        "amazing","incredible","unbelievable","shocking","secret",
        "exclusive","limited","proven","guaranteed","instant",
        "free","new","discover","revealed","hidden","forbidden",
        "dangerous","powerful","ultimate","complete","essential",
        "critical","urgent","warning","breakthrough","revolutionary",
        "mind-blowing","jaw-dropping","life-changing","game-changer",
        "unstoppable","legendary","epic","massive","insane",
        "kamaal","zabardast","shaandaar","behtreen","lajawab",
    }

    QUESTION_STARTERS = {
        "what","why","how","when","where","who","which",
        "can","could","would","should","will","do","does",
        "did","is","are","was","were","have","has","had",
        "kya","kyun","kaise","kab","kahan","kon","kisne",
    }

    CTA_PHRASES = [
        "subscribe","like","share","comment","follow",
        "click","link","description","channel","watch next",
        "don't forget","hit the bell","turn on notifications",
        "check out","sign up","join","download",
    ]

    @classmethod
    def detect_language(cls, text: str) -> str:
        text_lower = text.lower()
        ur_hi_count = en_count = 0
        for word in re.findall(r'\b\w+\b', text_lower):
            if any(m in word for m in ["ain","hay","tha","thi","aur","mein","se","ko","ka","ki","ke","kya","kyun","yeh","woh","tum","aap","hai","hain","ho"]):
                ur_hi_count += 1
            else:
                en_count += 1
        total = ur_hi_count + en_count
        if total == 0: return "en"
        if ur_hi_count / total > 0.5: return "ur"
        if ur_hi_count / total > 0.2: return "mixed"
        return "en"

    @classmethod
    def estimate_speaking_duration(cls, word_count: int, lang: str = "en") -> float:
        wps = cls.WPS_BY_LANG.get(lang, 2.4)
        return (word_count / wps) * 1.15

    @classmethod
    def is_question(cls, text: str) -> bool:
        t = text.strip()
        if t.endswith("?"): return True
        first = t.split()[0].lower() if t else ""
        return first in cls.QUESTION_STARTERS

    @classmethod
    def is_exclamation(cls, text: str) -> bool:
        return text.strip().endswith("!")

    @classmethod
    def has_power_word(cls, text: str) -> bool:
        tl = text.lower()
        return any(pw in tl for pw in cls.POWER_WORDS)

    @classmethod
    def is_cta(cls, text: str) -> bool:
        tl = text.lower()
        return any(p in tl for p in cls.CTA_PHRASES)

    @classmethod
    def extract_emphasis_words(cls, text: str) -> List[str]:
        emphasis = []
        for m in re.finditer(r'\b[A-Z]{2,}\b', text):
            emphasis.append(m.group().lower())
        tl = text.lower()
        for pw in cls.POWER_WORDS:
            if pw in tl: emphasis.append(pw)
        for m in re.finditer(r'\b\d+[\.,]?\d*\s?(million|billion|trillion|percent|%|x)\b', tl):
            emphasis.append(m.group())
        return list(set(emphasis))


# ============================================================
# SECTION 3: READABILITY & COMPLEXITY
# ============================================================

class ReadabilityAnalyzer:
    @staticmethod
    def count_syllables(word: str) -> int:
        word = word.lower().strip()
        if len(word) <= 2: return 1
        vowels = "aeiouy"
        count = 0
        prev = False
        for ch in word:
            is_v = ch in vowels
            if is_v and not prev: count += 1
            prev = is_v
        if word.endswith("e") and count > 1: count -= 1
        if word.endswith("le") and len(word) > 2 and word[-3] not in vowels:
            count += 1
        return max(1, count)

    @classmethod
    def flesch_reading_ease(cls, text: str) -> float:
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        words = re.findall(r'\b\w+\b', text)
        if not sentences or not words: return 50.0
        total_syl = sum(cls.count_syllables(w) for w in words)
        score = 206.835 - 1.015*(len(words)/len(sentences)) - 84.6*(total_syl/len(words))
        return max(0.0, min(100.0, score))

    @classmethod
    def grade_level(cls, text: str) -> float:
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        words = re.findall(r'\b\w+\b', text)
        if not sentences or not words: return 6.0
        total_syl = sum(cls.count_syllables(w) for w in words)
        grade = 0.39*(len(words)/len(sentences)) + 11.8*(total_syl/len(words)) - 15.59
        return max(0.0, min(20.0, grade))

    @classmethod
    def vocabulary_diversity(cls, text: str) -> float:
        words = re.findall(r'\b\w+\b', text.lower())
        if not words: return 0.0
        return len(set(words)) / len(words)


# ============================================================
# SECTION 4: EMOTION & PACING DETECTOR
# ============================================================

class EmotionDetector:
    EMOTION_KEYWORDS: Dict[EmotionLabel, List[str]] = {
        EmotionLabel.EXCITED: ["amazing","incredible","awesome","fantastic","wow","exciting","thrilling","electrifying","unstoppable","epic","magnificent"],
        EmotionLabel.CURIOUS: ["discover","secret","hidden","reveal","mystery","unknown","surprising","interesting","fascinating","curious","explore"],
        EmotionLabel.SERIOUS: ["important","critical","serious","grave","significant","crucial","essential","vital","fundamental","warning"],
        EmotionLabel.CALM: ["peaceful","gentle","soft","quiet","calm","slow","steady","serene","tranquil","subtle","smooth","delicate"],
        EmotionLabel.URGENT: ["urgent","now","immediate","hurry","rush","fast","quick","rapid","instant","alert","warning","deadline","breaking"],
        EmotionLabel.INSPIRING: ["inspire","believe","achieve","dream","success","greatness","overcome","rise","transform","powerful","unstoppable","legend"],
        EmotionLabel.SHOCKING: ["shocking","unbelievable","insane","crazy","mind-blowing","jaw-dropping","incredible","unprecedented","outrageous"],
        EmotionLabel.SAD: ["sad","tragic","heartbreaking","devastating","loss","grief","painful","sorrow","mourn","dark","depressing"],
        EmotionLabel.HUMOROUS: ["funny","hilarious","laugh","joke","comedy","humor","ridiculous","absurd","witty","entertaining"],
    }

    @classmethod
    def detect_emotion(cls, text: str) -> Tuple[EmotionLabel, float]:
        tl = text.lower()
        scores: Dict[EmotionLabel, float] = {}
        for emotion, keywords in cls.EMOTION_KEYWORDS.items():
            score = sum(1.0 for kw in keywords if kw in tl)
            scores[emotion] = min(1.0, score / len(keywords) * 3.0)
        if "!" in text:
            scores[EmotionLabel.EXCITED] = scores.get(EmotionLabel.EXCITED, 0) + 0.2
            scores[EmotionLabel.URGENT] = scores.get(EmotionLabel.URGENT, 0) + 0.15
        if "?" in text:
            scores[EmotionLabel.CURIOUS] = scores.get(EmotionLabel.CURIOUS, 0) + 0.15
        if not scores: return EmotionLabel.NEUTRAL, 0.3
        best = max(scores, key=scores.get)
        best_score = scores[best]
        if best_score < 0.15: return EmotionLabel.NEUTRAL, 0.3
        return best, min(1.0, best_score)


class PacingDetector:
    @classmethod
    def determine_pacing(cls, sentence: str, emotion: EmotionLabel,
                         word_count: int, is_critical: bool = False) -> PacingType:
        fast = {EmotionLabel.EXCITED, EmotionLabel.URGENT, EmotionLabel.SHOCKING, EmotionLabel.HUMOROUS}
        slow = {EmotionLabel.CALM, EmotionLabel.SAD, EmotionLabel.INSPIRING}
        if emotion in fast: return PacingType.FAST
        if emotion in slow: return PacingType.SLOW
        if word_count <= 3: return PacingType.PAUSE if is_critical else PacingType.NORMAL
        if word_count > 25: return PacingType.SLOW
        return PacingType.NORMAL


# ============================================================
# SECTION 5: STRUCTURE DETECTOR
# ============================================================

class StructureDetector:
    @staticmethod
    def classify_sentence(text: str, index: int,
                          total_sentences: int, word_count: int) -> ScriptSection:
        tl = text.lower()
        progress = index / max(1, total_sentences - 1)
        if progress < 0.08: return ScriptSection.HOOK
        if progress < 0.2: return ScriptSection.INTRO
        if progress > 0.90: return ScriptSection.OUTRO
        if progress > 0.80:
            if LanguageUtils.is_cta(text): return ScriptSection.CTA
            if any(k in tl for k in ["subscribe","like","share","follow","click","link","comment"]):
                return ScriptSection.CTA
            return ScriptSection.OUTRO
        if any(k in tl for k in ["but here's the thing","here's why","the truth is",
                                  "what if","imagine this","think about","the secret"]):
            if 0.4 < progress < 0.7: return ScriptSection.CLIMAX
        if any(k in tl for k in ["now let's","moving on","next","another","also",
                                  "besides","furthermore","in addition","meanwhile"]):
            return ScriptSection.TRANSITION
        return ScriptSection.BODY

    @classmethod
    def build_section_map(cls, sentences: List[SentenceAnalysis]
                          ) -> Dict[ScriptSection, List[int]]:
        sm: Dict[ScriptSection, List[int]] = defaultdict(list)
        for sa in sentences:
            sm[sa.section].append(sa.index)
        return dict(sm)

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
    _words_preview = re.findall(r'\b\w+\b', test_script)
    _sents_preview = [s for s in re.split(r'[.!?]+', test_script) if s.strip()]
    print(f"   Words: {len(_words_preview)}")
    print(f"   Sentences: {len(_sents_preview)}")
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