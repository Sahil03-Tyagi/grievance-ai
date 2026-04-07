from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join(
    os.path.dirname(__file__), 'grievance_ai_agent/.env'))

import uuid
from uuid import UUID
import json
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy import text

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from grievance_ai_agent.agent import root_agent
from grievance_ai_agent.tools.escalation_tool import check_and_escalate
from grievance_ai_agent.tools.tracking_tool import get_grievance_status
from grievance_ai_agent.tools.db_tools import engine

# ── Logging setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger("grievance_api")

app = FastAPI(title="GrievanceOS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

session_service = InMemorySessionService()
APP_NAME = "grievance_os"

# Agent name → pipeline key mapping
AGENT_KEY_MAP = {
    "classifier_agent": "classifier",
    "drafting_agent":   "drafting",
    "execution_agent":  "execution",
    "tracking_agent":   "tracking",
    "log_grievance":    "tracking",
    "grievance_orchestrator": None,  # orchestrator events — skip
}


class GrievanceRequest(BaseModel):
    complaint: str


# ── SSE stream endpoint ────────────────────────────────────────
@app.post("/grievance/stream")
async def file_grievance_stream(req: GrievanceRequest):
    """
    File a grievance and stream real-time agent events via SSE.
    Frontend listens to this and updates pipeline UI as agents fire.
    """
    async def event_stream():
        session_id = str(uuid.uuid4())
        user_id    = "citizen"

        log.info(f"NEW GRIEVANCE | session={session_id[:8]} | complaint='{req.complaint[:60]}'")

        try:
            await session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
            log.info(f"Session created | {session_id[:8]}")
        except Exception as e:
            log.error(f"Session creation failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return

        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service
        )

        message = types.Content(
            role="user",
            parts=[types.Part(text=req.complaint)]
        )

        current_agent = None
        event_count   = 0
        final_text    = ""

        try:
            log.info("Starting agent pipeline...")
            yield f"data: {json.dumps({'type': 'pipeline_start'})}\n\n"

            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=message
            ):
                event_count += 1

                # ── Agent started ──────────────────────────
                if hasattr(event, 'author') and event.author:
                    agent_name = event.author
                    pipeline_key = AGENT_KEY_MAP.get(agent_name)

                    if pipeline_key and pipeline_key != current_agent:
                        current_agent = pipeline_key
                        log.info(f"AGENT RUNNING → {agent_name} (key={pipeline_key})")

                        yield f"data: {json.dumps({'type': 'agent_start', 'agent': pipeline_key, 'agent_name': agent_name})}\n\n"

                # ── Tool called ────────────────────────────
                if hasattr(event, 'content') and event.content:
                    for part in (event.content.parts or []):
                        if hasattr(part, 'function_call') and part.function_call:
                            tool_name = part.function_call.name
                            log.info(f"  TOOL CALL → {tool_name}")
                            yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool_name, 'agent': current_agent})}\n\n"

                        if hasattr(part, 'function_response') and part.function_response:
                            tool_name = part.function_response.name
                            log.info(f"  TOOL DONE ← {tool_name}")
                            yield f"data: {json.dumps({'type': 'tool_done', 'tool': tool_name, 'agent': current_agent})}\n\n"

                # ── Agent completed ────────────────────────
                if event.is_final_response():
                    raw = ""
                    if event.content and event.content.parts:
                        raw = event.content.parts[0].text or ""
                    final_text = raw
                    log.info(f"PIPELINE COMPLETE | events_processed={event_count}")
                    log.info(f"Final response: {final_text[:200]}")

                    yield f"data: {json.dumps({'type': 'final', 'response': final_text})}\n\n"
                    break

                # Heartbeat every 10 events so browser doesn't timeout
                if event_count % 10 == 0:
                    log.info(f"  ... processing (event #{event_count})")
                    yield f"data: {json.dumps({'type': 'heartbeat', 'count': event_count})}\n\n"

        except Exception as e:
            log.error(f"Pipeline error: {type(e).__name__}: {e}")
            import traceback
            log.error(traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",
            "Access-Control-Allow-Origin": "*",
        }
    )


# ── Regular POST (non-streaming fallback) ─────────────────────
@app.post("/grievance")
async def file_grievance(req: GrievanceRequest):
    """Non-streaming fallback endpoint."""
    session_id = str(uuid.uuid4())
    user_id    = "citizen"

    log.info(f"GRIEVANCE (sync) | complaint='{req.complaint[:60]}'")

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id
    )

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=req.complaint)]
    )

    final_response = ""
    event_count    = 0

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message
    ):
        event_count += 1
        if event_count % 5 == 0:
            log.info(f"  processing event #{event_count}...")

        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text or ""
            log.info(f"Done | {event_count} events | response='{final_response[:100]}'")
            break

    return {"status": "success", "response": final_response}


# ── Other endpoints ────────────────────────────────────────────
@app.get("/grievance/status")
def get_status_by_keyword(keyword: str):
    log.info(f"STATUS LOOKUP | keyword='{keyword}'")
    return get_grievance_status(keyword)


@app.get("/grievance/{grievance_id}")
def get_grievance(grievance_id: UUID):
    log.info(f"GET GRIEVANCE | id={grievance_id[:8]}")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, category, location, issue_summary,
                   status, sla_deadline, escalation_level, created_at
            FROM grievances WHERE id = :id
        """), {"id": grievance_id}).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Grievance not found")

        return {
            "id":               str(result[0]),
            "category":         result[1],
            "location":         result[2],
            "issue_summary":    result[3],
            "status":           result[4],
            "sla_deadline":     str(result[5]),
            "escalation_level": result[6],
            "created_at":       str(result[7])
        }


@app.get("/logs/{grievance_id}")
def get_logs(grievance_id: str):
    log.info(f"GET LOGS | id={grievance_id[:8]}")
    with engine.connect() as conn:
        results = conn.execute(text("""
            SELECT agent_name, action, reasoning,
                   input_data, output_data, timestamp
            FROM workflow_logs
            WHERE grievance_id = :id
            ORDER BY timestamp ASC
        """), {"id": grievance_id}).fetchall()

        return {
            "grievance_id":    grievance_id,
            "reasoning_trace": [
                {
                    "agent":     row[0],
                    "action":    row[1],
                    "reasoning": row[2],
                    "timestamp": str(row[5])
                }
                for row in results
            ]
        }


@app.post("/escalate")
def run_escalation(demo: bool = False):
    log.info(f"ESCALATION CHECK | demo_mode={demo}")
    result = check_and_escalate(demo_mode=demo)
    log.info(f"Escalation done | {result.get('escalated_count', 0)} escalated")
    return result


@app.get("/dashboard")
def get_dashboard():
    with engine.connect() as conn:
        stats = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'filed') as filed,
                COUNT(*) FILTER (WHERE status = 'escalated') as escalated,
                COUNT(*) FILTER (WHERE status = 'resolved') as resolved
            FROM grievances
        """)).fetchone()

        by_category = conn.execute(text("""
            SELECT category, COUNT(*) as count
            FROM grievances
            GROUP BY category
            ORDER BY count DESC
        """)).fetchall()

        return {
            "total_grievances": stats[0],
            "filed":            stats[1],
            "escalated":        stats[2],
            "resolved":         stats[3],
            "by_category": [
                {"category": r[0], "count": r[1]}
                for r in by_category
            ]
        }


@app.get("/")
def serve_ui():
    return FileResponse("index.html")
