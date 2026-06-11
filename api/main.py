"""FastAPI job endpoints for GNSS Spoofing Aggregator."""

import uuid
import asyncio
import logging
import tempfile
import json
import os
import secrets
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

logger = logging.getLogger(__name__)
app = FastAPI(title="GNSS Spoofing Aggregator API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://totaleclipseoftheheatmap.com",
        "https://www.totaleclipseoftheheatmap.com",
        "http://localhost:5173",   # local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

def verify_credentials(
    credentials: HTTPBasicCredentials = Depends(security)
):
    username = os.environ.get("API_USERNAME", "gnss")
    password = os.environ.get("API_PASSWORD", "changeme")
    correct_user = secrets.compare_digest(
        credentials.username.encode("utf8"),
        username.encode("utf8")
    )
    correct_pass = secrets.compare_digest(
        credentials.password.encode("utf8"),
        password.encode("utf8")
    )
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# In-memory job store (MVP — replace with Redis at Slice 8 hardening)
jobs: dict[str, dict] = {}


@app.post("/jobs")
async def create_job(file: UploadFile = File(...), background_tasks: BackgroundTasks = None, username: str = Depends(verify_credentials)):
    """Create a new job from uploaded MP4."""
    # Validate file is MP4
    if not file.filename.endswith(".mp4"):
        raise HTTPException(400, "Only MP4 files accepted")

    # Create temp directory for this job's work
    work_dir = tempfile.mkdtemp(prefix="gnss_job_")

    # Save uploaded file
    input_path = Path(work_dir) / "input.mp4"
    contents = await file.read()
    input_path.write_bytes(contents)

    # Create job record
    job_id = uuid.uuid4().hex
    jobs[job_id] = {
        "id": job_id,
        "status": "queued",
        "stage": "queued",
        "percent": 0,
        "error": None,
        "poster_path": None,
        "zip_path": None,
        "work_dir": work_dir,
    }

    # Enqueue as background task
    if background_tasks:
        background_tasks.add_task(_run_pipeline, job_id)
    else:
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, _run_pipeline, job_id)

    return {"job_id": job_id, "status": "queued"}


def _run_pipeline(job_id: str):
    """Background task to run the pipeline."""
    job = jobs[job_id]
    job["status"] = "running"

    def progress_cb(stage, pct):
        job["stage"] = stage
        job["percent"] = pct

    try:
        from pipeline.pipeline import run
        input_path = Path(job["work_dir"]) / "input.mp4"
        output_dir = Path(job["work_dir"]) / "output"

        result = run(
            str(input_path),
            str(output_dir),
            progress_callback=progress_cb,
        )

        job["poster_path"] = result["poster_path"]
        job["zip_path"] = result["zip_path"]
        job["status"] = "done"
        job["percent"] = 100

    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
        logger.exception(f"Job {job_id} failed")


@app.get("/jobs/{job_id}")
async def get_job(job_id: str, username: str = Depends(verify_credentials)):
    """Get job status."""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    job = jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "stage": job["stage"],
        "percent": job["percent"],
        "error": job["error"],
    }


@app.get("/jobs/{job_id}/events")
async def job_events(job_id: str, username: str = Depends(verify_credentials)):
    """Server-sent events stream for job progress."""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")

    async def event_stream():
        while True:
            job = jobs.get(job_id)
            if not job:
                break
            data = json.dumps({
                "stage": job["stage"],
                "percent": job["percent"],
                "status": job["status"],
            })
            yield f"data: {data}\n\n"
            if job["status"] in ("done", "error"):
                break
            await asyncio.sleep(1)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
    )


@app.get("/jobs/{job_id}/result/poster")
async def get_poster(job_id: str, username: str = Depends(verify_credentials)):
    """Download poster PNG."""
    job = _get_done_job(job_id)
    return FileResponse(
        job["poster_path"],
        media_type="image/png",
        filename="poster.png",
    )


@app.get("/jobs/{job_id}/result/zip")
async def get_zip(job_id: str, username: str = Depends(verify_credentials)):
    """Download screenshots ZIP."""
    job = _get_done_job(job_id)
    return FileResponse(
        job["zip_path"],
        media_type="application/zip",
        filename="screenshots.zip",
    )


def _get_done_job(job_id: str) -> dict:
    """Get a completed job or raise appropriate HTTP error."""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    job = jobs[job_id]
    if job["status"] == "error":
        raise HTTPException(500, f"Job failed: {job['error']}")
    if job["status"] != "done":
        raise HTTPException(409, "Job not complete yet")
    return job
