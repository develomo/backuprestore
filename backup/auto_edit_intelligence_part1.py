# ============================================================
# PHASE 3 — FILE 1: auto_edit_intelligence.py (PART 1/2)
# ============================================================
# Purpose:
#   - Script/keyword se content analyze karta hai
#   - Niche auto-detect karta hai (AI-powered keyword matching)
#   - Best editing preset auto-choose karta hai (niche ke 8 presets mein se)
#   - Advanced auto-edit pipeline — full intelligence engine
#
# Usage:
#   from auto_edit_intelligence import AutoEditIntelligence
#   engine = AutoEditIntelligence()
#   result = engine.analyze_and_decide(script_text="...")
#   print(result.detected_niche, result.recommended_preset.preset_number)
#
# Dependencies:
#   - niche_editing_presets.py (Phase 1 output)
# ============================================================

import re
import math
import random
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import Counter
from enum import Enum

# ─── Logging ───────────────────────────────────────────────
logger = logging.getLogger("AutoEditIntelligence")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] [AutoIntel] %(message)s", datefmt="%H:%M:%S"
    ))
    logger.addHandler(h)


# ============================================================
# SECTION 1: NICHE KEYWORD DATABASE (Weighted)
# ============================================================

class NicheKeywordDB:
    """Advanced niche keyword database with weighted scoring.
    Har niche ke liye high-signal keywords — AI auto-detection ke liye.
    Keywords weighted hain (weight jitna zyada, utna strong signal).
    """

    NICHE_KEYWORDS: Dict[str, Dict[str, List[Tuple[str, float]]]] = {
        "luxury_lifestyle": {
            "core": [
                ("luxury", 1.0), ("lifestyle", 0.9), ("wealth", 0.85),
                ("millionaire", 0.9), ("billionaire", 0.95), ("mansions", 0.85),
                ("yacht", 0.9), ("private jet", 0.95), ("rolex", 0.85),
                ("ferrari", 0.85), ("lamborghini", 0.85), ("designer", 0.7),
                ("exclusive", 0.75), ("expensive", 0.7), ("luxurious", 0.85),
                ("lavish", 0.8), ("elegance", 0.7), ("penthouse", 0.8),
                ("villa", 0.75), ("high-end", 0.75), ("5-star", 0.8),
                ("first class", 0.85), ("bespoke", 0.7), ("couture", 0.75),
                ("supercar", 0.8), ("private island", 0.9), ("helicopter", 0.75),
                ("limousine", 0.7), ("champagne", 0.75), ("diamond", 0.7),
                ("premium", 0.65), ("sophisticated", 0.65), ("estate", 0.7),
            ],
            "contextual": [
                ("brand", 0.45), ("fashion", 0.5), ("resort", 0.55),
                ("suite", 0.55), ("limited edition", 0.6), ("rare", 0.55),
                ("custom", 0.4), ("handcrafted", 0.5), ("collection", 0.45),
            ],
            "negative": [
                ("budget", -0.6), ("cheap", -0.7), ("affordable", -0.55),
                ("discount", -0.65), ("poor", -0.5),
            ],
            "phrase_weight": 1.3,
        },
        "quantum_future": {
            "core": [
                ("technology", 0.85), ("future", 0.9), ("artificial intelligence", 1.0),
                ("AI", 0.95), ("machine learning", 0.9), ("robot", 0.85),
                ("automation", 0.8), ("quantum", 0.9), ("innovation", 0.8),
                ("futuristic", 0.9), ("metaverse", 0.85), ("blockchain", 0.75),
                ("crypto", 0.7), ("neural", 0.85), ("brain-computer", 0.9),
                ("cyborg", 0.85), ("nanotechnology", 0.85), ("biotech", 0.8),
                ("hologram", 0.8), ("virtual reality", 0.85), ("augmented reality", 0.85),
                ("sci-fi", 0.75), ("cyberpunk", 0.75), ("hyperloop", 0.8),
                ("3d printing", 0.7), ("fusion", 0.7), ("drone", 0.65),
                ("electric vehicle", 0.7), ("digital", 0.7), ("space", 0.7),
                ("mars", 0.75), ("rocket", 0.7), ("genetic", 0.7),
            ],
            "contextual": [
                ("science", 0.5), ("research", 0.5), ("breakthrough", 0.6),
                ("discovery", 0.55), ("next generation", 0.6), ("revolutionary", 0.6),
                ("advanced", 0.5), ("smart", 0.45), ("algorithm", 0.5),
            ],
            "negative": [
                ("old", -0.3), ("traditional", -0.4), ("outdated", -0.5),
                ("vintage", -0.3),
            ],
            "phrase_weight": 1.3,
        },
        "mystery": {
            "core": [
                ("mystery", 1.0), ("unsolved", 0.9), ("disappearance", 0.9),
                ("crime", 0.85), ("murder", 0.85), ("detective", 0.85),
                ("conspiracy", 0.9), ("secret", 0.8), ("hidden", 0.75),
                ("enigma", 0.85), ("haunted", 0.85), ("paranormal", 0.85),
                ("supernatural", 0.8), ("ghost", 0.8), ("occult", 0.8),
                ("serial killer", 0.9), ("kidnapping", 0.85), ("missing", 0.8),
                ("cold case", 0.85), ("investigation", 0.75), ("forensic", 0.7),
                ("vanished", 0.85), ("creepy", 0.7), ("eerie", 0.75),
                ("bizarre", 0.7), ("inexplicable", 0.8), ("cryptic", 0.8),
                ("puzzle", 0.75),
            ],
            "contextual": [
                ("story", 0.4), ("case", 0.45), ("true", 0.45),
                ("real", 0.4), ("discovered", 0.4), ("revealed", 0.45),
            ],
            "negative": [
                ("comedy", -0.5), ("funny", -0.55), ("happy", -0.3),
            ],
            "phrase_weight": 1.25,
        },
        "stoic_wisdom": {
            "core": [
                ("stoic", 1.0), ("stoicism", 0.95), ("philosophy", 0.85),
                ("wisdom", 0.9), ("discipline", 0.85), ("mindset", 0.8),
                ("marcus aurelius", 0.95), ("seneca", 0.9), ("epictetus", 0.9),
                ("meditation", 0.7), ("mindfulness", 0.75), ("inner peace", 0.8),
                ("resilience", 0.8), ("adversity", 0.75), ("virtue", 0.8),
                ("character", 0.7), ("purpose", 0.75), ("meaning", 0.7),
                ("self-improvement", 0.75), ("mastery", 0.7), ("detachment", 0.75),
                ("acceptance", 0.65), ("tranquility", 0.7), ("serenity", 0.65),
                ("ancient", 0.6), ("reflection", 0.65), ("contemplation", 0.7),
            ],
            "contextual": [
                ("life", 0.45), ("lesson", 0.45), ("principle", 0.5),
                ("quote", 0.4), ("teachings", 0.5), ("practice", 0.4),
            ],
            "negative": [
                ("money", -0.35), ("get rich", -0.5), ("hustle", -0.4),
            ],
            "phrase_weight": 1.2,
        },
        "interior_design": {
            "core": [
                ("interior", 0.95), ("design", 0.8), ("architecture", 0.85),
                ("home decor", 0.9), ("furniture", 0.8), ("renovation", 0.85),
                ("minimalist", 0.85), ("contemporary", 0.7), ("aesthetic", 0.7),
                ("ambiance", 0.75), ("lighting", 0.75), ("scandinavian", 0.8),
                ("industrial", 0.75), ("bohemian", 0.8), ("feng shui", 0.8),
                ("wabi-sabi", 0.85), ("japandi", 0.85), ("decor", 0.75),
                ("living room", 0.7), ("bedroom", 0.65), ("kitchen", 0.65),
                ("color palette", 0.7), ("open concept", 0.75), ("layout", 0.65),
                ("floor plan", 0.7), ("statement piece", 0.7), ("texture", 0.65),
            ],
            "contextual": [
                ("beautiful", 0.45), ("stunning", 0.5), ("elegant", 0.5),
                ("cozy", 0.45), ("transform", 0.5), ("makeover", 0.55),
                ("inspiration", 0.5),
            ],
            "negative": [
                ("outdoor", -0.35), ("car", -0.4), ("technology", -0.3),
            ],
            "phrase_weight": 1.2,
        },
        "finance_simulation": {
            "core": [
                ("finance", 0.9), ("money", 0.8), ("investing", 0.85),
                ("stock market", 0.9), ("trading", 0.85), ("crypto", 0.8),
                ("bitcoin", 0.8), ("economy", 0.8), ("inflation", 0.75),
                ("business", 0.75), ("entrepreneur", 0.8), ("startup", 0.75),
                ("revenue", 0.7), ("profit", 0.7), ("passive income", 0.85),
                ("real estate", 0.75), ("dividend", 0.7), ("compound interest", 0.8),
                ("wealth building", 0.85), ("financial freedom", 0.9), ("portfolio", 0.7),
                ("asset", 0.65), ("bull market", 0.8), ("bear market", 0.75),
                ("IPO", 0.7), ("valuation", 0.65), ("tax", 0.55),
                ("savings", 0.6), ("budget", 0.55), ("recession", 0.7),
            ],
            "contextual": [
                ("million", 0.55), ("billion", 0.6), ("dollar", 0.5),
                ("growth", 0.5), ("strategy", 0.5), ("prediction", 0.5),
            ],
            "negative": [
                ("broke", -0.4),
            ],
            "phrase_weight": 1.25,
        },
        "default": {
            "core": [
                ("video", 0.4), ("content", 0.35), ("watch", 0.3),
                ("subscribe", 0.25), ("like", 0.2),
            ],
            "contextual": [],
            "negative": [],
            "phrase_weight": 1.0,
        },
    }

    # Tone keyword mapping — helps preset selection
    TONE_KEYWORDS: Dict[str, List[Tuple[str, float]]] = {
        "urgent_fast": [
            ("urgent", 0.85), ("breaking", 0.8), ("alert", 0.75),
            ("warning", 0.7), ("hurry", 0.7), ("rush", 0.65),
            ("fast", 0.55), ("quick", 0.5), ("immediately", 0.7),
        ],
        "calm_slow": [
            ("peaceful", 0.7), ("calm", 0.75), ("gentle", 0.7),
            ("slow", 0.6), ("quiet", 0.65), ("relaxing", 0.7),
            ("serene", 0.75), ("mindful", 0.65), ("meditative", 0.7),
        ],
        "dramatic": [
            ("shocking", 0.8), ("unbelievable", 0.75), ("dramatic", 0.8),
            ("insane", 0.7), ("mind-blowing", 0.85), ("jaw-dropping", 0.85),
            ("epic", 0.7), ("revolutionary", 0.65), ("unprecedented", 0.75),
        ],
        "educational": [
            ("learn", 0.7), ("explain", 0.7), ("how to", 0.75),
            ("guide", 0.7), ("tutorial", 0.75), ("lesson", 0.65),
            ("education", 0.7), ("fact", 0.55), ("science", 0.55),
        ],
        "inspirational": [
            ("inspire", 0.75), ("motivation", 0.8), ("success", 0.7),
            ("achieve", 0.7), ("dream", 0.65), ("believe", 0.6),
            ("transform", 0.65), ("overcome", 0.7), ("greatness", 0.7),
        ],
    }


# ============================================================
# SECTION 2: DATA STRUCTURES
# ============================================================

class DetectedTone(Enum):
    URGENT_FAST = "urgent_fast"
    CALM_SLOW = "calm_slow"
    DRAMATIC = "dramatic"
    EDUCATIONAL = "educational"
    INSPIRATIONAL = "inspirational"
    NEUTRAL = "neutral"
    MIXED = "mixed"


@dataclass
class NicheScore:
    niche: str
    score: float
    matched_keywords: List[str] = field(default_factory=list)
    core_matches: int = 0
    contextual_matches: int = 0
    negative_matches: int = 0

    @property
    def is_confident(self) -> bool:
        return self.score >= 0.35


@dataclass
class PresetRecommendation:
    niche: str
    preset_number: int
    preset_label: str
    confidence: float
    reason: str
    matched_keywords: List[str] = field(default_factory=list)


@dataclass
class ContentAnalysis:
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    dominant_tone: DetectedTone
    tone_scores: Dict[str, float] = field(default_factory=dict)
    keyword_density: Dict[str, float] = field(default_factory=dict)
    complexity_score: float = 0.0
    energy_score: float = 0.0


@dataclass
class AutoEditDecision:
    detected_niche: str
    niche_scores: List[NicheScore]
    recommended_preset: PresetRecommendation
    content_analysis: ContentAnalysis
    confidence: float
    scene_change_points: List[float] = field(default_factory=list)
    edit_complexity: str = "normal"
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    @property
    def is_reliable(self) -> bool:
        return self.confidence >= 0.6

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected_niche": self.detected_niche,
            "niche_scores": [
                {"niche": ns.niche, "score": round(ns.score, 3),
                 "core_matches": ns.core_matches, "contextual_matches": ns.contextual_matches}
                for ns in sorted(self.niche_scores, key=lambda x: x.score, reverse=True)
            ],
            "recommended_preset": {
                "niche": self.recommended_preset.niche,
                "preset_number": self.recommended_preset.preset_number,
                "preset_label": self.recommended_preset.preset_label,
                "confidence": round(self.recommended_preset.confidence, 3),
                "reason": self.recommended_preset.reason,
                "matched_keywords": self.recommended_preset.matched_keywords[:15],
            },
            "content_analysis": {
                "word_count": self.content_analysis.word_count,
                "sentence_count": self.content_analysis.sentence_count,
                "avg_sentence_length": round(self.content_analysis.avg_sentence_length, 1),
                "dominant_tone": self.content_analysis.dominant_tone.value,
                "complexity_score": round(self.content_analysis.complexity_score, 3),
                "energy_score": round(self.content_analysis.energy_score, 3),
            },
            "confidence": round(self.confidence, 3),
            "edit_complexity": self.edit_complexity,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
        }


# ============================================================
# SECTION 3: CONTENT ANALYZER
# ============================================================

class ContentAnalyzer:
    """Analyzes script text for tone, complexity, energy, keyword density."""

    COMPLEX_INDICATORS: List[str] = [
        "however", "therefore", "consequently", "furthermore", "nevertheless",
        "nonetheless", "meanwhile", "subsequently", "accordingly", "moreover",
        "specifically", "particularly", "essentially", "fundamentally",
        "paradoxically", "interestingly", "surprisingly", "notably",
        "in contrast", "on the other hand", "in addition", "as a result",
    ]

    HIGH_ENERGY_WORDS: List[str] = [
        "amazing", "incredible", "unbelievable", "shocking", "mind-blowing",
        "insane", "crazy", "wild", "explosive", "massive", "huge", "enormous",
        "unstoppable", "revolutionary", "breakthrough", "never seen before",
        "game-changer", "ultimate", "extreme", "absolute", "total",
    ]

    LOW_ENERGY_WORDS: List[str] = [
        "gentle", "soft", "quiet", "peaceful", "calm", "serene",
        "subtle", "delicate", "mild", "gradual", "slow", "steady",
    ]

    @staticmethod
    def count_words(text: str) -> int:
        if not text:
            return 0
        return len(re.findall(r'\b\w+\b', text.lower()))

    @staticmethod
    def count_sentences(text: str) -> int:
        if not text:
            return 0
        sentences = re.split(r'[.!?]+', text)
        return max(1, len([s for s in sentences if s.strip()]))

    @classmethod
    def analyze(cls, text: str) -> ContentAnalysis:
        if not text or not text.strip():
            return ContentAnalysis(
                word_count=0, sentence_count=0, avg_sentence_length=0.0,
                dominant_tone=DetectedTone.NEUTRAL, tone_scores={},
                keyword_density={}, complexity_score=0.0, energy_score=0.5
            )

        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        word_count = len(words)
        sentence_count = cls.count_sentences(text)
        avg_sentence_len = word_count / max(1, sentence_count)

        # ── Tone Detection ──────────────────────────────
        tone_scores: Dict[str, float] = {}
        for tone_name, kw_list in NicheKeywordDB.TONE_KEYWORDS.items():
            score = 0.0
            for kw, weight in kw_list:
                count = len(re.findall(re.escape(kw.lower()), text_lower))
                if count > 0:
                    score += weight * count
            normalized = score / max(1, math.sqrt(word_count)) * 5
            tone_scores[tone_name] = min(1.0, max(0.0, normalized))

        if not tone_scores:
            dominant_tone = DetectedTone.NEUTRAL
        else:
            best_tone = max(tone_scores, key=tone_scores.get)
            best_score = tone_scores[best_tone]
            if best_score < 0.15:
                dominant_tone = DetectedTone.NEUTRAL
            elif best_score < 0.25:
                dominant_tone = DetectedTone.MIXED
            else:
                try:
                    dominant_tone = DetectedTone(best_tone)
                except ValueError:
                    dominant_tone = DetectedTone.MIXED

        # ── Keyword Density ─────────────────────────────
        keyword_density: Dict[str, float] = {}
        stopwords = {"the","a","an","is","are","was","were","in","on","at","to",
                      "for","of","and","or","but","it","this","that","with","from",
                      "by","as","be","has","have","had","do","does","did","will",
                      "would","can","could","should","may","might","not","so","if",
                      "then","than","also","just","now","very","really","about","into"}
        freq = Counter(w for w in words if w not in stopwords and len(w) > 1)
        total = sum(freq.values())
        for w, c in freq.most_common(30):
            if total > 0:
                keyword_density[w] = c / total

        # ── Complexity Score ────────────────────────────
        complex_word_count = sum(1 for w in words if len(w) > 8)
        complex_indicator_count = sum(
            1 for ind in cls.COMPLEX_INDICATORS if ind.lower() in text_lower
        )
        complexity_raw = (
            (complex_word_count / max(1, word_count)) * 0.4 +
            (min(complex_indicator_count, 10) / 10) * 0.3 +
            (min(avg_sentence_len, 30) / 30) * 0.3
        )
        complexity_score = min(1.0, max(0.0, complexity_raw))

        # ── Energy Score ────────────────────────────────
        high_count = sum(1 for w in cls.HIGH_ENERGY_WORDS if w.lower() in text_lower)
        low_count = sum(1 for w in cls.LOW_ENERGY_WORDS if w.lower() in text_lower)
        energy_raw = 0.5
        energy_raw += (high_count / max(1, sentence_count)) * 0.3
        energy_raw -= (low_count / max(1, sentence_count)) * 0.3
        if tone_scores.get("urgent_fast", 0) > 0.3:
            energy_raw += 0.2
        elif tone_scores.get("dramatic", 0) > 0.3:
            energy_raw += 0.15
        if tone_scores.get("calm_slow", 0) > 0.3:
            energy_raw -= 0.2
        energy_score = min(1.0, max(0.0, energy_raw))

        return ContentAnalysis(
            word_count=word_count, sentence_count=sentence_count,
            avg_sentence_length=avg_sentence_len, dominant_tone=dominant_tone,
            tone_scores=tone_scores, keyword_density=keyword_density,
            complexity_score=complexity_score, energy_score=energy_score,
        )


# ============================================================
# SECTION 4: NICHE DETECTOR
# ============================================================

class NicheDetector:
    """AI-powered niche detection using weighted keyword analysis."""

    MIN_SCORE_THRESHOLD = 0.08
    DIVERSITY_BOOST = 1.15

    @classmethod
    def detect_niche(cls, text: str) -> Tuple[str, List[NicheScore]]:
        if not text or not text.strip():
            return "default", [NicheScore(niche="default", score=0.5)]

        text_lower = text.lower()
        all_scores: List[NicheScore] = []

        for niche, keyword_groups in NicheKeywordDB.NICHE_KEYWORDS.items():
            core_kws = keyword_groups.get("core", [])
            contextual_kws = keyword_groups.get("contextual", [])
            negative_kws = keyword_groups.get("negative", [])
            phrase_weight = keyword_groups.get("phrase_weight", 1.0)

            # Core matching
            core_score = 0.0
            core_matches_list: List[str] = []
            for kw, weight in core_kws:
                count = len(re.findall(re.escape(kw.lower()), text_lower))
                if count > 0:
                    core_score += weight * count
                    core_matches_list.append(kw)

            # Contextual matching
            ctx_score = 0.0
            ctx_matches_list: List[str] = []
            for kw, weight in contextual_kws:
                count = len(re.findall(re.escape(kw.lower()), text_lower))
                if count > 0:
                    ctx_score += weight * count
                    ctx_matches_list.append(kw)

            # Negative matching (penalty)
            neg_score = 0.0
            neg_matches_list: List[str] = []
            for kw, weight in negative_kws:
                count = len(re.findall(re.escape(kw.lower()), text_lower))
                if count > 0:
                    neg_score += weight * count
                    neg_matches_list.append(kw)

            # Phrase bonus
            phrase_bonus = 0.0
            for kw, weight in core_kws:
                if " " in kw:
                    count = len(re.findall(re.escape(kw.lower()), text_lower))
                    if count > 0:
                        phrase_bonus += weight * count * (phrase_weight - 1.0)

            # Normalize
            word_count = max(1, len(re.findall(r'\b\w+\b', text_lower)))
            raw = max(0.0, core_score + ctx_score * 0.5 + neg_score)
            normalized = raw / max(1, math.sqrt(word_count)) * 3.0
            normalized += phrase_bonus / max(1, math.sqrt(word_count)) * 2.0

            # Diversity boost
            unique_count = len(set(core_matches_list + ctx_matches_list))
            if unique_count >= 5:
                normalized *= cls.DIVERSITY_BOOST
            elif unique_count >= 3:
                normalized *= 1.08

            final = min(1.0, max(0.0, normalized))
            all_scores.append(NicheScore(
                niche=niche, score=final,
                matched_keywords=core_matches_list + ctx_matches_list,
                core_matches=len(set(core_matches_list)),
                contextual_matches=len(set(ctx_matches_list)),
                negative_matches=len(set(neg_matches_list)),
            ))

        all_scores.sort(key=lambda x: x.score, reverse=True)
        meaningful = [s for s in all_scores if s.score >= cls.MIN_SCORE_THRESHOLD]

        if not meaningful:
            return "default", all_scores

        best = meaningful[0]

        # Tie-breaking
        if len(meaningful) >= 2:
            second = meaningful[1]
            gap = best.score - second.score
            if gap < 0.15 and second.core_matches > best.core_matches:
                best = second
            elif best.negative_matches > 0 and second.negative_matches == 0 and gap < 0.10:
                best = second

        logger.info(
            f"NicheDetect → {best.niche} (score={best.score:.3f}, "
            f"core={best.core_matches}, ctx={best.contextual_matches})"
        )
        return best.niche, all_scores


print("✅ auto_edit_intelligence.py PART 1/2 loaded — NicheKeywordDB, ContentAnalyzer, NicheDetector ready.")
print("   👉 PART 2 mein PresetSelector + AutoEditIntelligence + SceneDetection hai.")