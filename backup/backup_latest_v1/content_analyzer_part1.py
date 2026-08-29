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


print("✅ content_analyzer.py PART 1/2 loaded — Data structures + Utils + Readability + Emotion + Structure.")
print("   👉 PART 2 mein ContentAnalyzerEngine (MAIN) + Export + Self-test hai.")