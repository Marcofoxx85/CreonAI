# register.py

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import User
from passlib.context import CryptContext

router = APIRouter()

# Password hashing setup
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash_pw = lambda p: pwd_ctx.hash(p)

# DB session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── GET: Register page ─────────────────────────
@router.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return open("register.html").read()

# ── POST: Handle form ──────────────────────────
@router.post("/register")
def register_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.email == email).first():
        return HTMLResponse("❌ Email already registered.", status_code=400)

    user = User(email=email, hashed_password=hash_pw(password))
    db.add(user)
    db.commit()

    return RedirectResponse("/login", status_code=302)
