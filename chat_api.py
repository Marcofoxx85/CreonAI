from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import openai
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request body schema
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: Optional[str] = "gpt-4"
    messages: List[ChatMessage]
    stream: Optional[bool] = True

# Stream route
@app.post("/api/chat")
async def stream_chat(payload: ChatRequest):
    messages = payload.messages
    model = payload.model

    def event_stream():
        response = openai.ChatCompletion.create(
            model=model,
            messages=[m.dict() for m in messages],
            stream=True
        )
        for chunk in response:
            if "choices" in chunk and chunk["choices"][0]["delta"].get("content"):
                delta = chunk["choices"][0]["delta"]["content"]
                data = {
                    "choices": [{"delta": {"content": delta}}]
                }
                yield f"data: {json.dumps(data)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
