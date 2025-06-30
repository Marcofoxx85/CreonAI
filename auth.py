# auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from pydantic import BaseModel
import os
from backend.database import get_db

from backend.models import User
from backend.utils import log_action


router = APIRouter()

# ───────────────────────────────────────────────
# Environment + config
# ───────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ───────────────────────────────────────────────
# Password hashing
# ───────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_pw, hashed_pw):
    return pwd_context.verify(plain_pw, hashed_pw)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ───────────────────────────────────────────────
# Auth Input Schema
# ───────────────────────────────────────────────
class AuthInput(BaseModel):
    email: str
    password: str
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# ───────────────────────────────────────────────
# Register user
# ───────────────────────────────────────────────
@router.post("/register")
def register_user(payload: AuthInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    log_action(db, new_user.id, "register", "Account created")
    return {"message": "User registered", "user_id": new_user.id}


# ───────────────────────────────────────────────
# Login user
# ───────────────────────────────────────────────
@router.post("/token")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"sub": str(user.id)})
    log_action(db, user.id, "login", "Successful login")
    return {"access_token": token, "token_type": "bearer"}


# ───────────────────────────────────────────────
# Auth helper: get current user
# ───────────────────────────────────────────────
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception
    return user


# ───────────────────────────────────────────────
# OAuth login (placeholders)
# ───────────────────────────────────────────────
@router.get("/google/callback")
def google_oauth_stub(code: str):
    return {"status": "Google login stub"}

@router.get("/apple/callback")
def apple_oauth_stub(code: str):
    return {"status": "Apple login stub"}

@router.get("/facebook/callback")
def facebook_oauth_stub(code: str):
    return {"status": "Facebook login stub"}
