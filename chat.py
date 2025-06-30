# chat.py

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Literal
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os, asyncio, json

from backend.database import get_db
from backend.utils import check_user_credits, log_action
from backend.models import User


load_dotenv()
router = APIRouter()
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ───────────────────────────────────────────────
# Chat input payload schema
# ───────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    model: Literal["gpt-4o", "gemini", "image", "audio", "video"]
    persona: str = "You are a helpful assistant."
    temperature: float = 0.8


# ───────────────────────────────────────────────
# Stream generator for OpenAI (GPT-4o)
# ───────────────────────────────────────────────
async def stream_openai_response(prompt: str, persona: str, temp: float):
    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": persona},
            {"role": "user", "content": prompt},
        ],
        temperature=temp,
        stream=True,
    )

    async def event_gen():
        full = ""
        async for chunk in response:
            delta = chunk.choices[0].delta.content or ""
            full += delta
            yield f"data: {delta}\n\n"
        yield f"data: [END]\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")
@router.post("/chat")
async def chat_route(
    body: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(lambda: request.state.user if hasattr(request.state, "user") else None),
):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # ── CREDIT CHECK ─────────────────────────────
    try:
        credits_left = check_user_credits(db, user.id, required=1)
    except HTTPException:
        return JSONResponse(status_code=402, content={"error": "Out of credits"})

    log_action(db, user.id, f"chat_request:{body.model}", body.message)

    # ── GPT-4o Streaming ─────────────────────────
    if body.model == "gpt-4o":
        return await stream_openai_response(
            prompt=body.message,
            persona=body.persona,
            temp=body.temperature
        )

    # ── GEMINI (Text) ────────────────────────────
    elif body.model == "gemini":
        return JSONResponse(content={
            "response": f"(Gemini reply stub) You said: {body.message}"
        })

    # ── IMAGE GENERATION ─────────────────────────
    elif body.model == "image":
        return JSONResponse(content={
            "image_url": "/static/media/images/sample.png",
            "response": "(Image generation stub)"
        })

    # ── AUDIO GENERATION ─────────────────────────
    elif body.model == "audio":
        return JSONResponse(content={
            "audio_url": "/static/media/audio/sample.mp3",
            "response": "(Audio TTS stub)"
        })

    # ── VIDEO GENERATION ─────────────────────────
    elif body.model == "video":
        return JSONResponse(content={
            "video_url": "/static/media/videos/sample.mp4",
            "response": "(Video gen stub — Veo integration coming)"
        })

    else:
        raise HTTPException(status_code=400, detail="Unknown model")
# ───────────────────────────────────────────────
# Optional: Gemini API integration
# ───────────────────────────────────────────────
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    async def call_gemini(prompt: str):
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text

except Exception as e:
    print("⚠️ Gemini integration not available:", e)
    call_gemini = None


# Optional route for Gemini (non-streaming)
@router.post("/gemini")
async def gemini_route(
    body: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(lambda: None)
):
    if not call_gemini:
        raise HTTPException(status_code=503, detail="Gemini not configured")

    try:
        reply = await asyncio.to_thread(call_gemini, body.message)
        check_user_credits(db, user.id, 1)
        log_action(db, user.id, "gemini_prompt", body.message)
        return {"response": reply}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ───────────────────────────────────────────────
# Optional: Upload endpoint (future use)
# ───────────────────────────────────────────────
from fastapi import UploadFile, File

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # TODO: Add to /media + create Asset if needed
    return {"filename": file.filename, "status": "received"}
