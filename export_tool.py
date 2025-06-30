# backend/export_tool.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .models import User, ChatHistory, ImageGeneration  # adjust model names as needed
from .database import SessionLocal
from .auth import get_current_user  # your JWT logic

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/api/export/history")
async def export_user_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Replace model classes with actual names used in your DB
    chat_data = db.query(ChatHistory).filter(ChatHistory.user_id == current_user.id).all()
    image_data = db.query(ImageGeneration).filter(ImageGeneration.user_id == current_user.id).all()

    chat_dump = [dict(id=msg.id, content=msg.content, timestamp=msg.created_at.isoformat()) for msg in chat_data]
    image_dump = [dict(id=img.id, prompt=img.prompt, output_url=img.output_url) for img in image_data]

    return JSONResponse(content={
        "user_id": current_user.id,
        "email": current_user.email,
        "chat_history": chat_dump,
        "image_generations": image_dump
    })
