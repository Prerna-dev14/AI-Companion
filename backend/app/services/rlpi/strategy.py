import logging
from typing import List, Dict, Optional, Any, Tuple
from backend.app.services.rlpi.llm_adapter import BaseLLMAdapter, get_llm_adapter

logger = logging.getLogger("ai_companion.rlpi")


class RLPIEngine:
    """
    Reinforcement Learning / Policy Inference Engine (Phase 7: Emotion-Aware).
    
    Coordinates conversational policy, system prompts, and LLM generation.
    Adapts conversational policy dynamically based on the normalized EmotionalState
    output by the independent Emotion Engine, while maintaining strict safety boundaries
    against clinical psychological diagnosis.
    """

    def __init__(self, llm_adapter: Optional[BaseLLMAdapter] = None):
        self.llm_adapter = llm_adapter or get_llm_adapter()

    def determine_strategy(self, emotional_state: Optional[Any]) -> Tuple[str, str]:
        """
        Maps normalized EmotionalState into a defined conversational policy strategy
        and prompting instructions.
        """
        if not emotional_state:
            return (
                "balanced_conversational",
                "Maintain a balanced, warm, attentive, and thoughtful conversational tone."
            )

        # Extract attributes whether Pydantic model or dict
        dominant = getattr(emotional_state, "dominant_emotion", None)
        if dominant is None and isinstance(emotional_state, dict):
            dominant = emotional_state.get("dominant_emotion", "neutral")
        dominant = (dominant or "neutral").lower()

        confidence = getattr(emotional_state, "confidence", 0.5)
        if isinstance(emotional_state, dict):
            confidence = emotional_state.get("confidence", 0.5)

        intensity = getattr(emotional_state, "intensity", 0.5)
        if isinstance(emotional_state, dict):
            intensity = emotional_state.get("intensity", 0.5)

        uncertainty = getattr(emotional_state, "uncertainty", 0.0)
        if isinstance(emotional_state, dict):
            uncertainty = emotional_state.get("uncertainty", 0.0)

        # If uncertainty is elevated or confidence is very low, adopt inquisitive attunement
        if uncertainty >= 0.45 or confidence < 0.25:
            return (
                "inquisitive_attunement",
                "The user's emotional state has high uncertainty or subtle mixed signals. "
                "Keep your tone open-ended, gentle, and inquisitive rather than presuming their exact feelings. "
                "Invite them to share more if they wish."
            )

        # Map by dominant emotion
        if dominant == "happy":
            return (
                "supportive_celebration",
                f"The user is experiencing positive, joyful energy (intensity: {intensity:.2f}). "
                "Share in their delight, offer warm validation, and encourage their positive momentum with an uplifting tone."
            )
        elif dominant == "sad":
            return (
                "empathetic_validation",
                f"The user is feeling sad, down, or vulnerable (intensity: {intensity:.2f}). "
                "Adopt a gentle, patient, and deeply compassionate tone. Validate their feelings without offering toxic positivity or quick fixes. "
                "Be present and supportive without assuming a clinical role."
            )
        elif dominant == "angry":
            return (
                "calm_deescalation",
                f"The user is experiencing anger or frustration (intensity: {intensity:.2f}). "
                "Remain calm, non-defensive, and grounded. Acknowledge their frustration respectfully and help them feel heard."
            )
        elif dominant == "confused":
            return (
                "structured_clarification",
                f"The user is experiencing confusion or uncertainty (intensity: {intensity:.2f}). "
                "Be patient and clear. Break complex ideas down into structured, digestible points and invite clarifying questions."
            )
        elif dominant == "bored":
            return (
                "dynamic_engagement",
                f"The user appears disengaged or bored (intensity: {intensity:.2f}). "
                "Keep your response concise, energetic, and propose an engaging question or intriguing thought to spark curiosity."
            )
        elif dominant == "surprised":
            return (
                "inquisitive_grounding",
                f"The user is feeling surprised or startled (intensity: {intensity:.2f}). "
                "Acknowledge the unexpected situation with a grounding, calm presence and invite them to unpack the moment."
            )
        else:
            return (
                "balanced_conversational",
                "Maintain a balanced, warm, attentive, and thoughtful conversational tone."
            )

    def build_system_prompt(
        self,
        strategy: str,
        strategy_instruction: str,
        language: str = "en",
        memories: Optional[List[str]] = None,
    ) -> str:
        """
        Builds the server-side system instructions injecting the active emotion strategy,
        active consent-gated memories, and mandatory non-diagnostic guardrails.
        """
        mem_section = ""
        if memories and len(memories) > 0:
            formatted_mems = "\n".join(f"- {m}" for m in memories)
            mem_section = f"\nUSER REMEMBERED PREFERENCES (CONSENT-GRANTED):\n{formatted_mems}\n"

        return (
            "You are AI Companion, an empathetic, attentive, and thoughtful personal companion.\n\n"
            "MANDATORY SAFETY AND BOUNDARY GUIDELINE:\n"
            "- You are an AI companion, NOT a physician, psychologist, or licensed therapist.\n"
            "- NEVER diagnose mental health conditions, clinical depression, or psychological disorders.\n"
            "- NEVER declare user emotions as clinical facts; use them strictly as an internal guide for conversational tone.\n\n"
            f"ACTIVE CONVERSATIONAL STRATEGY: [{strategy.upper()}]\n"
            f"STRATEGY GUIDELINE: {strategy_instruction}\n"
            f"{mem_section}\n"
            "GENERAL GUIDELINES:\n"
            "- Speak naturally, warmly, and in an engaging manner.\n"
            "- Listen closely to context and ask thoughtful questions when appropriate.\n"
            "- Keep your responses balanced, conversational, and respectful.\n"
            f"- Respond in {language} unless the user explicitly requests another language."
        )

    async def generate_reply(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        language: str = "en",
        emotional_state: Optional[Any] = None,
        memories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates context, selects emotion-aware response strategy, and queries the LLM adapter.
        """
        # Phase 7: Dynamic strategy mapping from independent Emotion Engine state
        strategy_name, strategy_instruction = self.determine_strategy(emotional_state)
        system_prompt = self.build_system_prompt(
            strategy=strategy_name,
            strategy_instruction=strategy_instruction,
            language=language,
            memories=memories,
        )

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
            logger.error(f"Error during LLM response generation: {exc}. Using heuristic fallback.")
            try:
                from backend.app.services.rlpi.llm_adapter import LocalHeuristicLLMAdapter
                fallback_adapter = LocalHeuristicLLMAdapter()
                reply_text = await fallback_adapter.generate_response(
                    messages=context_messages,
                    system_prompt=system_prompt,
                )
            except Exception:
                reply_text = (
                    "I am right here with you and listening. Could you tell me a little more about how you're feeling?"
                )

        inferred_emotion = None
        if emotional_state:
            inferred_emotion = getattr(emotional_state, "dominant_emotion", None)
            if inferred_emotion is None and isinstance(emotional_state, dict):
                inferred_emotion = emotional_state.get("dominant_emotion")

        return {
            "content": reply_text,
            "response_strategy": strategy_name,
            "inferred_emotion": inferred_emotion,
            "model_name": self.llm_adapter.model_name,
        }
