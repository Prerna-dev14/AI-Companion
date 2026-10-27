import logging
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc, and_

from backend.app.models.entities import MemoryItem, Consent, UserSettings, EmotionEvent, User, Session

logger = logging.getLogger("ai_companion.memory")


class MemoryService:
    """Consent-Gated Long-Term Memory and History Service.
    
    Adheres strictly to the AI Companion Master Specification:
    Long-term facts and emotional histories are strictly consent-controlled,
    fully transparent, and user-deletable at any time.
    """

    # --- Consent Management ---

    async def get_consent_status(
        self,
        db: AsyncSession,
        user_id: str,
        scope: str,
    ) -> bool:
        """Checks if active consent has been granted for a specific scope."""
        res = await db.execute(
            select(Consent).where(
                and_(Consent.user_id == user_id, Consent.scope == scope)
            )
        )
        consent = res.scalar_one_or_none()
        return bool(consent and consent.granted)

    async def list_consents(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> List[Consent]:
        """Lists all consent scopes and statuses for a user."""
        res = await db.execute(
            select(Consent).where(Consent.user_id == user_id)
        )
        return list(res.scalars().all())

    async def update_consent(
        self,
        db: AsyncSession,
        user_id: str,
        scope: str,
        granted: bool,
        user_agent: Optional[str] = None,
    ) -> Consent:
        """Updates or registers a consent grant/revocation."""
        res = await db.execute(
            select(Consent).where(
                and_(Consent.user_id == user_id, Consent.scope == scope)
            )
        )
        consent = res.scalar_one_or_none()
        if consent:
            consent.granted = granted
            if user_agent:
                consent.user_agent = user_agent
        else:
            consent = Consent(
                user_id=user_id,
                scope=scope,
                granted=granted,
                user_agent=user_agent,
            )
            db.add(consent)

        # Sync user settings flags if applicable
        settings_res = await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
        user_setting = settings_res.scalar_one_or_none()
        if not user_setting:
            user_setting = UserSettings(user_id=user_id)
            db.add(user_setting)

        if scope == "long_term_memory":
            user_setting.allow_long_term_memory = granted
        elif scope == "emotion_storage":
            user_setting.allow_emotion_storage = granted
        elif scope == "camera":
            user_setting.camera_enabled = granted
        elif scope == "microphone":
            user_setting.voice_enabled = granted

        await db.commit()
        await db.refresh(consent)
        logger.info(f"User {user_id} consent for '{scope}' set to {granted}")
        return consent

    # --- Long-Term Memory Management ---

    async def create_memory(
        self,
        db: AsyncSession,
        user_id: str,
        content: str,
        category: str = "preference",
    ) -> MemoryItem:
        """Stores a persistent user fact or preference, strictly gating on consent."""
        has_consent = await self.get_consent_status(db, user_id, "long_term_memory")
        if not has_consent:
            raise PermissionError("Long-term memory storage requires explicit user consent.")

        memory = MemoryItem(
            user_id=user_id,
            content=content.strip(),
            category=category,
            is_active=True,
        )
        db.add(memory)
        await db.commit()
        await db.refresh(memory)
        logger.info(f"Created memory item {memory.id} for user {user_id}")
        return memory

    async def list_memories(
        self,
        db: AsyncSession,
        user_id: str,
        limit: int = 50,
    ) -> List[MemoryItem]:
        """Lists active memory items for review."""
        res = await db.execute(
            select(MemoryItem)
            .where(and_(MemoryItem.user_id == user_id, MemoryItem.is_active == True))
            .order_by(desc(MemoryItem.created_at))
            .limit(limit)
        )
        return list(res.scalars().all())

    async def delete_memory(
        self,
        db: AsyncSession,
        user_id: str,
        memory_id: str,
    ) -> bool:
        """Permanently deletes a specific memory item."""
        res = await db.execute(
            select(MemoryItem).where(
                and_(MemoryItem.id == memory_id, MemoryItem.user_id == user_id)
            )
        )
        memory = res.scalar_one_or_none()
        if not memory:
            return False

        await db.delete(memory)
        await db.commit()
        logger.info(f"Deleted memory item {memory_id} for user {user_id}")
        return True

    async def clear_all_memories(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> int:
        """Deletes all memory items for the user (Right to be Forgotten)."""
        res = await db.execute(
            delete(MemoryItem).where(MemoryItem.user_id == user_id)
        )
        await db.commit()
        count = res.rowcount
        logger.info(f"Cleared all ({count}) memory items for user {user_id}")
        return count

    async def get_active_memory_context(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> List[str]:
        """Fetches active memory items for prompt context if consent is active."""
        has_consent = await self.get_consent_status(db, user_id, "long_term_memory")
        if not has_consent:
            return []

        memories = await self.list_memories(db, user_id, limit=10)
        return [m.content for m in memories]

    # --- Emotion Event History ---

    async def get_emotion_history(
        self,
        db: AsyncSession,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> Tuple[int, List[EmotionEvent]]:
        """Retrieves past logged emotion events."""
        query = select(EmotionEvent)
        if session_id:
            query = query.where(EmotionEvent.session_id == session_id)
        elif user_id:
            query = query.join(Session).where(Session.user_id == user_id)

        query = query.order_by(desc(EmotionEvent.created_at)).limit(limit)
        res = await db.execute(query)
        items = list(res.scalars().all())
        return len(items), items

    async def clear_emotion_history(
        self,
        db: AsyncSession,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> int:
        """Clears logged emotion events."""
        if session_id:
            res = await db.execute(
                delete(EmotionEvent).where(EmotionEvent.session_id == session_id)
            )
        elif user_id:
            subq = select(Session.id).where(Session.user_id == user_id)
            res = await db.execute(
                delete(EmotionEvent).where(EmotionEvent.session_id.in_(subq))
            )
        else:
            res = await db.execute(delete(EmotionEvent))

        await db.commit()
        return res.rowcount


# Singleton instance
memory_service = MemoryService()
