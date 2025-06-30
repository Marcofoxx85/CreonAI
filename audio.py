from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path

from backend.database import get_db
from backend.models import User, Asset
from backend.utils import check_user_credits, log_action
from backend.config import AUDIO_DIR

router = APIRouter()

# ───────────────────────────────────────────────
# Request Schema
# ───────────────────────────────────────────────
class AudioPrompt(BaseModel):
    prompt: str
    model: str = "openai-tts"
    voice: str = "nova"  # or alloy, shimmer, etc.

# ───────────────────────────────────────────────
# Generate audio (stub logic for now)
# ───────────────────────────────────────────────
@router.post("/audio")
async def generate_audio(
    body: AudioPrompt,
    db: Session = Depends(get_db),
    user: User = Depends(lambda: None)
):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        check_user_credits(db, user.id, required=2)
    except HTTPException:
        return JSONResponse(status_code=402, content={"error": "Not enough credits"})

    log_action(db, user.id, "generate_audio", body.prompt)

    # Simulate TTS output path
    fake_path = AUDIO_DIR / "demo.mp3"
    filename = f"tts_{datetime.utcnow().timestamp()}.mp3"
    out_path = AUDIO_DIR / filename

    try:
        Path(AUDIO_DIR).mkdir(parents=True, exist_ok=True)

        demo_source = AUDIO_DIR / "demo.mp3"
        with open(demo_source, "rb") as src, open(out_path, "wb") as dst:
            dst.write(src.read())

        asset = Asset(
            user_id=user.id,
            type="audio",
            title=body.prompt,
            filepath=str(out_path).replace("static", "/static"),
            created_at=datetime.utcnow()
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)

        return {
            "audio_url": asset.filepath,
            "title": body.prompt,
            "voice": body.voice,
            "asset_id": asset.id,
            "response": "Audio generated successfully"
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Audio generation failed: {str(e)}"})
