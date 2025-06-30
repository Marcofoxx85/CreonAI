# main.py

import os
import json
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

# ── API Keys & Config ─────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not SECRET_KEY:
    raise RuntimeError("❌ SECRET_KEY must be set in .env")

# ── FastAPI & Libs ────────────────────────────────
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_login import LoginManager
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
import requests
import google.generativeai as genai
from openai import AsyncOpenAI
from starlette.background import BackgroundTask

# ── Internal Modules ─────────────────────────────
from backend.database import SessionLocal, init_db
from backend.models import User, ChatLog
from backend.routes import register_routes
from backend.google_oauth import router as google_auth_router
from backend.stripe_webhook import router as stripe_webhook_router
from backend.export_tool import router as export_router

# ── Clients ──────────────────────────────────────
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
genai.configure(api_key=GOOGLE_API_KEY)


# ── App Init ─────────────────────────────────────
from backend.database import engine
from models import Base
from login import router as login_router
from payment import router as payment_router
from webhook import router as webhook_router
from file_upload import router as upload_router

Base.metadata.create_all(bind=engine)
app = FastAPI(title="CreonAI", version="1.0")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")

app.include_router(login_router)
app.include_router(payment_router)
app.include_router(webhook_router)
app.include_router(upload_router)

# ── Password Hashing ─────────────────────────────
pwd_ctx   = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash_pw   = lambda p: pwd_ctx.hash(p)
verify_pw = lambda p, h: pwd_ctx.verify(p, h)

# ── Login Manager ────────────────────────────────
manager = LoginManager(SECRET_KEY, token_url="/login", use_cookie=True)
manager.cookie_name = "creonai_token"

@manager.user_loader()
def load_user(email: str):
    with SessionLocal() as db:
        return db.query(User).filter(User.email == email).first()

# ── DB Dependency ────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Pages ────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/why", response_class=HTMLResponse)
def why(request: Request):
    return templates.TemplateResponse("why-us.html", {"request": request})

@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

# ── Registration ─────────────────────────────────
@app.post("/register", response_class=HTMLResponse)
def register_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "❌ Email already registered."
        }, status_code=400)

    user = User(email=email, hashed_password=hash_pw(password))
    db.add(user)
    db.commit()
    return RedirectResponse("/login", status_code=302)


# ── Login (JSON) ─────────────────────────────────
@app.post("/login")
def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_pw(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"}, status_code=401)

    token = manager.create_access_token(data={"sub": user.email}, expires=timedelta(days=14))
    resp = RedirectResponse("/chat", status_code=302)
    manager.set_cookie(resp, token)
    return resp

# ── Chat Page ────────────────────────────────────
@app.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request, user: User = Depends(manager)):
    return templates.TemplateResponse("chat.html", {"request": request, "user": user})

@app.get("/logout")
def logout():
    resp = RedirectResponse("/", status_code=302)
    manager.set_cookie(resp, "")
    return resp

# ── API Routes ───────────────────────────────────
api = APIRouter(prefix="/api")

@api.post("/chat")
async def api_chat(prompt: str = Form(...), model: str = Form("gpt-4o"), user: User = Depends(manager), db: Session = Depends(get_db)):
    if user.credits <= 0:
        raise HTTPException(402, "Out of credits")

    user.credits -= 1
    db.commit()

    openai_resp = await openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    reply = openai_resp.choices[0].message.content

    db.add(ChatLog(user_id=user.id, role="user", content=prompt, model=model))
    db.add(ChatLog(user_id=user.id, role="bot", content=reply, model=model))
    db.commit()

    return JSONResponse({"role": "bot", "content": reply, "credits": user.credits})

class GeminiReq(BaseModel):
    prompt: str

@api.post("/gemini")
def api_gemini(req: GeminiReq, user: User = Depends(manager), db: Session = Depends(get_db)):
    if not GOOGLE_API_KEY:
        raise HTTPException(503, "Gemini not configured")
    if user.credits <= 0:
        raise HTTPException(402, "Out of credits")

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-pro:generateContent?key={GOOGLE_API_KEY}"
    payload = {"contents": [{"parts": [{"text": req.prompt}]}]}
    resp = requests.post(endpoint, json=payload, timeout=60)
    if not resp.ok:
        raise HTTPException(resp.status_code, resp.text)

    answer = resp.json()["candidates"][0]["content"]["parts"][0]["text"]

    user.credits -= 1
    db.add(ChatLog(user_id=user.id, role="user", content=req.prompt, model="gemini"))
    db.add(ChatLog(user_id=user.id, role="bot", content=answer, model="gemini"))
    db.commit()

    return JSONResponse({"role": "bot", "content": answer, "credits": user.credits})

app.include_router(api)
register_routes(app)

@app.on_event("startup")
def on_startup():
    init_db()

@app.exception_handler(HTTPException)
def http_exc_handler(request: Request, exc: HTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    raise exc
@app.post("/chat-stream")
async def chat_stream(request: Request, user: User = Depends(manager), db: Session = Depends(get_db)):
    data = await request.json()
    messages = data.get("messages", [])

    if not messages or not messages[0].get("content"):
        raise HTTPException(400, "Invalid or missing message content.")

    if user.credits <= 0:
        raise HTTPException(402, "Out of credits")

    user.credits -= 1
    db.commit()

    async def stream():
        response = await openai_client.chat.completions.create(
            model=data.get("model", "gpt-4o"),
            messages=messages,
            stream=True
        )
        async for chunk in response:
            delta = chunk.choices[0].delta.content if chunk.choices else ""
            if delta:
                yield f"data: {json.dumps({'choices': [{'delta': {'content': delta}}]})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
