import math
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.emotion import (
    EmotionalState,
    MultimodalFusionRequest,
    MultimodalFusionResponse,
    TextEmotionResponse,
    VoiceEmotionResponse,
)
from backend.app.schemas.vision import VisionSignalResponse
from backend.app.models.entities import EmotionEvent, EmotionSource

ALL_EMOTIONS = ["neutral", "happy", "sad", "angry", "bored", "surprised", "confused"]

# Base modality weights when all modalities are active at full confidence
BASE_WEIGHTS = {
    "text": 0.45,
    "voice": 0.35,
    "face": 0.20,
}


class BaseEmotionEngine:
    """Base interface for multimodal emotion fusion."""
    
    async def fuse(
        self,
        request: MultimodalFusionRequest,
        db: Optional[AsyncSession] = None,
    ) -> MultimodalFusionResponse:
        raise NotImplementedError


class MultimodalEmotionEngine(BaseEmotionEngine):
    """Independent Multimodal Emotion Engine.
    
    Adheres strictly to the Emotion Engine Independence principle:
    Structured signals from decoupled modalities (text NLP, voice prosody,
    face vision) are fused mathematically into a normalized EmotionalState.
    """

    def __init__(self, temporal_smoothing_alpha: float = 0.70):
        """
        Args:
            temporal_smoothing_alpha: Weight given to current measurement (0.0 to 1.0).
                                      Remainder (1 - alpha) is given to previous state.
        """
        self.alpha = max(0.1, min(1.0, temporal_smoothing_alpha))

    async def fuse(
        self,
        request: MultimodalFusionRequest,
        db: Optional[AsyncSession] = None,
    ) -> MultimodalFusionResponse:
        """Fuses text, voice, and facial signals into a single normalized EmotionalState."""
        text = request.text_signal
        voice = request.voice_signal
        face = request.face_signal
        prev = request.previous_state

        active_modalities: List[str] = []
        modality_probs: Dict[str, Dict[str, float]] = {}
        modality_confidences: Dict[str, float] = {}
        modality_weights: Dict[str, float] = {}

        # 1. Inspect Text Signal
        text_active = text is not None and bool(text.probabilities)
        if text_active:
            active_modalities.append("text")
            modality_probs["text"] = self._normalize_prob_dict(text.probabilities)
            modality_confidences["text"] = max(0.1, min(1.0, text.confidence))
            modality_weights["text"] = BASE_WEIGHTS["text"] * modality_confidences["text"]

        # 2. Inspect Voice Signal
        voice_active = voice is not None and bool(voice.probabilities)
        if voice_active:
            active_modalities.append("voice")
            modality_probs["voice"] = self._normalize_prob_dict(voice.probabilities)
            modality_confidences["voice"] = max(0.1, min(1.0, voice.confidence))
            modality_weights["voice"] = BASE_WEIGHTS["voice"] * modality_confidences["voice"]

        # 3. Inspect Facial Vision Signal
        face_active = False
        if face is not None:
            # Handle either VisionSignalResponse or dict payload
            face_detected = getattr(face, "face_detected", None)
            if face_detected is None and isinstance(face, dict):
                face_detected = face.get("face_detected", False)
            
            if face_detected:
                face_active = True
                active_modalities.append("face")
                
                # Derive face probability distribution
                face_p = self._derive_face_probabilities(face)
                modality_probs["face"] = face_p

                # Quality attenuation based on lighting and status
                lighting = getattr(face, "lighting_score", 1.0)
                conf = getattr(face, "confidence", 0.8)
                status = getattr(face, "status", "ok")

                quality_mult = lighting * conf
                if status in ["poor_lighting", "low_confidence"]:
                    quality_mult *= 0.5

                modality_confidences["face"] = max(0.1, min(1.0, conf * lighting))
                modality_weights["face"] = BASE_WEIGHTS["face"] * max(0.1, quality_mult)

        # 4. Handle Case: No Active Modalities (Fallback Baseline)
        if not active_modalities:
            fallback_probs = {e: 0.05 for e in ALL_EMOTIONS}
            fallback_probs["neutral"] = 0.70
            fallback_probs = self._normalize_prob_dict(fallback_probs)
            
            return MultimodalFusionResponse(
                dominant_emotion="neutral",
                probabilities=fallback_probs,
                confidence=0.50,
                intensity=0.10,
                uncertainty=0.10,
                sources=[],
                modality_status={
                    "text": False,
                    "voice": False,
                    "face": False,
                },
                timestamp=datetime.now(timezone.utc),
            )

        # 5. Normalize Modality Weights
        total_weight = sum(modality_weights.values())
        if total_weight > 0:
            norm_weights = {m: w / total_weight for m, w in modality_weights.items()}
        else:
            norm_weights = {m: 1.0 / len(active_modalities) for m in active_modalities}

        # 6. Weighted Multimodal Probability Blending
        blended_probs: Dict[str, float] = {e: 0.0 for e in ALL_EMOTIONS}
        for m in active_modalities:
            w = norm_weights[m]
            p_dist = modality_probs[m]
            for e in ALL_EMOTIONS:
                blended_probs[e] += w * p_dist.get(e, 0.0)

        blended_probs = self._normalize_prob_dict(blended_probs)

        # 7. Calculate Intensity / Arousal
        raw_intensity = self._calculate_intensity(text, voice, face, blended_probs)

        # 8. Calculate Modality Conflict & Uncertainty
        divergence = self._calculate_divergence(active_modalities, modality_probs)
        entropy = self._calculate_normalized_entropy(blended_probs)
        
        weighted_conf = sum(norm_weights[m] * modality_confidences[m] for m in active_modalities)
        uncertainty = max(0.0, min(1.0, 0.5 * divergence + 0.5 * entropy))
        overall_confidence = max(0.1, min(1.0, weighted_conf * (1.0 - 0.4 * uncertainty)))

        # 9. Temporal Smoothing (if prior state is provided)
        if prev and prev.probabilities:
            blended_probs = self._smooth_probabilities(blended_probs, prev.probabilities, self.alpha)
            raw_intensity = self.alpha * raw_intensity + (1.0 - self.alpha) * prev.intensity
            overall_confidence = self.alpha * overall_confidence + (1.0 - self.alpha) * prev.confidence
            uncertainty = self.alpha * uncertainty + (1.0 - self.alpha) * prev.uncertainty

        # 10. Select Dominant Emotion
        dominant_emotion = max(blended_probs, key=blended_probs.get)
        if blended_probs[dominant_emotion] < 0.22:
            dominant_emotion = "neutral"

        # Construct final response
        fused_state = MultimodalFusionResponse(
            dominant_emotion=dominant_emotion,
            probabilities=blended_probs,
            confidence=round(overall_confidence, 4),
            intensity=round(raw_intensity, 4),
            uncertainty=round(uncertainty, 4),
            sources=active_modalities,
            modality_status={
                "text": text_active,
                "voice": voice_active,
                "face": face_active,
            },
            timestamp=datetime.now(timezone.utc),
        )

        # 11. Optional Persistence to Database
        if request.persist and request.session_id and db is not None:
            event_id = await self._persist_event(fused_state, request, db)
            fused_state.event_id = event_id

        return fused_state

    def _derive_face_probabilities(self, face: Any) -> Dict[str, float]:
        """Converts facial geometry metrics to a probability distribution."""
        # If model/vision already provided expression_signals, use them
        exp = getattr(face, "expression_signals", None)
        if exp and isinstance(exp, dict):
            return self._normalize_prob_dict(exp)

        features = getattr(face, "facial_features", None) or {}
        smile_ratio = features.get("smile_ratio", 0.0)
        eye_openness = features.get("eye_openness", 0.5)

        probs = {e: 0.05 for e in ALL_EMOTIONS}
        if smile_ratio > 0.4:
            probs["happy"] = min(0.9, 0.4 + smile_ratio * 0.5)
            probs["neutral"] = 0.15
        elif eye_openness > 0.75:
            probs["surprised"] = 0.60
            probs["neutral"] = 0.25
        elif eye_openness < 0.30:
            probs["bored"] = 0.45
            probs["sad"] = 0.35
            probs["neutral"] = 0.15
        else:
            probs["neutral"] = 0.70

        return self._normalize_prob_dict(probs)

    def _calculate_intensity(
        self,
        text: Optional[TextEmotionResponse],
        voice: Optional[VoiceEmotionResponse],
        face: Any,
        probs: Dict[str, float],
    ) -> float:
        """Computes emotional arousal/intensity based on multimodal indicators."""
        factors = []

        # Peak probability factor
        peak_p = max(probs.values()) if probs else 0.5
        factors.append(peak_p)

        # Text sentiment valence factor
        if text:
            factors.append(abs(text.sentiment_score))

        # Voice energy factor
        if voice:
            energy_map = {"low": 0.2, "medium": 0.5, "high": 0.85}
            factors.append(energy_map.get(voice.energy_level, 0.5))
            if voice.speaking_rate == "fast":
                factors.append(0.75)

        # Face smile / activity factor
        if face and getattr(face, "face_detected", False):
            features = getattr(face, "facial_features", None) or {}
            smile = features.get("smile_ratio", 0.0)
            if smile > 0.2:
                factors.append(smile)

        intensity = sum(factors) / max(1, len(factors))
        return max(0.05, min(1.0, intensity))

    def _calculate_divergence(
        self,
        active_modalities: List[str],
        modality_probs: Dict[str, Dict[str, float]],
    ) -> float:
        """Measures variance/disagreement across active modality probability distributions."""
        if len(active_modalities) <= 1:
            return 0.0

        # Mean Euclidean distance between all pairs of modalities
        distances = []
        n = len(active_modalities)
        for i in range(n):
            for j in range(i + 1, n):
                m1 = active_modalities[i]
                m2 = active_modalities[j]
                p1 = modality_probs[m1]
                p2 = modality_probs[m2]
                
                # Euclidean distance across categories
                dist = math.sqrt(sum((p1.get(e, 0.0) - p2.get(e, 0.0)) ** 2 for e in ALL_EMOTIONS))
                distances.append(dist)

        # Max theoretical Euclidean distance between two one-hot vectors is sqrt(2) ≈ 1.414
        avg_dist = sum(distances) / len(distances)
        return min(1.0, avg_dist / 1.414)

    def _calculate_normalized_entropy(self, probs: Dict[str, float]) -> float:
        """Calculates Shannon entropy normalized by log2(N)."""
        n = len(ALL_EMOTIONS)
        if n <= 1:
            return 0.0
        
        entropy = 0.0
        for p in probs.values():
            if p > 1e-6:
                entropy -= p * math.log2(p)
        
        max_entropy = math.log2(n)
        return min(1.0, max(0.0, entropy / max_entropy))

    def _smooth_probabilities(
        self,
        current: Dict[str, float],
        previous: Dict[str, float],
        alpha: float,
    ) -> Dict[str, float]:
        """Applies Exponential Moving Average (EMA) to probability distributions."""
        smoothed = {}
        for e in ALL_EMOTIONS:
            c = current.get(e, 0.0)
            p = previous.get(e, 0.0)
            smoothed[e] = alpha * c + (1.0 - alpha) * p
        return self._normalize_prob_dict(smoothed)

    def _normalize_prob_dict(self, probs: Dict[str, float]) -> Dict[str, float]:
        """Ensures all standard emotions exist and sum strictly to 1.0."""
        complete = {e: max(0.0, float(probs.get(e, 0.0))) for e in ALL_EMOTIONS}
        total = sum(complete.values())
        if total <= 0:
            return {e: 1.0 / len(ALL_EMOTIONS) for e in ALL_EMOTIONS}
        return {e: round(v / total, 4) for e, v in complete.items()}

    async def _persist_event(
        self,
        fused: MultimodalFusionResponse,
        request: MultimodalFusionRequest,
        db: AsyncSession,
    ) -> str:
        """Persists the fused EmotionEvent and EmotionSource records to the database."""
        event = EmotionEvent(
            session_id=request.session_id,
            dominant_emotion=fused.dominant_emotion,
            confidence=fused.confidence,
            intensity=fused.intensity,
            uncertainty=fused.uncertainty,
            probabilities=fused.probabilities,
            sources=fused.sources,
            modality_status=fused.modality_status,
        )
        db.add(event)
        await db.flush()

        # Add child sources
        if request.text_signal:
            src_text = EmotionSource(
                emotion_event_id=event.id,
                modality="text",
                raw_score=request.text_signal.sentiment_score,
                extracted_features={
                    "intent": request.text_signal.intent,
                    "confidence": request.text_signal.confidence,
                },
            )
            db.add(src_text)

        if request.voice_signal:
            src_voice = EmotionSource(
                emotion_event_id=event.id,
                modality="voice",
                raw_score=request.voice_signal.acoustic_features.get("pitch_hz", 0.0),
                extracted_features={
                    "energy_level": request.voice_signal.energy_level,
                    "speaking_rate": request.voice_signal.speaking_rate,
                    "confidence": request.voice_signal.confidence,
                },
            )
            db.add(src_voice)

        if request.face_signal and getattr(request.face_signal, "face_detected", False):
            src_face = EmotionSource(
                emotion_event_id=event.id,
                modality="face",
                raw_score=getattr(request.face_signal, "lighting_score", 1.0),
                extracted_features={
                    "status": getattr(request.face_signal, "status", "ok"),
                    "facial_features": getattr(request.face_signal, "facial_features", None),
                },
            )
            db.add(src_face)

        await db.commit()
        await db.refresh(event)
        return event.id


# Singleton instance
emotion_engine = MultimodalEmotionEngine()
