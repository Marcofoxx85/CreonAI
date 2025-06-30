from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path

from backend.database import get_db
from backend.models import User, Asset
from backend.utils import check_user_credits, log_action
from backend.config import VIDEO_DIR

router = APIRouter()

# ───────────────────────────────────────────────
# Request Schema
# ───────────────────────────────────────────────
class VideoPrompt(BaseModel):
    prompt: str
    model: str = "veo-1"  # placeholder for model selector
    duration: int = 5     # seconds

# ───────────────────────────────────────────────
# Route: Generate video from text prompt
# ───────────────────────────────────────────────
@router.post("/video")
async def generate_video(
    body: VideoPrompt,
    db: Session = Depends(get_db),
    user: User = Depends(lambda: None)
):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Credit check (e.g. 3 credits per video)
    try:
        check_user_credits(db, user.id, required=3)
    except HTTPException:
        return JSONResponse(status_code=402, content={"error": "Not enough credits"})

    log_action(db, user.id, "generate_video", body.prompt)

    # ─── Stubbed Response ─────────────────────────────
    # Simulate a generation delay + return a placeholder file
    fake_url = "/static/media/videos/demo.mp4"
    return {
        "video_url": fake_url,
        "response": f"(stubbed) Generated {body.duration}s video with prompt: {body.prompt}"
    }

    # ─── Save stub video to disk (for now) ────────
    try:
        Path(VIDEO_DIR).mkdir(parents=True, exist_ok=True)

        original_demo = "static/media/videos/demo.mp4"
        timestamp = int(datetime.utcnow().timestamp())
        filename = f"veo_{timestamp}.mp4"
        saved_path = VIDEO_DIR / filename

        with open(original_demo, "rb") as src, open(saved_path, "wb") as dst:
            dst.write(src.read())

        asset = Asset(
            user_id=user.id,
            type="video",
            title=body.prompt,
            filepath=str(saved_path).replace("static", "/static"),
            created_at=datetime.utcnow()
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)

        return {
            "video_url": asset.filepath,
            "title": body.prompt,
            "asset_id": asset.id,
            "response": "Video generated and saved"
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Video generation failed: {str(e)}"})
