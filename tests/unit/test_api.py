"""Tests for api.main"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_create_job_rejects_non_mp4():
    """Create job rejects non-MP4 files."""
    response = client.post(
        "/jobs",
        files={"file": ("test.txt", b"fake content", "text/plain")},
    )
    assert response.status_code == 400


def test_create_job_accepts_mp4():
    """Create job accepts MP4 files."""
    with patch("api.main._run_pipeline"):
        response = client.post(
            "/jobs",
            files={"file": ("test.mp4", b"fake mp4 content", "video/mp4")},
        )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"


def test_get_job_not_found():
    """Get job returns 404 for nonexistent job."""
    response = client.get("/jobs/nonexistent-id")
    assert response.status_code == 404


def test_get_job_returns_status():
    """Get job returns status for existing job."""
    # First create a job
    with patch("api.main._run_pipeline"):
        create_resp = client.post(
            "/jobs",
            files={"file": ("test.mp4", b"fake mp4 content", "video/mp4")},
        )
    job_id = create_resp.json()["job_id"]

    # Then fetch its status
    status_resp = client.get(f"/jobs/{job_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["job_id"] == job_id
    assert data["status"] in ("queued", "running", "done", "error")
    assert "percent" in data
    assert "stage" in data
