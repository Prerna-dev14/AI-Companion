import logging
from typing import List, Dict, Optional, Any
from backend.app.services.rlpi.llm_adapter import BaseLLMAdapter, get_llm_adapter

logger = logging.getLogger("ai_companion.rlpi")

class RLPIEngine:
    """
    Reinforcement Learning / Policy Inference Engine.
    Coordinates conversational policy, system prompts, and LLM generation.
    In Phase 2: Establishes base response policy and context handling.
    In Phase 7: Will inject fused EmotionalState and emotion-adaptive policies.
    """

    def __init__(self, llm_adapter: Optional[BaseLLMAdapter] = None):
        self.llm_adapter = llm_adapter or get_llm_adapter()

    def build_system_prompt(self, language: str = "en") -> str:
        """
        Builds the server-side system instructions.
        Secrets and internal guidelines remain strictly server-side.
        """
        return (
            "You are AI Companion, an empathetic, attentive, and thoughtful personal companion. "
            "Your goal is to converse naturally, attentively, and helpfully with the user. "
            "Guidelines:\n"
            "- Speak naturally, warmly, and in an engaging manner.\n"
            "- Listen closely to context and ask thoughtful questions when appropriate.\n"
            "- Never claim to be a medical or psychological professional, and never provide clinical diagnoses.\n"
            "- Keep your responses balanced, conversational, and respectful.\n"
            f"- Respond in {language} unless the user explicitly requests another language."
        )

    async def generate_reply(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        language: str = "en",
        emotional_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates context, selects response strategy, and queries the LLM adapter.
        """
        # Phase 2 baseline strategy
        strategy_name = "neutral_standard"
        system_prompt = self.build_system_prompt(language=language)

        # Build message history window (sliding context)
        context_messages = []
        for msg in conversation_history[-10:]:
            context_messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })

        # Append current user message if not already included
        if not context_messages or context_messages[-1]["content"] != user_message:
            context_messages.append({"role": "user", "content": user_message})

        try:
            reply_text = await self.llm_adapter.generate_response(
                messages=context_messages,
                system_prompt=system_prompt,
            )
        except Exception as exc:
            logger.error(f"Error during LLM response generation: {exc}")
            reply_text = (
                "I am here and listening, though I experienced a brief connection hiccup. "
                "Could you please repeat that?"
            )

        return {
            "content": reply_text,
            "response_strategy": strategy_name,
            "model_name": self.llm_adapter.model_name,
        }
