# utils.py

import os
import uuid
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.models import User, CreditTransaction, ActivityLog, Asset


# ───────────────────────────────────────────────
# Check if user has enough credits
# ───────────────────────────────────────────────
def check_user_credits(db: Session, user_id: int, required: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.credits < required:
        raise HTTPException(status_code=402, detail="Insufficient credits")
    user.credits -= required

    tx = CreditTransaction(
        user_id=user.id,
        amount=-required,
        type="generation",
        description=f"Used {required} credits"
    )
    db.add(tx)
    db.commit()
    return user.credits


# ───────────────────────────────────────────────
# Log a user action
# ───────────────────────────────────────────────
def log_action(db: Session, user_id: int, action: str, metadata: str = ""):
    log = ActivityLog(user_id=user_id, action=action, metadata=metadata)
    db.add(log)
    db.commit()
from fastapi import UploadFile
from shutil import copyfileobj

# ───────────────────────────────────────────────
# Save uploaded/generated file to /media folder
# and create Asset DB entry
# ───────────────────────────────────────────────
def save_asset_file(
    db: Session,
    user_id: int,
    file: UploadFile,
    asset_type: str,
    title: str = ""
):
    # Ensure media directory exists
    folder = f"static/media/{asset_type}s"
    os.makedirs(folder, exist_ok=True)

    # Generate unique filename
    ext = os.path.splitext(file.filename)[-1]
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(folder, filename)

    # Save file to disk
    with open(path, "wb") as out_file:
        copyfileobj(file.file, out_file)

    # Create DB asset entry
    asset = Asset(
        user_id=user_id,
        type=asset_type,
        title=title or file.filename,
        filepath=path.replace("static/", "/static/"),  # browser path
        created_at=datetime.utcnow()
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset
