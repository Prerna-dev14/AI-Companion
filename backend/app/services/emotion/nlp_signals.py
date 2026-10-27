import re
import math
from typing import Dict, Any, Tuple
from backend.app.schemas.emotion import TextEmotionResponse

# Curated affective lexicons with valence weights
POSITIVE_WORDS = {
    "happy": 0.8, "glad": 0.6, "great": 0.8, "joy": 0.9, "wonderful": 0.9,
    "excellent": 0.8, "love": 0.9, "excited": 0.85, "awesome": 0.8, "fun": 0.7,
    "delighted": 0.8, "celebrate": 0.75, "proud": 0.8, "smile": 0.6, "good": 0.5,
    "fantastic": 0.9, "blessed": 0.7, "thrilled": 0.9, "cheer": 0.7, "amazing": 0.85
}

NEGATIVE_SAD_WORDS = {
    "sad": -0.8, "unhappy": -0.7, "depressed": -0.9, "lonely": -0.8, "down": -0.5,
    "hopeless": -0.9, "cry": -0.8, "crying": -0.85, "grief": -0.9, "hurt": -0.7,
    "pain": -0.7, "miserable": -0.85, "heartbroken": -0.9, "gloomy": -0.6, "tears": -0.75
}

NEGATIVE_ANGRY_WORDS = {
    "angry": -0.8, "mad": -0.7, "furious": -0.95, "hate": -0.9, "annoyed": -0.6,
    "frustrated": -0.7, "irritated": -0.6, "rage": -0.95, "disgusted": -0.8, "pissed": -0.8
}

BORED_WORDS = {
    "bored": -0.3, "boring": -0.3, "tired": -0.4, "meh": -0.2, "dull": -0.4,
    "uninterested": -0.5, "whatever": -0.3, "apathy": -0.5, "monotonous": -0.4
}

class NLPTextSignalService:
    """
    Extracts structured intent, sentiment valence, and emotion probability distributions
    from text inputs independently from other modalities.
    """

    def analyze(self, text: str, language: str = "en") -> TextEmotionResponse:
        cleaned = text.strip()
        tokens = re.findall(r"\b\w+\b", cleaned.lower())

        # 1. Intent Detection
        intent = self._classify_intent(cleaned, tokens)

        # 2. Sentiment Valence Calculation (-1.0 to 1.0)
        sentiment_score, confidence = self._calculate_sentiment(tokens)

        # 3. Emotion Category Probability Distribution
        probabilities = self._compute_emotion_probabilities(tokens, sentiment_score)

        return TextEmotionResponse(
            modality="text",
            intent=intent,
            sentiment_score=sentiment_score,
            probabilities=probabilities,
            confidence=confidence,
            detected_language=language or "en",
        )

    def _classify_intent(self, text: str, tokens: list) -> str:
        text_lower = text.lower()
        if any(w in tokens for w in ["hello", "hi", "hey", "greetings", "howdy"]):
            return "greeting"
        if "?" in text or any(tokens[:2]) in ["what", "why", "how", "when", "who", "where", "can", "could"]:
            return "question"
        if any(w in tokens for w in ["thank", "thanks", "grateful", "appreciate"]):
            return "gratitude"
        if any(w in tokens for w in NEGATIVE_ANGRY_WORDS):
            return "venting"
        if any(w in tokens for w in NEGATIVE_SAD_WORDS):
            return "seeking_comfort"
        if any(w in tokens for w in POSITIVE_WORDS):
            return "sharing_positive"
        if any(w in tokens for w in BORED_WORDS):
            return "expressing_disengagement"
        return "general_conversation"

    def _calculate_sentiment(self, tokens: list) -> Tuple[float, float]:
        if not tokens:
            return 0.0, 0.5

        score = 0.0
        matches = 0

        for token in tokens:
            if token in POSITIVE_WORDS:
                score += POSITIVE_WORDS[token]
                matches += 1
            elif token in NEGATIVE_SAD_WORDS:
                score += NEGATIVE_SAD_WORDS[token]
                matches += 1
            elif token in NEGATIVE_ANGRY_WORDS:
                score += NEGATIVE_ANGRY_WORDS[token]
                matches += 1
            elif token in BORED_WORDS:
                score += BORED_WORDS[token]
                matches += 0.5

        if matches == 0:
            return 0.0, 0.65  # Confident neutral baseline

        normalized_score = max(-1.0, min(1.0, round(score / max(1.0, math.sqrt(matches)), 3)))
        confidence = min(0.95, round(0.65 + (matches * 0.08), 2))
        return normalized_score, confidence

    def _compute_emotion_probabilities(self, tokens: list, sentiment_score: float) -> Dict[str, float]:
        pos_hits = sum(1 for t in tokens if t in POSITIVE_WORDS)
        sad_hits = sum(1 for t in tokens if t in NEGATIVE_SAD_WORDS)
        angry_hits = sum(1 for t in tokens if t in NEGATIVE_ANGRY_WORDS)
        bored_hits = sum(1 for t in tokens if t in BORED_WORDS)

        # Raw weights
        w_happy = max(0.02, pos_hits * 1.5 + (max(0.0, sentiment_score) * 1.2))
        w_sad = max(0.02, sad_hits * 1.5 + (max(0.0, -sentiment_score) * 1.0))
        w_angry = max(0.01, angry_hits * 1.5 + (0.5 if sentiment_score < -0.4 and angry_hits > 0 else 0.0))
        w_bored = max(0.02, bored_hits * 1.2)
        w_neutral = max(0.15, 1.0 - (pos_hits + sad_hits + angry_hits + bored_hits) * 0.3)

        total = w_happy + w_sad + w_angry + w_bored + w_neutral
        return {
            "happy": round(w_happy / total, 3),
            "sad": round(w_sad / total, 3),
            "angry": round(w_angry / total, 3),
            "bored": round(w_bored / total, 3),
            "neutral": round(w_neutral / total, 3),
        }
