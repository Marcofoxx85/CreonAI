# image.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from openai import AsyncOpenAI
import os, base64, requests

from backend.database import get_db
from backend.models import User, Asset
from backend.utils import check_user_credits, log_action
from backend.config import OPENAI_API_KEY, IMAGE_DIR
from pathlib import Path

router = APIRouter()
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ───────────────────────────────────────────────
# Request Schema
# ───────────────────────────────────────────────
class ImagePrompt(BaseModel):
    prompt: str
    size: str = "1024x1024"
    n: int = 1  # number of images

# ───────────────────────────────────────────────
# Route: Generate image from prompt
# ───────────────────────────────────────────────
@router.post("/image")
async def generate_image(
    body: ImagePrompt,
    db: Session = Depends(get_db),
    user: User = Depends(lambda: None)
):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Check credits
    try:
        check_user_credits(db, user.id, required=1)
    except HTTPException:
        return JSONResponse(status_code=402, content={"error": "Out of credits"})

    log_action(db, user.id, "generate_image", body.prompt)

    # Create image
    try:
        dalle = await openai_client.images.generate(
            model="dall-e-3",
            prompt=body.prompt,
            size=body.size,
            n=body.n,
        )
        image_url = dalle.data[0].url
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    # Download + Save
    try:
        response = requests.get(image_url)
        if response.status_code != 200:
            raise Exception("Failed to fetch image from OpenAI")

        # Ensure save folder exists
        Path(IMAGE_DIR).mkdir(parents=True, exist_ok=True)

        filename = f"dalle_{datetime.utcnow().timestamp()}.png"
        local_path = IMAGE_DIR / filename

        with open(local_path, "wb") as f:
            f.write(response.content)

        # Save as Asset
       
        asset = Asset(
            user_id=user.id,
            type="image",
            title=body.prompt,
            filepath=str(local_path).replace("static", "/static"),
            created_at=datetime.utcnow(),
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)

        return {
            "image_url": asset.filepath,
            "title": body.prompt,
            "asset_id": asset.id,
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Image save failed: {str(e)}"})
