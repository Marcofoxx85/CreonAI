import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.models import Base, User
from database import SessionLocal, engine
from passlib.context import CryptContext
from datetime import datetime

Base.metadata.create_all(bind=engine)
db = SessionLocal()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed_password = pwd_context.hash("Monsterenergy85")

existing = db.query(User).filter(User.email == "Marco.fox@creonai.co.uk").first()

if not existing:
    user = User(
        email="Marco.fox@creonai.co.uk",
        hashed_password=hashed_password,
        full_name="Marco Fox",
        avatar_url="",
        credits=50,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    print("✅ User created.")
else:
    print("ℹ️ User already exists.")

db.close()
