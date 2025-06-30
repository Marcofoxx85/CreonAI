# app.py

from dotenv import load_dotenv
import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Load vars from .env in this directory
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set in environment")

app = FastAPI()

class GeminiRequest(BaseModel):
    prompt: str

class GeminiResponse(BaseModel):
    content: str

@app.post("/api/gemini", response_model=GeminiResponse)
async def gemini_chat(req: GeminiRequest):
    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta2/"
        f"models/text-bison-001:generateText?key={GEMINI_API_KEY}"
    )
    payload = {
        "prompt": {"text": req.prompt},
        "temperature": 0.2,
        "maxOutputTokens": 512
    }
    resp = requests.post(endpoint, json=payload)
    if not resp.ok:
        raise HTTPException(status_code=502, detail=f"Gemini API error: {resp.text}")
    data = resp.json()
    return GeminiResponse(content=data["candidates"][0]["output"])
