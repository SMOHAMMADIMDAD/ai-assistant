# app/crud.py
# Contains all the functions that interact directly with the database.

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func
from sqlalchemy.orm import selectinload

# Correct imports
from . import models, schemas
# FIX: The create_user function now accepts the hashed password directly
# from . import security

# User CRUD
async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(models.User).where(models.User.email == email))
    return result.scalar_one_or_none()

async def get_user_by_identifier(db: AsyncSession, identifier: str):
    result = await db.execute(
        select(models.User).where(
            or_(models.User.email == identifier, models.User.phone_number == identifier)
        )
    )
    return result.scalar_one_or_none()

# FIX: The hashed password is now passed in as a parameter
async def create_user(db: AsyncSession, user: schemas.UserCreate, hashed_password: str):
    db_user = models.User(
        name=user.name,
        email=user.email,
        phone_number=user.phone_number,
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_session_count_for_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(func.count(models.ChatSession.id)).where(models.ChatSession.user_id == user_id))
    return result.scalar_one()

# Chat CRUD
async def get_chat_session(db: AsyncSession, session_id: int, user_id: int):
    result = await db.execute(
        select(models.ChatSession)
        .where(models.ChatSession.id == session_id, models.ChatSession.user_id == user_id)
    )
    return result.scalar_one_or_none()

async def get_chat_session_with_history(db: AsyncSession, session_id: int, user_id: int):
    result = await db.execute(
        select(models.ChatSession)
        .options(selectinload(models.ChatSession.messages))
        .where(models.ChatSession.id == session_id, models.ChatSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if session:
        # Manually sort messages by creation time
        session.messages.sort(key=lambda msg: msg.created_at)
    return session

async def create_chat_session(db: AsyncSession, user_id: int, title: str, system_prompt: str):
    session = models.ChatSession(user_id=user_id, title=title, system_prompt=system_prompt)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

async def create_chat_message(db: AsyncSession, session_id: int, role: models.MessageRole, content: str):
    message = models.ChatMessage(session_id=session_id, role=role, content=content)
    db.add(message)
    await db.commit()
    return message

async def get_all_sessions_for_user(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(models.ChatSession)
        .where(models.ChatSession.user_id == user_id)
        .order_by(models.ChatSession.created_at.desc())
    )
    return result.scalars().all()

# FIX: Removed all API endpoints from this file
# async def list_histories... (removed)
# async def get_history... (removed)
# async def delete_session... (removed)
