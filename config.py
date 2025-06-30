# config.py

import os
from dotenv import load_dotenv
from pathlib import Path

# ───────────────────────────────────────────────
# Load .env
# ───────────────────────────────────────────────
load_dotenv()

# ───────────────────────────────────────────────
# Basic Config
# ───────────────────────────────────────────────
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
BASE_DIR = Path(__file__).resolve().parent

# ───────────────────────────────────────────────
# JWT
# ───────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "changeme-super-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ───────────────────────────────────────────────
# Database
# ───────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./creon.db")

# ───────────────────────────────────────────────
# Stripe
# ───────────────────────────────────────────────
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# ───────────────────────────────────────────────
# OpenAI / Gemini / Veo
# ───────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("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")
GOOGLE_API_KEY = os.getenv("AIzaSyAqlzNFyEk-3Yx4Lfp19pt5hT9eQzJU3Ao")

# ───────────────────────────────────────────────
# Upload Paths
# ───────────────────────────────────────────────
MEDIA_DIR = BASE_DIR / "static" / "media"
IMAGE_DIR = MEDIA_DIR / "images"
AUDIO_DIR = MEDIA_DIR / "audio"
VIDEO_DIR = MEDIA_DIR / "videos"
PDF_DIR   = MEDIA_DIR / "pdfs"

# ───────────────────────────────────────────────
# OAuth (stubbed)
# ───────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
APPLE_CLIENT_ID = os.getenv("APPLE_CLIENT_ID")
APPLE_CLIENT_SECRET = os.getenv("APPLE_CLIENT_SECRET")
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
