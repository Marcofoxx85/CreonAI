from fastapi import FastAPI

from backend.auth import router as auth_router
from backend.chat import router as chat_router
from backend.image import router as image_router
from backend.audio import router as audio_router
from backend.video import router as video_router
from backend.stripe import router as stripe_router

def register_routes(app: FastAPI):
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
    app.include_router(image_router, prefix="/api/image", tags=["Image"])
    app.include_router(audio_router, prefix="/api/audio", tags=["Audio"])
    app.include_router(video_router, prefix="/api/video", tags=["Video"])
    app.include_router(stripe_router, prefix="/api/stripe", tags=["Stripe"])
