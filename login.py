from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException
from passlib.context import CryptContext
from pydantic import BaseModel
from backend.database import get_db
from models import User
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter()
SECRET = os.getenv("SECRET_KEY", "supersecret")

# Setup login manager and password hashing
manager = LoginManager(SECRET, token_url="/login", use_cookie=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Model for user registration
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str

# Hash passwords securely
def hash_password(password: str):
    return pwd_context.hash(password)

# Verify password
def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)

# Get user by username
@manager.user_loader
def load_user(username: str, db: Session = Depends(get_db)):
    return db.query(User).filter(User.username == username).first()

# Register route
@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter((User.username == user.username) | (User.email == user.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists.")

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        full_name=user.full_name,
        credits=0,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "username": new_user.username,
        "credits": new_user.credits
    }

# Login route
@router.post("/login")
def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsException

    access_token = manager.create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}
