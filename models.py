# models.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text
from datetime import datetime

from backend.database import Base  # ✅ USE THIS INSTEAD


# ───────────────────────────────────────────────
# USER MODEL
# ───────────────────────────────────────────────
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)  # ✅ NEW username field
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    avatar_url = Column(String, default="")
    credits = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    subscriptions = relationship("Subscription", back_populates="user")
    assets = relationship("Asset", back_populates="user")
    credit_logs = relationship("CreditTransaction", back_populates="user")
    logs = relationship("ActivityLog", back_populates="user")      # ✅ Needed for ActivityLog
    chat_logs = relationship("ChatLog", back_populates="user")     # ✅ Fixed indent


# ───────────────────────────────────────────────
# CREDIT TRANSACTIONS
# ───────────────────────────────────────────────
class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer)
    type = Column(String)  # e.g., "topup", "generation"
    description = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="credit_logs")


# ───────────────────────────────────────────────
# SUBSCRIPTIONS
# ───────────────────────────────────────────────
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stripe_subscription_id = Column(String, unique=True)
    plan_name = Column(String)
    status = Column(String, default="active")  # or "canceled", "past_due"
    started_at = Column(DateTime, default=datetime.utcnow)
    canceled_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="subscriptions")
# ───────────────────────────────────────────────
# ASSETS (Images, Videos, Audio, PDFs, etc.)
# ───────────────────────────────────────────────
class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)         # image, video, audio, pdf, text
    title = Column(String)
    filepath = Column(String)     # relative path like /media/robot.mp3
    created_at = Column(DateTime, default=datetime.utcnow)
    is_public = Column(Boolean, default=False)

    user = relationship("User", back_populates="assets")


# ───────────────────────────────────────────────
# ACTIVITY LOGS (Login, Generation, etc.)
# ───────────────────────────────────────────────
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)         # e.g., "login", "generate_image", "stripe_webhook"
    meta_data = Column(Text)  # use snake_case or any other name        # ✅ Fixed name
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="logs")
class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)       # "user" or "bot"
    content = Column(Text)
    model = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_logs")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")

class ImageGeneration(Base):
    __tablename__ = "image_generations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    prompt = Column(String)
    image_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")