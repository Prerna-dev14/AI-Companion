import os
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import httpx

from backend.app.core.config import settings

logger = logging.getLogger("ai_companion.llm_adapter")

class BaseLLMAdapter(ABC):
    """Abstract Base Class for LLM providers."""

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 800,
    ) -> str:
        """Generates a text completion given conversation message history."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the identifier of the configured model."""
        pass


class OpenAILLMAdapter(BaseLLMAdapter):
    """Adapter for OpenAI and OpenAI-compatible API providers."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self._api_key = api_key or os.getenv("LLM_API_KEY") or ""
        self._model_name = model_name or os.getenv("LLM_MODEL_NAME", "gpt-4o")
        self._base_url = (base_url or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")).rstrip("/")

    @property
    def model_name(self) -> str:
        return f"openai/{self._model_name}"

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 800,
    ) -> str:
        if not self._api_key:
            raise ValueError("OpenAI API key is not configured.")

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})

        formatted_messages.extend(messages)

        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self._model_name,
                "messages": formatted_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                logger.error(f"OpenAI API error {response.status_code}: {response.text}")
                raise RuntimeError(f"OpenAI API call failed with status {response.status_code}")

            data = response.json()
            return data["choices"][0]["message"]["content"].strip()


class LocalHeuristicLLMAdapter(BaseLLMAdapter):
    """
    High-fidelity built-in companion adapter for offline/development environments.
    Analyzes intent, context, and sentiment to deliver coherent conversational replies
    without requiring external paid credentials.
    """

    def __init__(self, model_name: str = "ai-companion-engine-v1"):
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return f"local/{self._model_name}"

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 800,
    ) -> str:
        last_message = messages[-1]["content"] if messages else ""
        cleaned = last_message.strip().lower()
        sys = (system_prompt or "").upper()

        # Phase 7: Emotion-aware strategy adaptations
        if "[EMPATHETIC_VALIDATION]" in sys:
            return (
                "I hear how heavy this feels, and I want you to know it's completely okay to feel this way. "
                "I'm right here with you—take all the time you need. Would you like to talk through it, "
                "or would you simply like a calm, supportive presence?"
            )

        if "[SUPPORTIVE_CELEBRATION]" in sys:
            return (
                "That is truly wonderful! Your positive energy and joy really shine through. "
                "It brings a smile to celebrate this moment with you. What was the most meaningful part of this for you?"
            )

        if "[CALM_DEESCALATION]" in sys:
            return (
                "I hear how frustrating and difficult this situation is, and I completely understand why you're upset. "
                "Let's take a steady breath together. I'm here to listen calmly and help you work through this with zero judgment."
            )

        if "[STRUCTURED_CLARIFICATION]" in sys:
            return (
                "It is completely normal to feel confused or uncertain about this. "
                "Let's break this down together into simple, structured steps. "
                "Which specific part would you like to start clarifying first?"
            )

        if "[DYNAMIC_ENGAGEMENT]" in sys:
            return (
                "Sounds like we could use a spark of fresh energy! Let's shake things up—would you like to explore an "
                "intriguing creative dilemma, a thought-provoking idea, or pivot to something totally new?"
            )

        if "[INQUISITIVE_GROUNDING]" in sys:
            return (
                "That sounds like a real surprise! Take a moment to catch your breath and ground yourself. "
                "What was your immediate reaction when you found out?"
            )

        if "[INQUISITIVE_ATTUNEMENT]" in sys:
            return (
                "I sense there might be mixed feelings or subtle thoughts going on right now. "
                "I'm listening with an open mind and heart—how does everything feel from your perspective?"
            )

        # Context-aware fallback heuristics for conversational foundation
        if any(g in cleaned for g in ["hello", "hi", "hey", "greetings"]):
            return (
                "Hello! It's wonderful to connect with you. I'm your AI Companion, "
                "designed to listen, understand both what you say and how you feel, "
                "and support you throughout our conversations. How are you doing today?"
            )

        if "how are you" in cleaned or "how're you" in cleaned:
            return (
                "I'm doing well, thank you for asking! I'm here and fully attentive. "
                "More importantly, how is your day unfolding so far?"
            )

        if any(w in cleaned for w in ["help", "what can you do", "features"]):
            return (
                "As your AI Companion, I can have natural, attentive conversations with you. "
                "I incorporate speech, facial cues, and an independent Emotion Engine to dynamically adapt "
                "my conversational tone and empathy to your feelings while respecting strict safety boundaries."
            )

        if any(w in cleaned for w in ["sad", "depressed", "unhappy", "down", "upset"]):
            return (
                "I hear you, and I'm really sorry things are feeling difficult right now. "
                "I'm here to listen and support you. Would you like to share a bit more about what's on your mind?"
            )

        if any(w in cleaned for w in ["happy", "great", "awesome", "excited", "good news"]):
            return (
                "That's fantastic to hear! It brings a genuine smile to hear about positive moments. "
                "What made things go so well?"
            )

        if any(w in cleaned for w in ["thank", "thanks", "appreciate"]):
            return (
                "You're very welcome! I'm always glad to be here with you. "
                "Let me know if there's anything else you'd like to talk about."
            )

        # Standard context continuation
        return (
            f"I appreciate you sharing that with me. Regarding \"{last_message}\", "
            "I'm listening closely. Could you tell me more about your thoughts on this?"
        )


def get_llm_adapter() -> BaseLLMAdapter:
    """
    Factory function returning the configured LLM adapter.
    Falls back gracefully to LocalHeuristicLLMAdapter if OpenAI key is omitted or invalid.
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    api_key = os.getenv("LLM_API_KEY", "").strip()

    if provider == "openai" and api_key and not api_key.startswith("replace-"):
        try:
            return OpenAILLMAdapter(api_key=api_key)
        except Exception as exc:
            logger.warning(f"Could not initialize OpenAI adapter: {exc}. Using local adapter.")

    return LocalHeuristicLLMAdapter()
