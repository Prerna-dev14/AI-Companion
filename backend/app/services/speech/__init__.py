from backend.app.services.speech.adapters import (
    BaseSTTAdapter,
    BaseTTSAdapter,
    OpenAISTTAdapter,
    FallbackSTTAdapter,
    OpenAITTSAdapter,
    GTTSAdapter,
    SyntheticWavTTSAdapter,
    get_stt_adapter,
    get_tts_adapter,
)

__all__ = [
    "BaseSTTAdapter",
    "BaseTTSAdapter",
    "OpenAISTTAdapter",
    "FallbackSTTAdapter",
    "OpenAITTSAdapter",
    "GTTSAdapter",
    "SyntheticWavTTSAdapter",
    "get_stt_adapter",
    "get_tts_adapter",
]
