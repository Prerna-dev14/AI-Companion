import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.entities import User, Session, Message, UserSettings

@pytest.mark.asyncio
async def test_user_and_session_creation(db_session: AsyncSession):
    # Create user
    user = User(username="test_companion_user", email="test@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.is_active is True

    # Create settings and session
    settings = UserSettings(user_id=user.id, preferred_language="en", voice_enabled=True)
    chat_session = Session(user_id=user.id, title="Initial Chat Session")
    db_session.add_all([settings, chat_session])
    await db_session.commit()
    await db_session.refresh(chat_session)

    # Create message
    message = Message(
        session_id=chat_session.id,
        role="user",
        content="Hello AI Companion!"
    )
    db_session.add(message)
    await db_session.commit()

    # Query back
    res = await db_session.execute(select(Message).where(Message.session_id == chat_session.id))
    messages = res.scalars().all()
    assert len(messages) == 1
    assert messages[0].content == "Hello AI Companion!"
