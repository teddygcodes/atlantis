"""Sydyn FastAPI server for atlantiskb.com frontend.

Provides real-time adversarial search with SSE streaming.
"""

import os
import json
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from sydyn.engine import SydynEngine
from core.llm import LLMProvider

# Load environment variables
load_dotenv(override=True)


class QueryRequest(BaseModel):
    """Query request model."""
    query: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    sydyn_ready: bool
    api_keys_valid: bool


# Global engine instance
engine: SydynEngine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    global engine

    # Startup: Verify API keys and initialize engine
    print("[SYDYN API] Starting up...")

    # Verify ANTHROPIC_API_KEY
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment")

    # Test Anthropic API
    try:
        test_provider = LLMProvider(api_key=anthropic_key, mode="api")
        test_response = test_provider.complete(
            system_prompt="You are a test assistant.",
            user_prompt="Reply with OK",
            max_tokens=5,
            temperature=0.0,
            model="claude-haiku-4-5-20251001",
            task_type="sydyn_test"
        )
        if "[LLM ERROR" in test_response.content:
            raise RuntimeError(f"Anthropic API test failed: {test_response.content}")
        print("[SYDYN API] ✓ Anthropic API key verified")
    except Exception as e:
        raise RuntimeError(f"Anthropic API verification failed: {e}")

    # Verify TAVILY_API_KEY
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        print("[SYDYN API] WARNING: TAVILY_API_KEY not set - searches will fail")
    else:
        print("[SYDYN API] ✓ Tavily API key found")

    # Initialize Sydyn engine
    try:
        engine = SydynEngine(db_path="sydyn_api.db", search_provider="tavily")
        print("[SYDYN API] ✓ Sydyn engine initialized")
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Sydyn engine: {e}")

    print("[SYDYN API] 🚀 Server ready")

    yield

    # Shutdown
    print("[SYDYN API] Shutting down...")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Sydyn API",
    description="Real-time adversarial search with constitutional governance",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - allow atlantiskb.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://atlantiskb.com",
        "https://www.atlantiskb.com",
        "http://localhost:3000",  # Local development
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def generate_sse_stream(query: str) -> AsyncGenerator[str, None]:
    """Generate SSE stream for Sydyn query.

    Args:
        query: User query text

    Yields:
        SSE-formatted messages
    """
    try:
        import queue
        import threading

        # Create a queue for real-time status updates from engine
        status_queue = queue.Queue()
        result_container = []

        def status_callback(message: str):
            """Callback to receive status updates from engine."""
            status_queue.put({"type": "status", "message": message})

        def run_query():
            """Run query in thread and put result in container."""
            try:
                result = engine.query(query, save_kb=True, status_callback=status_callback)
                result_container.append(result)
                status_queue.put({"type": "done"})
            except Exception as e:
                status_queue.put({"type": "error", "message": str(e)})

        # Start query in background thread
        query_thread = threading.Thread(target=run_query, daemon=True)
        query_thread.start()

        # Stream status updates in real-time
        while True:
            try:
                # Non-blocking check with timeout
                msg = status_queue.get(timeout=0.1)

                if msg["type"] == "status":
                    yield f"data: {json.dumps(msg)}\n\n"
                elif msg["type"] == "error":
                    yield f"data: {json.dumps(msg)}\n\n"
                    break
                elif msg["type"] == "done":
                    break
            except queue.Empty:
                # No message yet, continue waiting
                await asyncio.sleep(0.05)

        # Get result from container
        if not result_container:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Query failed to produce result'})}\n\n"
            return

        result = result_container[0]

        # Extract metadata for formatting
        is_cached = result.get("cached", False)
        mode = result.get("mode", "unknown")
        claims_data = result.get("claims", {})

        if isinstance(claims_data, dict):
            researcher_claims = claims_data.get("researcher", 0)
            adversary_attacks = claims_data.get("adversary", 0)
        else:
            researcher_claims = len([c for c in claims_data if c.get("agent_role") == "researcher"])
            adversary_attacks = len([c for c in claims_data if c.get("agent_role") == "adversary"])

        # Format sources for frontend
        sources_list = []
        for source in result.get("sources", []):
            sources_list.append({
                "title": source.get("title", source.get("url", "Unknown")),
                "url": source.get("url", ""),
                "credibility": f"{source.get('credibility_score', 0.0):.2f}"
            })

        # Format violations
        violations = result.get("violations", [])
        if violations and isinstance(violations[0], dict):
            # Dict format: {rule: ..., explanation: ...}
            violations_list = [f"{v.get('rule')}: {v.get('explanation')}" for v in violations]
        else:
            # Already formatted strings
            violations_list = violations

        # Format result for frontend
        frontend_result = {
            "answer_bullets": result.get("answer", "").split("\n"),
            "confidence": result.get("confidence_band", "UNKNOWN"),
            "confidence_score": result.get("confidence", 0.0),
            "sources": sources_list,
            "constitutional_violations": violations_list,
            "audit_trail": {
                "mode": mode,
                "researcher_claims": researcher_claims,
                "adversary_attacks": adversary_attacks,
                "attacks_survived": researcher_claims - adversary_attacks if adversary_attacks > 0 else researcher_claims,
                "judge_verdict": result.get("verdict", "UNKNOWN"),
                "reasoning": result.get("confidence_explanation", ""),
                "cached": is_cached,
                "cache_age_days": result.get("cache_age_days", 0) if is_cached else 0
            }
        }

        # Send final result
        yield f"data: {json.dumps({'type': 'result', 'data': frontend_result})}\n\n"
        await asyncio.sleep(0.1)

        # Send done signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        error_msg = str(e)
        print(f"[SYDYN API] Error processing query: {error_msg}")
        yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"


@app.get("/health")
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status with API key validation
    """
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    api_keys_valid = bool(anthropic_key and tavily_key)
    sydyn_ready = engine is not None

    return HealthResponse(
        status="healthy" if (api_keys_valid and sydyn_ready) else "degraded",
        sydyn_ready=sydyn_ready,
        api_keys_valid=api_keys_valid
    )


@app.post("/api/query")
async def query_endpoint(request: QueryRequest):
    """Execute Sydyn query with SSE streaming.

    Args:
        request: Query request with query text

    Returns:
        SSE stream of pipeline status and results
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Sydyn engine not initialized")

    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query text is required")

    return StreamingResponse(
        generate_sse_stream(request.query.strip()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        }
    )


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Sydyn API",
        "version": "1.0.0",
        "description": "Real-time adversarial search with constitutional governance",
        "endpoints": {
            "health": "/health",
            "query": "POST /api/query"
        }
    }
