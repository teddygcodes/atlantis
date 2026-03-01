"""Takeoff FastAPI server — adversarial lighting takeoff pipeline with SSE streaming.

Mirrors sydyn/api.py exactly: same lifespan, CORS, SSE streaming pattern.
"""

import os
import json
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from takeoff.engine import TakeoffEngine
from core.llm import LLMProvider

# Load env vars
load_dotenv(override=True)


# ─── Request / Response Models ────────────────────────────────────────────────

class SnippetModel(BaseModel):
    """Single drawing snippet."""
    id: str
    label: str                      # fixture_schedule | rcp | panel_schedule | plan_notes | detail | site_plan
    sub_label: Optional[str] = None # Area name for RCP snippets
    page_number: Optional[int] = None
    image_data: str                 # Base64-encoded PNG
    bbox: Optional[dict] = None


class TakeoffRequest(BaseModel):
    """Takeoff job request."""
    snippets: List[SnippetModel]
    mode: Optional[str] = None      # fast | strict | liability (auto-selects strict if None)
    drawing_name: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    takeoff_ready: bool
    api_keys_valid: bool


# ─── Global Engine ────────────────────────────────────────────────────────────

engine: TakeoffEngine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    global engine

    print("[TAKEOFF API] Starting up...")

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment")

    # Verify Anthropic API key
    try:
        test_provider = LLMProvider(api_key=anthropic_key, mode="api")
        test_response = test_provider.complete(
            system_prompt="You are a test assistant.",
            user_prompt="Reply with OK",
            max_tokens=5,
            temperature=0.0,
            model="claude-haiku-4-5-20251001",
            task_type="takeoff_test"
        )
        content = test_response.content or ""
        if not content or content.startswith("[LLM ERROR"):
            raise RuntimeError(f"Anthropic API test returned error: {content}")
        print("[TAKEOFF API] ✓ Anthropic API key verified")
    except Exception as e:
        raise RuntimeError(f"Anthropic API verification failed: {e}")

    # Initialize engine
    try:
        engine = TakeoffEngine(db_path="takeoff_api.db")
        print("[TAKEOFF API] ✓ Takeoff engine initialized")
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Takeoff engine: {e}")

    print("[TAKEOFF API] 🚀 Server ready")

    yield

    print("[TAKEOFF API] Shutting down...")
    if engine and engine.db:
        engine.db.close()
        print("[TAKEOFF API] ✓ Database connection closed")


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Takeoff API",
    description="Adversarial lighting takeoff with constitutional governance",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://atlantiskb.com",
        "https://www.atlantiskb.com",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── SSE Streaming ────────────────────────────────────────────────────────────

async def generate_takeoff_stream(request: TakeoffRequest) -> AsyncGenerator[str, None]:
    """Generate SSE stream for a takeoff job."""
    import queue
    import threading
    import time as _time

    status_queue = queue.Queue(maxsize=200)
    result_container = []
    done_event = threading.Event()  # set in finally so always fires on thread exit

    def status_callback(message: str):
        status_queue.put({"type": "status", "message": message})

    def run_job():
        try:
            snippets = [s.model_dump() for s in request.snippets]
            mode = request.mode or "strict"
            result = engine.run_takeoff(
                snippets=snippets,
                mode=mode,
                drawing_name=request.drawing_name,
                status_callback=status_callback
            )
            result_container.append(result)
            status_queue.put({"type": "done"})
        except Exception as e:
            status_queue.put({"type": "error", "message": str(e)})
        finally:
            done_event.set()  # always signals completion even on exception

    # Run job in background thread
    job_thread = threading.Thread(target=run_job, daemon=True)
    job_thread.start()

    # Stream status updates with 10-minute hard timeout
    MAX_WAIT_SECONDS = 600
    start_time = _time.time()

    try:
        while True:
            # Drain any queued messages before checking done_event
            # to avoid missing messages produced just before thread exit
            try:
                msg = status_queue.get_nowait()
                if msg["type"] == "status":
                    yield f"data: {json.dumps(msg)}\n\n"
                elif msg["type"] == "error":
                    yield f"data: {json.dumps(msg)}\n\n"
                    break
                elif msg["type"] == "done":
                    break
                continue
            except queue.Empty:
                pass

            # Queue is empty — now check if the thread has finished
            if done_event.is_set():
                # Drain any final messages that arrived before event was checked
                while True:
                    try:
                        msg = status_queue.get_nowait()
                        if msg["type"] == "status":
                            yield f"data: {json.dumps(msg)}\n\n"
                        elif msg["type"] in ("error", "done"):
                            break
                    except queue.Empty:
                        break
                break

            # Hard timeout guard
            if _time.time() - start_time > MAX_WAIT_SECONDS:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Takeoff pipeline timed out after 10 minutes'})}\n\n"
                return
            await asyncio.sleep(0.05)

        if not result_container:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Takeoff failed to produce result'})}\n\n"
            return

        result = result_container[0]

        if result.get("error"):
            yield f"data: {json.dumps({'type': 'error', 'message': result.get('message', result['error'])})}\n\n"
            return

        # Format result for frontend
        frontend_result = _format_for_frontend(result)

        yield f"data: {json.dumps({'type': 'result', 'data': frontend_result})}\n\n"
        await asyncio.sleep(0.1)
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        error_msg = str(e)
        print(f"[TAKEOFF API] Error: {error_msg}")
        yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"


def _format_for_frontend(result: dict) -> dict:
    """Format engine result for frontend consumption."""
    return {
        "job_id": result.get("job_id"),
        "mode": result.get("mode"),
        "grand_total": result.get("grand_total", 0),
        "fixture_table": result.get("fixture_table", []),
        "areas_covered": result.get("areas_covered", []),
        "confidence_band": result.get("confidence_band", "UNKNOWN"),
        "confidence_score": result.get("confidence", 0.0),
        "confidence_explanation": result.get("confidence_explanation", ""),
        "verdict": result.get("verdict", "UNKNOWN"),
        "violations": result.get("violations", []),
        "flags": result.get("flags", []),
        "ruling_summary": result.get("ruling_summary", ""),
        "adversarial_log": result.get("adversarial_log", []),
        "agent_counts": result.get("agent_counts", {}),
        "latency_ms": result.get("latency_ms", 0)
    }


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/takeoff/health")
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    api_keys_valid = bool(anthropic_key)
    takeoff_ready = engine is not None

    return HealthResponse(
        status="healthy" if (api_keys_valid and takeoff_ready) else "degraded",
        takeoff_ready=takeoff_ready,
        api_keys_valid=api_keys_valid
    )


@app.post("/takeoff/run")
async def run_takeoff(request: TakeoffRequest):
    """Execute adversarial takeoff with SSE streaming.

    Receives snippet data (JSON with base64 images), runs full pipeline,
    returns results via SSE streaming.
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Takeoff engine not initialized")

    if not request.snippets:
        raise HTTPException(status_code=400, detail="At least one snippet is required")

    # Guard against oversized requests (max 30 snippets, each image ≤ 15MB base64, total ≤ 50MB)
    MAX_SNIPPETS = 30
    MAX_IMAGE_B64_BYTES = 15 * 1024 * 1024  # 15 MB base64 ≈ 11 MB image
    MAX_TOTAL_B64_BYTES = 50 * 1024 * 1024  # 50 MB total across all snippets
    if len(request.snippets) > MAX_SNIPPETS:
        raise HTTPException(status_code=400, detail=f"Too many snippets (max {MAX_SNIPPETS})")
    total_size = 0
    for snip in request.snippets:
        img_size = len(snip.image_data)
        if img_size > MAX_IMAGE_B64_BYTES:
            raise HTTPException(status_code=400, detail=f"Snippet '{snip.id}' image_data exceeds 15 MB limit")
        total_size += img_size
    if total_size > MAX_TOTAL_B64_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Total snippet payload {total_size // (1024 * 1024)} MB exceeds 50 MB limit"
        )

    fixture_snippets = [s for s in request.snippets if s.label == "fixture_schedule"]
    rcp_snippets = [s for s in request.snippets if s.label == "rcp"]

    if not fixture_snippets:
        raise HTTPException(status_code=400, detail="At least 1 fixture_schedule snippet is required")

    if not rcp_snippets:
        raise HTTPException(status_code=400, detail="At least 1 rcp snippet is required")

    return StreamingResponse(
        generate_takeoff_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/takeoff/jobs")
async def list_jobs(limit: int = 20):
    """List recent takeoff jobs."""
    if not engine:
        raise HTTPException(status_code=503, detail="Takeoff engine not initialized")
    jobs = engine.db.list_jobs(limit=limit)
    return {"jobs": jobs, "count": len(jobs)}


@app.get("/takeoff/jobs/{job_id}")
async def get_job(job_id: str):
    """Get results for a specific takeoff job."""
    if not engine:
        raise HTTPException(status_code=503, detail="Takeoff engine not initialized")

    job = engine.db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    counts = engine.db.get_job_counts(job_id)
    adv_log = engine.db.get_job_adversarial_log(job_id)

    return {
        "job": job,
        "fixture_counts": counts,
        "adversarial_log": adv_log
    }


@app.get("/takeoff/result/{job_id}")
async def get_result(job_id: str):
    """Retrieve the full formatted result for a completed takeoff job.

    Useful for clients that disconnected from the SSE stream before receiving the result.
    Returns the same format as the SSE 'result' event payload.
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Takeoff engine not initialized")

    job = engine.db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    full_result = engine.db.get_full_result(job_id)
    if not full_result:
        # Job exists but result not yet stored (still running or failed before completion)
        status = job.get("status", "unknown")
        raise HTTPException(
            status_code=404,
            detail=f"No result available for job {job_id} (status: {status})"
        )

    return full_result


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Takeoff API",
        "version": "0.1.0",
        "description": "Adversarial lighting takeoff with constitutional governance",
        "endpoints": {
            "health": "GET /takeoff/health",
            "run": "POST /takeoff/run",
            "jobs": "GET /takeoff/jobs",
            "job": "GET /takeoff/jobs/{job_id}",
            "result": "GET /takeoff/result/{job_id}"
        }
    }
