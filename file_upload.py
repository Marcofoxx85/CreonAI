import os
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from models import Asset
from datetime import datetime
from typing import Literal
from uuid import uuid4

router = APIRouter()

# Directory for storing uploaded files
UPLOAD_DIR = os.path.join(os.getcwd(), "media")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = {
    "image": ["jpg", "jpeg", "png", "gif", "webp"],
    "video": ["mp4", "webm", "mov"],
    "audio": ["mp3", "wav", "ogg"],
    "pdf": ["pdf"]
}

# Dummy user simulation (replace with actual auth logic)
def get_current_user_id():
    return 1  # Replace this with token-based session logic

@router.post("/upload")
async def upload_asset(
    file: UploadFile = File(...),
    type: Literal["image", "video", "audio", "pdf", "text"] = Form(...),
    title: str = Form(...),
    db: Session = Depends(get_db)
):
    user_id = get_current_user_id()

    ext = file.filename.split(".")[-1].lower()
    if ext not in sum(ALLOWED_TYPES.values(), []):
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    if ext not in ALLOWED_TYPES[type]:
        raise HTTPException(status_code=400, detail=f"File extension does not match declared type '{type}'")

    unique_filename = f"{uuid4().hex}.{ext}"
    save_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(save_path, "wb") as f:
        f.write(await file.read())

    asset = Asset(
        user_id=user_id,
        type=type,
        title=title,
        filepath=f"/media/{unique_filename}",
        created_at=datetime.utcnow(),
        is_public=False
    )

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return JSONResponse({
        "id": asset.id,
        "title": asset.title,
        "type": asset.type,
        "filepath": asset.filepath
    })
