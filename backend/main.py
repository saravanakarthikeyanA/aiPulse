import logging
import os
import sys
from typing import List, Dict, Any

# Ensure repository root is on sys.path so imports like `from backend.agent` work
# even when running `uvicorn main:app` from the `backend/` directory.
_here = os.path.dirname(__file__)
_repo_root = os.path.dirname(_here)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agent import fetch_news, chat_with_news, cleanup

logger = logging.getLogger("ai_pulse")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Pulse Backend")

# Allow frontend at localhost:5173
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ALLOWED_TOPICS = {"LLM Releases", "Research", "Regulation", "Industry", "Tools", "All"}


class NewsRequest(BaseModel):
    topic: str


class HistoryItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[HistoryItem] = []


@app.get("/api/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/news")
async def api_news(req: NewsRequest) -> Dict[str, Any]:
    topic = req.topic or "All"
    if topic not in ALLOWED_TOPICS:
        raise HTTPException(status_code=400, detail=f"Invalid topic '{topic}'.")

    try:
        result = await fetch_news(topic)
        return result
    except Exception as exc:
        logger.exception("Error fetching news")
        raise HTTPException(status_code=500, detail="Unable to fetch news. Please try again later.")


@app.post("/api/chat")
async def api_chat(req: ChatRequest) -> Dict[str, Any]:
    if not req.message:
        raise HTTPException(status_code=400, detail="Message is required.")

    # Convert pydantic history to plain list of dicts
    history = [{"role": h.role, "content": h.content} for h in req.history]

    try:
        result = await chat_with_news(req.message, history)
        return result
    except Exception:
        logger.exception("Error in chat_with_news")
        raise HTTPException(status_code=500, detail="Unable to process chat. Please try again later.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)


@app.on_event("shutdown")
def _on_shutdown():
    """FastAPI shutdown hook: ensure agent cleanup runs when the server stops."""
    try:
        cleanup()
    except Exception:
        logger.exception("Error during agent cleanup")
