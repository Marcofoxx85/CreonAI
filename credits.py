# backend/credits.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import SessionLocal, User
from backend.main2 import manager  # circular import is fine for router

router = APIRouter(prefix="/credits", tags=["credits"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── helpers ─────────────────────────────────────────────────────
def get_credits(user_id: int, db: Session) -> int:
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.credits


# ── endpoints ───────────────────────────────────────────────────
@router.post("/add/{amount}")
def add_credits(
    amount: int,
    user: User = Depends(manager),
    db: Session = Depends(get_db),
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    user.credits += amount
    db.commit()
    return {"credits": user.credits}
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/credits", response_class=HTMLResponse)
async def credits_page(request: Request):
    return templates.TemplateResponse("credits.html", {"request": request})
