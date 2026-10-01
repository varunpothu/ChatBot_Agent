from fastapi import FastAPI
from pydantic import BaseModel

from agents.orchestrator import CoachAIOrchestrator

app = FastAPI(title="CoachAI API", version="0.1.0")
orchestrator = CoachAIOrchestrator()

class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "coachai-api"}

@app.post("/chat")
async def chat(request: ChatRequest):
    return await orchestrator.run(request.message, request.conversation_id)
