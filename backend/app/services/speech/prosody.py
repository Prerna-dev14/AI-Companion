import io
import wave
import math
import numpy as np
import logging
from typing import Dict, Any, Tuple

from backend.app.schemas.emotion import VoiceEmotionResponse

logger = logging.getLogger("ai_companion.prosody")

class VoiceProsodyService:
    """
    Extracts acoustic and prosodic features from in-memory voice audio.
    Computes pitch, energy, pacing, and prosody-driven emotion likelihoods.
    Enforces strict zero raw audio retention.
    """

    def analyze_audio(self, audio_bytes: bytes, filename: str = "voice.wav") -> VoiceEmotionResponse:
        if not audio_bytes or len(audio_bytes) == 0:
            raise ValueError("Empty audio payload received.")

        samples, sample_rate = self._read_audio_samples(audio_bytes)

        try:
            # 1. Acoustic Metrics Computation
            rms_energy = float(np.sqrt(np.mean(samples**2))) if len(samples) > 0 else 0.0
            peak_energy = float(np.max(np.abs(samples))) if len(samples) > 0 else 0.0

            pitch_hz, pitch_variance = self._estimate_pitch(samples, sample_rate)

            # Energy classification
            if rms_energy > 0.15:
                energy_level = "high"
            elif rms_energy < 0.03:
                energy_level = "low"
            else:
                energy_level = "medium"

            # Speaking pacing estimation
            zero_crossings = int(np.sum(np.diff(np.sign(samples)) != 0)) if len(samples) > 1 else 0
            zcr_rate = zero_crossings / max(1.0, len(samples) / float(sample_rate))
            if zcr_rate > 3000:
                speaking_rate = "fast"
            elif zcr_rate < 800:
                speaking_rate = "slow"
            else:
                speaking_rate = "normal"

            acoustic_features = {
                "rms_energy": round(rms_energy, 4),
                "peak_energy": round(peak_energy, 4),
                "pitch_hz": round(pitch_hz, 1),
                "pitch_variance": round(pitch_variance, 2),
                "zero_crossing_rate": round(zcr_rate, 1),
            }

            # 2. Emotion Category Probabilities Derived from Prosody
            probabilities, confidence = self._derive_prosodic_probabilities(
                rms_energy, pitch_hz, pitch_variance, speaking_rate, energy_level
            )

            return VoiceEmotionResponse(
                modality="voice",
                acoustic_features=acoustic_features,
                probabilities=probabilities,
                confidence=confidence,
                speaking_rate=speaking_rate,
                energy_level=energy_level,
            )
        finally:
            del samples

    def _read_audio_samples(self, audio_bytes: bytes) -> Tuple[np.ndarray, int]:
        """Reads audio bytes in-memory into a normalized float32 numpy array."""
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()
                raw_frames = wf.readframes(n_frames)
                sampwidth = wf.getsampwidth()

                if sampwidth == 2:
                    data = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0
                elif sampwidth == 1:
                    data = (np.frombuffer(raw_frames, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
                else:
                    data = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0

                if wf.getnchannels() > 1:
                    data = data.reshape(-1, wf.getnchannels()).mean(axis=1)

                return data, sample_rate
        except Exception:
            # Fallback raw byte interpretation (assuming 16kHz 16-bit mono)
            count = len(audio_bytes) // 2
            if count > 0:
                raw_ints = np.frombuffer(audio_bytes[: count * 2], dtype=np.int16)
                return raw_ints.astype(np.float32) / 32768.0, 16000
            return np.zeros(1600, dtype=np.float32), 16000

    def _estimate_pitch(self, samples: np.ndarray, sample_rate: int) -> Tuple[float, float]:
        """Estimates fundamental frequency (F0) using autocorrelation."""
        if len(samples) < 512:
            return 140.0, 10.0

        # Subsample frame center
        center_idx = len(samples) // 2
        chunk = samples[max(0, center_idx - 1024) : min(len(samples), center_idx + 1024)]
        if len(chunk) < 512 or np.all(chunk == 0):
            return 140.0, 5.0

        corr = np.correlate(chunk, chunk, mode="full")
        corr = corr[len(corr) // 2 :]

        # Look for pitch peak between 70Hz and 400Hz
        min_lag = int(sample_rate / 400.0)
        max_lag = int(sample_rate / 70.0)

        if max_lag >= len(corr):
            max_lag = len(corr) - 1

        if min_lag >= max_lag:
            return 140.0, 10.0

        peak_lag = min_lag + int(np.argmax(corr[min_lag:max_lag]))
        if peak_lag > 0 and corr[peak_lag] > 0.2 * corr[0]:
            f0 = float(sample_rate / peak_lag)
            variance = float(np.std(chunk) * 100.0)
            return round(f0, 1), round(variance, 2)

        return 140.0, 8.0

    def _derive_prosodic_probabilities(
        self,
        rms: float,
        pitch: float,
        variance: float,
        rate: str,
        energy: str,
    ) -> Tuple[Dict[str, float], float]:
        w_happy = 0.1
        w_sad = 0.1
        w_angry = 0.05
        w_bored = 0.1
        w_neutral = 0.65

        if energy == "high" and pitch > 180.0:
            w_happy += 0.5
            w_neutral -= 0.3
        elif energy == "high" and pitch < 160.0 and variance > 15.0:
            w_angry += 0.4
            w_neutral -= 0.2
        elif energy == "low" and pitch < 120.0 and rate == "slow":
            w_sad += 0.45
            w_bored += 0.25
            w_neutral -= 0.35
        elif rate == "slow" and variance < 5.0:
            w_bored += 0.4
            w_neutral -= 0.2

        weights = [max(0.01, w) for w in [w_happy, w_sad, w_angry, w_bored, w_neutral]]
        total = sum(weights)
        probs = {
            "happy": round(weights[0] / total, 3),
            "sad": round(weights[1] / total, 3),
            "angry": round(weights[2] / total, 3),
            "bored": round(weights[3] / total, 3),
            "neutral": round(weights[4] / total, 3),
        }

        confidence = 0.82 if energy != "medium" else 0.70
        return probs, confidence
