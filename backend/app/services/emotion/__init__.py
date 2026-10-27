"""Emotion Engine Module.
Independent multimodal emotion fusion engine.
Combines structured signals from NLP, speech, and vision.
"""

from backend.app.services.emotion.engine import (
    BaseEmotionEngine,
    MultimodalEmotionEngine,
    emotion_engine,
)

__all__ = [
    "BaseEmotionEngine",
    "MultimodalEmotionEngine",
    "emotion_engine",
]
