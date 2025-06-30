# backend/google_oauth.py

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
import httpx
import os
from .models import User
from .database import SessionLocal
from jose import jwt
from fastapi.responses import RedirectResponse

router = APIRouter()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")  # e.g. http://localhost:8000/api/auth/google/callback

class Token(BaseModel):
    id_token: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/api/auth/google")
async def google_login(token: Token, db=Depends(get_db)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={token.id_token}"
            )
        payload = response.json()

        if payload.get("aud") != GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Invalid Google token")

        email = payload["email"]
        name = payload.get("name", "Unknown User")
        picture = payload.get("picture")

        # Create or fetch user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, name=name, profile_picture=picture)
            db.add(user)
            db.commit()
            db.refresh(user)

        # Return JWT token (or session cookie)
        return {"email": user.email, "id": user.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
