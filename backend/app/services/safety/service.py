import re
import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("ai_companion.safety")


@dataclass
class SafetyAssessment:
    is_safe: bool
    category: str  # "none", "self_harm", "violence", "abuse"
    confidence: float
    matched_phrase: Optional[str] = None
    intervention_text: Optional[str] = None
    resources: Dict[str, str] = field(default_factory=dict)


class SafetyInterventionService:
    """Classifies high-risk safety triggers and generates compliant crisis interventions.
    
    Adheres strictly to the AI Companion Master Specification:
    - Intercepts self-harm and violence triggers before LLM generation.
    - Provides immediate, compassionate crisis resources.
    - Maintains strict non-clinical and non-diagnostic boundaries (never diagnoses, never prescribes).
    """

    # Self-Harm & Suicide Triggers
    SELF_HARM_PATTERNS = [
        r"\b(?:kill|killing)\s+(?:my\s*self|myself)\b",
        r"\b(?:want|wanna|wish)\s+(?:to\s+)?(?:die|be\s+dead|disappear|not\s+wake\s+up)\b",
        r"\b(?:commit|committing)\s+suicide\b",
        r"\b(?:end|ending)\s+(?:my\s+life|it\s+all)\b",
        r"\bbetter\s+off\s+dead\b",
        r"\b(?:hurt|hurting|cut|cutting)\s+(?:my\s*self|myself)\b",
        r"\b(?:hang|hanging)\s+myself\b",
        r"\b(?:overdose|swallow\s+all\s+(?:my\s+)?pills)\b",
        r"\b(?:suicidal|suicide\s+(?:note|plan|ideation))\b",
        r"\b(?:don't|do\s+not)\s+want\s+to\s+live\b",
        r"\bno\s+reason\s+to\s+live\b",
    ]

    # Extreme Violence Triggers
    VIOLENCE_PATTERNS = [
        r"\b(?:going\s+to|gonna|will)\s+(?:kill|murder|shoot)\s+(?:you|them|everyone|people)\b",
        r"\b(?:bomb|shoot\s+up)\s+(?:a\s+school|the\s+building|a\s+public\s+place)\b",
    ]

    CRISIS_RESOURCES = {
        "988_lifeline": "Call or text 988 (Available 24/7, free, confidential in US & Canada)",
        "crisis_text_line": "Text HOME to 741741 to connect with a crisis counselor 24/7",
        "trevor_project": "LGBTQ youth: Call 866-488-7386 or text START to 678-678",
        "veterans_crisis_line": "Dial 988, then press 1, or text 838255",
        "international": "International directory: https://findahelpline.com or https://www.befrienders.org",
        "emergency": "If in immediate physical danger, please contact local emergency services (911) or your nearest hospital.",
    }

    SELF_HARM_INTERVENTION_TEXT = (
        "It sounds like you are carrying a lot of pain and distress right now, and your life and safety matter deeply. "
        "Please know that you do not have to carry this alone, and there is immediate, compassionate support available right now:\n\n"
        "• **988 Suicide & Crisis Lifeline**: Call or text **988** (Available 24/7, free, confidential, English & Spanish)\n"
        "• **Crisis Text Line**: Text **HOME** to **741741** (24/7 crisis support via SMS)\n"
        "• **The Trevor Project** (LGBTQ youth): Call **866-488-7386** or text **START to 678-678**\n"
        "• **Veterans Crisis Line**: Dial **988, press 1**, or text **838255**\n"
        "• **International Support**: Visit **[findahelpline.com](https://findahelpline.com)** or **[befrienders.org](https://www.befrienders.org)**\n\n"
        "If you are in immediate danger of hurting yourself, please reach out to emergency services (like 911) or go to the nearest emergency room. "
        "I am here to support you, but reaching out to one of these trained crisis specialists right now can connect you with the real-time help you deserve."
    )

    VIOLENCE_INTERVENTION_TEXT = (
        "I cannot assist with statements involving violence or harm against others. "
        "If you are feeling overwhelmed, angry, or in crisis, please consider speaking with a crisis specialist or professional counselor who can support you through this safely:\n\n"
        "• **Crisis Text Line**: Text **HOME** to **741741**\n"
        "• **988 Suicide & Crisis Lifeline**: Call or text **988** (24/7 free support)\n"
        "• **Immediate Emergency**: Please contact your local emergency services."
    )

    def assess_message(self, text: str) -> SafetyAssessment:
        """Evaluates text for high-risk safety triggers.
        
        Returns:
            SafetyAssessment indicating if message is safe or requires crisis intervention.
        """
        if not text or not text.strip():
            return SafetyAssessment(is_safe=True, category="none", confidence=1.0)

        normalized = text.lower().strip()

        # 1. Check for self-harm / crisis patterns
        for pattern in self.SELF_HARM_PATTERNS:
            match = re.search(pattern, normalized, re.IGNORECASE)
            if match:
                matched_phrase = match.group(0)
                logger.warning(f"High-risk self-harm trigger detected: '{matched_phrase}'")
                return SafetyAssessment(
                    is_safe=False,
                    category="self_harm",
                    confidence=0.98,
                    matched_phrase=matched_phrase,
                    intervention_text=self.SELF_HARM_INTERVENTION_TEXT,
                    resources=self.CRISIS_RESOURCES,
                )

        # 2. Check for violence patterns
        for pattern in self.VIOLENCE_PATTERNS:
            match = re.search(pattern, normalized, re.IGNORECASE)
            if match:
                matched_phrase = match.group(0)
                logger.warning(f"Violence trigger detected: '{matched_phrase}'")
                return SafetyAssessment(
                    is_safe=False,
                    category="violence",
                    confidence=0.95,
                    matched_phrase=matched_phrase,
                    intervention_text=self.VIOLENCE_INTERVENTION_TEXT,
                    resources=self.CRISIS_RESOURCES,
                )

        return SafetyAssessment(
            is_safe=True,
            category="none",
            confidence=1.0,
            matched_phrase=None,
            intervention_text=None,
            resources={},
        )


safety_service = SafetyInterventionService()
