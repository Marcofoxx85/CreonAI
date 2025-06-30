import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# ── Load environment variables from .env ───────────────
load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "..", "creonai.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
print("[DEBUG] Using DB:", DATABASE_URL)

# ── Create engine and session ──────────────────────────
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Base model ─────────────────────────────────────────
Base = declarative_base()

# ── Initialize all tables (called in main.py) ──────────
def init_db():
    from backend import models  # avoid circular import
    Base.metadata.create_all(bind=engine)

# ── Dependency for DB session ──────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
