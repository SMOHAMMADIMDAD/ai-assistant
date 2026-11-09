import os
import io
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
from google import genai
from google.genai import types
from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    UploadFile,
    File,
    Form,
    status,
)
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from PIL import Image
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Import application services
from app.research_service import perform_deep_research, ResearchServiceError
from app import database
from app import models, security, crud, schemas, services

# ============================================================
# App & Configuration
# ============================================================
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("ai-backend")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError("❌ GOOGLE_API_KEY (or GEMINI_API_KEY) is not set.")

# ============================================================
# New Google GenAI Client & Multi-Model Priority List
# ============================================================
client = genai.Client(api_key=GOOGLE_API_KEY)

AVAILABLE_MODELS = [
    "gemini-3.8-turbo",
    "gemini-2.5-flash",

]
GEMINI_MODEL = AVAILABLE_MODELS[0]

# ============================================================
# Authentication
# ============================================================
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token"
)

# ============================================================
# Startup Smoke-Test & Database Lifespan
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Ensure Database Tables
    async with database.engine.begin() as conn:
        await conn.run_sync(
            models.Base.metadata.create_all
        )
    logger.info("✅ Database ready; tables ensured.")

    # 2. Automated Smoke Test for Gemini Connection
    logger.info("🧪 Running startup Gemini model smoke-test...")
    test_success = False
    for model_name in AVAILABLE_MODELS:
        try:
            test_response = await client.aio.models.generate_content(
                model=model_name,
                contents="Hello, reply with 'OK'.",
            )
            if test_response and test_response.text:
                logger.info("✨ Smoke-test passed successfully with model: %s", model_name)
                test_success = True
                break
        except Exception as e:
            logger.warning("⚠️ Smoke-test probe failed on model %s: %s", model_name, str(e))

    if not test_success:
        logger.error("❌ Warning: All startup model probes failed or experienced high traffic. Server is up, but API calls may require retry.")

    yield

# ============================================================
# FastAPI App
# ============================================================
app = FastAPI(
    title="Upgraded Gemini AI Backend",
    version="3.0.0",
    lifespan=lifespan,
)

# ============================================================
# CORS
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db():
    async with database.SessionLocal() as session:
        yield session

# ============================================================
# Authentication Helpers
# ============================================================
def verify_password(plain, hashed):
    return security.verify_password(plain, hashed)

def get_password_hash(password):
    return security.get_password_hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = (
        datetime.now(timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

CurrentUser = Depends(get_current_user)

# ============================================================
# Root Endpoint & Health Check
# ============================================================
@app.get("/")
def home():
    return {
        "message": "✅ AI Backend is running with Multi-Model Fallback & Testing enabled!",
        "version": app.version,
        "gemini_sdk": "google-genai",
        "priority_models": AVAILABLE_MODELS,
    }

# ============================================================
# Register & Authentication Endpoints
# ============================================================
@app.post("/register", status_code=201)
async def register_user(
    user: schemas.UserCreate,
    db: AsyncSession = Depends(get_db),
):
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match.",
        )
    db_user = await crud.get_user_by_identifier(db, user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email or phone number is already registered.",
        )
    hashed_password = get_password_hash(user.password)
    db_user = await crud.create_user(db, user, hashed_password)
    logger.info(f"👤 Registered user: {user.email}")
    return {
        "message": f"User '{user.name}' registered successfully."
    }

@app.post("/token")
async def login_for_access_token(
    form_data: schemas.TokenRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await crud.get_user_by_identifier(db, form_data.identifier)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect identifier or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    logger.info(f"🔐 Login success: {user.email}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@app.get("/me")
async def get_profile(
    current_user: models.User = CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    sessions_count = await crud.get_session_count_for_user(db, current_user.id)
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "phone_number": current_user.phone_number,
        "sessions_count": sessions_count,
        "custom_instruction": current_user.custom_instruction,
    }

@app.put("/me/instruction")
async def update_custom_instruction(
    request: schemas.CustomInstructionUpdate,
    current_user: models.User = CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    current_user.custom_instruction = request.instruction
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    logger.info(f"🧠 Updated custom instruction for {current_user.email}")
    return {
        "message": "✅ Custom instruction updated successfully."
    }

# ============================================================
# AI Web Search Tool Configuration
# ============================================================
web_searcher = services.WebSearcher()
web_search_function = types.FunctionDeclaration(
    name="web_search",
    description="Search the web for recent, current, or real-time information.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The exact topic or question to search for.",
            }
        },
        "required": ["query"],
    },
)
web_search_tool = types.Tool(
    function_declarations=[web_search_function]
)

# ============================================================
# Rate Limiting
# ============================================================
RATE_LIMIT_DURATION = 60
RATE_LIMIT_REQUESTS = 15
user_request_timestamps: Dict[str, list] = {}

async def rate_limit_chat(
    current_user: models.User = CurrentUser,
):
    user_id = str(current_user.id)
    current_time = time.time()
    if user_id not in user_request_timestamps:
        user_request_timestamps[user_id] = []

    user_request_timestamps[user_id] = [
        timestamp for timestamp in user_request_timestamps[user_id]
        if current_time - timestamp <= RATE_LIMIT_DURATION
    ]
    if len(user_request_timestamps[user_id]) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You have exceeded the API rate limit. Please try again later.",
        )
    user_request_timestamps[user_id].append(current_time)

# ============================================================
# Gemini Content Helpers
# ============================================================
def create_user_content(
    text: str,
    image_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
):
    parts = [types.Part.from_text(text=text)]
    if image_bytes:
        parts.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type or "image/jpeg",
            )
        )
    return types.Content(role="user", parts=parts)

def convert_database_history(messages: List[models.ChatMessage]):
    history = []
    for message in messages:
        role = (
            message.role.value
            if hasattr(message.role, "value")
            else str(message.role)
        )
        sdk_role = "user" if role == "user" else "model"
        history.append(
            types.Content(
                role=sdk_role,
                parts=[types.Part.from_text(text=message.content or "")],
            )
        )
    return history

# ============================================================
# Multi-Model Streaming Fallback Generator
# ============================================================
async def stream_gemini_response(
    history: List[models.ChatMessage],
    prompt: str,
    system_instruction: str,
    image_bytes: Optional[bytes] = None,
    image_mime_type: Optional[str] = None,
):
    contents = convert_database_history(history)
    current_user_content = create_user_content(
        text=prompt,
        image_bytes=image_bytes,
        mime_type=image_mime_type,
    )
    contents.append(current_user_content)

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=[web_search_tool],
    )

    success = False
    for model_name in AVAILABLE_MODELS:
        try:
            logger.info("🤖 Attempting stream with model: %s", model_name)
            response_stream = await client.aio.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=config,
            )
            async for chunk in response_stream:
                if chunk.text:
                    success = True
                    yield chunk.text
            if success:
                break
        except Exception as e:
            logger.warning("⚠️ Model %s failed: %s. Trying next available model...", model_name, str(e))
            continue

    if not success:
        yield "I'm sorry, all AI models are currently experiencing high traffic. Please try again in a moment."

# ============================================================
# Core Chat Endpoint (Streaming + Multi-Model Fallback)
# ============================================================
@app.post("/chat/")
async def chat_gemini(
    current_user: models.User = CurrentUser,
    prompt: str = Form(...),
    session_id: Optional[int] = Form(None),
    personality: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    is_deep_research: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    rate_limit_check: None = Depends(rate_limit_chat),
):
    if not prompt.strip() and not image:
        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty unless an image is provided.",
        )

    if is_deep_research:
        if image:
            raise HTTPException(
                status_code=400,
                detail="Deep research does not support image inputs.",
            )
        try:
            research_result = await perform_deep_research(prompt)
            title = "Research: " + " ".join(prompt.split()[:4])
            session = models.ChatSession(
                user_id=current_user.id,
                title=title,
                system_prompt="Deep Research Session",
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)

            db.add_all([
                models.ChatMessage(session_id=session.id, role=models.MessageRole.USER, content=prompt),
                models.ChatMessage(session_id=session.id, role=models.MessageRole.MODEL, content=research_result["report"])
            ])
            await db.commit()
            return {
                "response": research_result["report"],
                "session_id": session.id,
                "title": session.title,
                "sources": research_result["sources"],
            }
        except Exception as e:
            logger.error("Deep research error: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    image_bytes = None
    image_mime_type = None
    system_prompt_for_api = (
        "You are a helpful AI assistant. Answer directly and concisely. "
        "Only use the web_search tool if the user explicitly asks for recent news, live scores, or real-time current events. "
        f"User's custom instruction: {personality or current_user.custom_instruction or 'None'}"
    )

    if image:
        try:
            image_bytes = await image.read()
            image_mime_type = image.content_type or "image/jpeg"
            Image.open(io.BytesIO(image_bytes)).verify()
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file.",
            )

    # Database Session Phase
    try:
        if session_id:
            session = await crud.get_chat_session_with_history(
                db, session_id, current_user.id
            )
            if not session:
                raise HTTPException(status_code=404, detail="Session not found.")
            active_session_id = session.id
        else:
            title = " ".join(prompt.split()[:5]) or "New Chat"
            session = await crud.create_chat_session(
                db, current_user.id, title, system_prompt_for_api
            )
            active_session_id = session.id

        user_msg_text = prompt + (" [Image Attached]" if image else "")
        await crud.create_chat_message(
            db, active_session_id, models.MessageRole.USER, user_msg_text
        )

        result = await db.execute(
            select(models.ChatMessage)
            .where(models.ChatMessage.session_id == active_session_id)
            .order_by(models.ChatMessage.created_at.asc())
        )
        messages = list(result.scalars().all())
        history_messages = messages[:-1][-15:] if messages else []

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Database operation failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Database read operation failed.",
        )

    # Stream generator wrapper
    async def event_generator():
        full_response = ""
        try:
            async for chunk in stream_gemini_response(
                history=history_messages,
                prompt=prompt,
                system_instruction=system_prompt_for_api,
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
            ):
                full_response += chunk
                yield chunk
        finally:
            if full_response:
                async with database.SessionLocal() as write_db:
                    await crud.create_chat_message(
                        write_db,
                        active_session_id,
                        models.MessageRole.MODEL,
                        full_response,
                    )

    return StreamingResponse(event_generator(), media_type="text/plain")

# ============================================================
# History Endpoints
# ============================================================
@app.get("/history")
async def list_histories(
    current_user: models.User = CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    sessions = await crud.get_all_sessions_for_user(db, current_user.id)
    return {
        "sessions": [
            schemas.ChatSessionInfo.model_validate(session)
            for session in sessions
        ]
    }

@app.get("/history/{session_id}")
async def get_history(
    session_id: int,
    current_user: models.User = CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    session = await crud.get_chat_session_with_history(
        db, session_id, current_user.id
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return schemas.ChatSessionDetail(
        session_id=session.id,
        title=session.title,
        history=[
            schemas.ChatMessagePublic(
                role=message.role,
                content=message.content,
                created_at=message.created_at,
            )
            for message in session.messages
        ],
    )

@app.delete("/history/{session_id}")
async def delete_session(
    session_id: int,
    current_user: models.User = CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    session_to_delete = await crud.get_chat_session(
        db, session_id, current_user.id
    )
    if not session_to_delete:
        raise HTTPException(status_code=404, detail="Session not found.")
    title = session_to_delete.title
    await db.delete(session_to_delete)
    await db.commit()
    return {"message": f"✅ Session '{title}' deleted successfully."}

@app.patch("/history/{session_id}/rename")
async def rename_session(
    session_id: int,
    request: schemas.SessionRenameRequest,
    current_user: models.User = CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    session = await crud.get_chat_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    old_title = session.title
    session.title = request.title.strip()
    db.add(session)
    await db.commit()
    return {
        "message": "✅ Session renamed successfully.",
        "title": session.title,
    }