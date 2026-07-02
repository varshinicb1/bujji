from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from bujji.agents.assistant import AssistantAgent
from bujji.core.config import Settings, load_config
from bujji.core.models import ChatRequest as ChatRequestModel

app = FastAPI(
    title="BUJJI API",
    description="AI Engineering Assistant API",
    version="1.0.0",
)

_agent: AssistantAgent | None = None


def get_agent() -> AssistantAgent:
    global _agent
    if _agent is None:
        settings = load_config()
        _agent = AssistantAgent(settings)
    return _agent


class ChatBody(BaseModel):
    message: str
    conversation_id: str | None = None
    stream: bool = False


class PlanBody(BaseModel):
    task: str


class MemorySearchBody(BaseModel):
    query: str
    limit: int = 10
    entry_type: str | None = None
    semantic: bool = True


class MemoryStoreBody(BaseModel):
    content: str
    entry_type: str = "general"
    metadata: dict[str, Any] = {}


@app.on_event("startup")
async def startup() -> None:
    agent = get_agent()
    await agent.initialize()


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "BUJJI", "version": "1.0.0", "status": "running"}


@app.post("/chat")
async def chat(body: ChatBody) -> dict[str, Any]:
    agent = get_agent()
    request = ChatRequestModel(
        message=body.message,
        conversation_id=body.conversation_id,
        stream=body.stream,
    )
    response = await agent.process(request)
    return response.model_dump()


@app.post("/plan")
async def plan(body: PlanBody) -> dict[str, Any]:
    agent = get_agent()
    plan_result = await agent.planner.plan(body.task)
    return plan_result.model_dump()


@app.get("/tools")
async def list_tools() -> list[dict[str, Any]]:
    agent = get_agent()
    return [t.model_dump() for t in agent.tools.list_tools()]


@app.post("/memory/search")
async def memory_search(body: MemorySearchBody) -> list[dict[str, Any]]:
    agent = get_agent()
    results = await agent.memory.search(
        query=body.query,
        limit=body.limit,
        entry_type=body.entry_type,
        semantic=body.semantic,
    )
    return [r.model_dump() for r in results]


@app.post("/memory/store")
async def memory_store(body: MemoryStoreBody) -> dict[str, str]:
    agent = get_agent()
    entry_id = await agent.memory.store(
        content=body.content,
        entry_type=body.entry_type,
        metadata=body.metadata,
    )
    return {"id": entry_id}


@app.get("/providers")
async def list_providers() -> dict[str, str | list[str]]:
    return {
        "providers": ["ollama", "openai", "openrouter", "local"],
        "active_provider": get_agent().llm.provider.provider_name,
    }


@app.get("/status")
async def get_status() -> dict[str, Any]:
    agent = get_agent()
    return {
        "version": "1.0.0",
        "provider": agent.llm.provider.provider_name,
        "model": agent.llm.provider.model_name,
        "memory": await agent.memory.get_stats(),
        "tools_count": len(agent.tools),
    }


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings:
        global _agent
        _agent = AssistantAgent(settings)
    return app
