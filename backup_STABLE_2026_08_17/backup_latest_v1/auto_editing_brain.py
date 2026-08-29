# auto_editing_brain.py
# ==========================================================
# MY CREATION VIDEO GENERATOR — PHASE 1
# AUTO EDITING BRAIN v1.2 — Advanced Content-Aware Intelligence
# ==========================================================

from __future__ import annotations
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

# ============================================================
# STYLE FAMILIES
# ============================================================

STYLE_FAMILIES = {
    "luxury": {
        "keywords": ["luxury", "rich", "wealth", "mansion", "yacht", "supercar", "watch",
                      "diamond", "gold", "premium", "elite", "exclusive", "lifestyle",
                      "royal", "fashion", "brand", "expensive", "billionaire", "millionaire",
                      "villa", "jet", "resort", "champagne", "designer", "elegant"],
        "niche": "luxury_lifestyle",
        "energy": 0.62,
    },
    "future_tech": {
        "keywords": ["ai", "artificial intelligence", "robot", "future", "technology",
                      "quantum", "machine", "automation", "neural", "cyber", "space",
                      "science", "innovation", "digital", "software", "algorithm",
                      "data", "metaverse", "virtual", "simulation", "breakthrough",
                      "startup", "tech", "coding", "programming"],
        "niche": "quantum_future",
        "energy": 0.78,
    },
    "mystery": {
        "keywords": ["mystery", "secret", "hidden", "dark", "unknown", "crime",
                      "conspiracy", "truth", "buried", "forbidden", "haunted",
                      "ghost", "fear", "danger", "warning", "creepy", "evidence",
                      "lost", "missing", "strange", "unexplained", "classified"],
        "niche": "mystery",
        "energy": 0.72,
    },
    "wisdom": {
        "keywords": ["wisdom", "stoic", "stoicism", "mindset", "discipline",
                      "philosophy", "ancient", "peace", "control", "patience",
                      "silence", "growth", "meaning", "truth", "habits",
                      "self improvement", "motivation", "mental strength", "calm"],
        "niche": "stoic_wisdom",
        "energy": 0.45,
    },
    "interior_design": {
        "keywords": ["interior", "design", "room", "home", "house", "decor",
                      "architecture", "space", "living room", "bedroom", "kitchen",
                      "minimal", "aesthetic", "cozy", "modern", "renovation",
                      "transformation", "furniture", "lighting"],
        "niche": "interior_design",
        "energy": 0.52,
    },
    "finance": {
        "keywords": ["finance", "money", "invest", "stock", "trading", "crypto",
                      "business", "income", "profit", "market", "economy", "bank",
                      "budget", "tax", "asset", "debt", "financial freedom",
                      "compound", "saving", "wealth building", "cash"],
        "niche": "finance_simulation",
        "energy": 0.66,
    },
    "documentary": {
        "keywords": ["documentary", "history", "story", "explained", "timeline",
                      "rise", "fall", "empire", "war", "society", "culture",
                      "country", "civilization", "human", "people", "world"],
        "niche": "default",
        "energy": 0.55,
    },
    "health_wellness": {
        "keywords": ["health", "fitness", "wellness", "body", "mind", "sleep",
                      "diet", "nutrition", "exercise", "workout", "mental health",
                      "stress", "healing", "doctor", "medicine", "healthy"],
        "niche": "default",
        "energy": 0.54,
    },
    "education": {
        "keywords": ["learn", "education", "tutorial", "how to", "guide", "tips",
                      "tricks", "facts", "lesson", "course", "skill", "training"],
        "niche": "default",
        "energy": 0.56,
    },
    "travel": {
        "keywords": ["travel", "destination", "trip", "adventure", "explore",
                      "tour", "vacation", "journey", "wanderlust", "backpack",
                      "hotel", "beach", "mountain", "nature", "road trip"],
        "niche": "luxury_lifestyle",
        "energy": 0.58,
    },
}


# ============================================================
# AUTO BRAIN CORE CLASS
# ============================================================

class AutoEditingBrain:
    """Advanced auto-detect intelligence. Content-aware, no templates."""

    def __init__(self, history_file: Optional[str] = None):
        self._history: Dict[str, List[int]] = defaultdict(list)
        self._preset_usage: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self._history_file = Path(history_file) if history_file else None
        if self._history_file and self._history_file.exists():
            self._load_history()

    def _load_history(self):
        try:
            data = json.loads(self._history_file.read_text(encoding="utf-8"))
            for k, v in data.get("preset_usage", {}).items():
                self._preset_usage[k] = defaultdict(int, {int(kk): vv for kk, vv in v.items()})
            self._history = defaultdict(list, data.get("history", {}))
        except Exception:
            pass

    def _save_history(self):
        if not self._history_file:
            return
        try:
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            self._history_file.write_text(json.dumps({
                "preset_usage": {k: dict(v) for k, v in self._preset_usage.items()},
                "history": dict(self._history),
                "updated": datetime.now().isoformat()
            }, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _clean_text(self, text: Any) -> str:
        text = str(text or "").lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _tokenize(self, text: Any) -> List[str]:
        return self._clean_text(text).split()

    def detect_niche(self, script_text: Optional[str] = None,
                     niche_hint: Optional[str] = None,
                     keywords: Optional[List[str]] = None) -> Tuple[str, float]:
        """Detect best niche from content."""
        # If user explicitly selected a niche, respect it
        if niche_hint and str(niche_hint).lower() in {
            "luxury_lifestyle", "quantum_future", "mystery",
            "stoic_wisdom", "interior_design", "finance_simulation",
            "default", "auto",
        }:
            return str(niche_hint).lower(), 1.0

        combined = self._clean_text(script_text or "")
        if keywords:
            combined += " " + " ".join(str(k) for k in keywords)

        tokens = set(self._tokenize(combined))

        scores: Dict[str, float] = {}
        for family_key, family in STYLE_FAMILIES.items():
            score = 0.0
            for kw in family["keywords"]:
                kw_clean = self._clean_text(kw)
                if " " in kw_clean:
                    if kw_clean in combined:
                        score += 3.5
                else:
                    if kw_clean in tokens:
                        score += 1.5
            if score > 0:
                scores[family_key] = score

        if not scores:
            return "default", 0.3

        best_family = max(scores, key=scores.get)
        best_score = scores[best_family]
        total = sum(scores.values())
        confidence = min(1.0, best_score / max(total, 0.01) * 1.5)
        niche = STYLE_FAMILIES[best_family]["niche"]
        return niche, round(confidence, 3)

    def choose_preset(self, niche: str, render_count: int = 0,
                      script_text: Optional[str] = None) -> int:
        """Choose best preset number (1-8) with anti-repetition."""
        # FIX v1.2: ensure niche is valid string, init usage if missing
        niche = str(niche) if niche else "default"
        
        if niche not in self._preset_usage:
            self._preset_usage[niche] = defaultdict(int)
        usage = self._preset_usage[niche]

        content_hash = 0
        if script_text:
            content_hash = int(hashlib.md5(script_text.encode()).hexdigest()[:8], 16)

        preset_scores = {}
        for p in range(1, 9):
            used = usage.get(p, 0)
            score = 100.0 - (used * 8.0)
            variation = ((render_count + content_hash + p * 7) % 17) / 17.0 * 15.0
            score += variation
            preset_scores[p] = score

        best_preset = max(preset_scores, key=preset_scores.get)

        if best_preset not in self._preset_usage[niche]:
            self._preset_usage[niche][best_preset] = 0
        self._preset_usage[niche][best_preset] += 1
        self._history[niche].append(best_preset)
        if len(self._history[niche]) > 50:
            self._history[niche] = self._history[niche][-50:]

        self._save_history()
        return best_preset

    def get_energy_level(self, niche: str) -> float:
        for family_key, family in STYLE_FAMILIES.items():
            if family["niche"] == niche:
                return family["energy"]
        return 0.55

    def analyze_complexity(self, script_text: str, clip_count: int = 0) -> float:
        tokens = self._tokenize(script_text)
        word_count = len(tokens)
        length_factor = min(1.0, word_count / 300.0)
        unique_ratio = len(set(tokens)) / max(1, word_count)
        sentences = re.split(r"[.!?]+", script_text or "")
        avg_sentence_len = word_count / max(1, len(sentences))
        sentence_factor = min(1.0, avg_sentence_len / 25.0)
        clip_factor = min(1.0, clip_count / 30.0)
        complexity = (
            length_factor * 0.30 + unique_ratio * 0.25 +
            sentence_factor * 0.25 + clip_factor * 0.20
        )
        return round(min(1.0, max(0.1, complexity)), 3)

    def get_variation_seed(self, preset_number: int, render_count: int,
                           niche: str = "default") -> int:
        usage = self._preset_usage.get(niche, {}).get(preset_number, 0)
        base = preset_number * 100 + niche.__hash__() % 1000
        return base + render_count * 13 + usage * 7


# ============================================================
# SINGLETON
# ============================================================

_brain_instance: Optional[AutoEditingBrain] = None


def get_auto_brain() -> AutoEditingBrain:
    global _brain_instance
    if _brain_instance is None:
        history_path = Path(__file__).parent / "config" / "auto_brain_history.json"
        _brain_instance = AutoEditingBrain(history_file=str(history_path))
    return _brain_instance


def auto_detect_niche(script_text: str = "",
                      niche_hint: str = "",
                      keywords: List[str] = None) -> Tuple[str, float, Dict[str, Any]]:
    brain = get_auto_brain()
    niche, confidence = brain.detect_niche(script_text, niche_hint, keywords)
    energy = brain.get_energy_level(niche)
    preset = brain.choose_preset(niche, render_count=0, script_text=script_text)
    complexity = brain.analyze_complexity(script_text)
    return niche, confidence, {
        "niche": niche,
        "confidence": confidence,
        "energy": energy,
        "recommended_preset": preset,
        "complexity": complexity,
    }


def auto_choose_preset(niche: str, render_count: int = 0,
                       script_text: str = "") -> int:
    return get_auto_brain().choose_preset(niche, render_count, script_text)


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    brain = AutoEditingBrain()

    tests = [
        "luxury watches and supercars billionaire lifestyle",
        "artificial intelligence robots future technology breakthrough",
        "dark mystery crime scene hidden truth revealed",
        "stoic wisdom discipline mindset ancient philosophy",
        "modern interior design home renovation before after transformation",
        "stock market crypto trading investment strategy finance",
    ]

    print("=" * 60)
    print("AUTO EDITING BRAIN v1.2 — NICHE DETECTION TEST")
    print("=" * 60)

    for i, text in enumerate(tests):
        try:
            niche, conf, info = auto_detect_niche(script_text=text)
            print(f"[{i+1}] \"{text[:55]}...\"")
            print(f"    -> Niche: {niche} | Confidence: {conf:.0%} | Energy: {info['energy']:.2f}")
            print(f"    -> Preset #{info['recommended_preset']} | Complexity: {info['complexity']:.2f}")
        except Exception as e:
            print(f"[{i+1}] ERROR: {e}")

    print("\n" + "=" * 60)
    print("SELF-TEST COMPLETE")
    print("=" * 60)
