import logging
from typing import List, Optional, Tuple, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.models.entities import User, Session, Message
from backend.app.services.rlpi.strategy import RLPIEngine
from backend.app.schemas.chat import ChatResponse, MessageResponse

logger = logging.getLogger("ai_companion.conversation")

class ConversationManager:
    def __init__(self, rlpi_engine: Optional[RLPIEngine] = None):
        self.rlpi_engine = rlpi_engine or RLPIEngine()

    async def get_or_create_default_user(self, db: AsyncSession, user_id: Optional[str] = None) -> User:
        """Retrieves user by ID or creates a default user if not present."""
        if user_id:
            res = await db.execute(select(User).where(User.id == user_id))
            user = res.scalar_one_or_none()
            if user:
                return user

        # Look for default user
        res = await db.execute(select(User).where(User.username == "default_user"))
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                username="default_user",
                email="user@example.com",
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"Created default user: {user.id}")
        return user

    async def get_or_create_session(
        self,
        db: AsyncSession,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Session:
        """Gets active session or creates a new one."""
        user = await self.get_or_create_default_user(db, user_id)

        if session_id:
            res = await db.execute(select(Session).where(Session.id == session_id))
            session = res.scalar_one_or_none()
            if session:
                return session

        # Create new session
        new_session = Session(
            user_id=user.id,
            title=title or f"Conversation {datetime.now(timezone.utc).strftime('%b %d, %H:%M')}",
            is_active=True,
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        logger.info(f"Created new conversation session: {new_session.id}")
        return new_session

    async def process_chat(
        self,
        db: AsyncSession,
        message_text: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        emotional_state: Optional[Any] = None,
    ) -> ChatResponse:
        """
        Processes a user chat message:
        1. Ensures session exists
        2. Saves user message
        3. Retrieves conversation context
        4. Queries RLPI engine with emotion-aware policy adaptation
        5. Saves assistant message with strategy metadata
        6. Returns structured ChatResponse
        """
        session = await self.get_or_create_session(db, session_id=session_id, user_id=user_id)

        # 1. Save user message to database
        user_msg = Message(
            session_id=session.id,
            role="user",
            content=message_text,
        )
        db.add(user_msg)
        await db.commit()
        await db.refresh(user_msg)

        # 2. Retrieve recent message history for context
        res = await db.execute(
            select(Message)
            .where(Message.session_id == session.id)
            .order_by(Message.created_at.asc())
        )
        all_messages = res.scalars().all()
        history = [{"role": m.role, "content": m.content} for m in all_messages]

        # 3. Generate response via RLPI engine (Phase 7: Emotion-aware)
        rlpi_result = await self.rlpi_engine.generate_reply(
            user_message=message_text,
            conversation_history=history,
            emotional_state=emotional_state,
        )

        # 4. Save assistant response
        assistant_msg = Message(
            session_id=session.id,
            role="assistant",
            content=rlpi_result["content"],
            metadata_payload={
                "response_strategy": rlpi_result["response_strategy"],
                "inferred_emotion": rlpi_result.get("inferred_emotion"),
                "model_name": rlpi_result["model_name"],
            },
        )
        db.add(assistant_msg)
        await db.commit()
        await db.refresh(assistant_msg)

        return ChatResponse(
            session_id=session.id,
            message=MessageResponse.model_validate(assistant_msg),
            response_strategy=rlpi_result["response_strategy"],
            model_name=rlpi_result["model_name"],
            created_at=assistant_msg.created_at,
        )

    async def get_sessions(self, db: AsyncSession, user_id: Optional[str] = None) -> List[Session]:
        """Lists active sessions."""
        user = await self.get_or_create_default_user(db, user_id)
        res = await db.execute(
            select(Session)
            .where(Session.user_id == user.id)
            .order_by(desc(Session.updated_at))
        )
        return list(res.scalars().all())

    async def get_session_messages(self, db: AsyncSession, session_id: str) -> List[Message]:
        """Fetches all messages for a session."""
        res = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
        )
        return list(res.scalars().all())
