"""Full end-to-end workflow tested via the API layer."""

import asyncio

import httpx
import pytest
import pytest_asyncio
import uvicorn

from studob.api.app import app


@pytest_asyncio.fixture
async def api_client():
    config = uvicorn.Config(app, host="127.0.0.1", port=8001, log_level="error")
    server = uvicorn.Server(config)
    task = asyncio.get_event_loop().create_task(server.serve())
    await asyncio.sleep(3)

    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8001", timeout=10, follow_redirects=True
    ) as c:
        yield c

    server.should_exit = True
    await task


@pytest.mark.asyncio
async def test_workflow_api(api_client):
    c = api_client

    # 1. Health
    r = await c.get("/health")
    assert r.status_code == 200

    # 2. List students (should be 5 from seed)
    r = await c.get("/api/v1/students/")
    assert r.status_code == 200
    students = r.json()
    assert len(students) >= 1
    sid = students[0]["id"]

    # 3. Get questions
    r = await c.get("/api/v1/questions/app")
    assert r.status_code == 200

    # 4. Create a session
    r = await c.post("/api/v1/sessions/", json={"student_id": sid, "session_type": "practice"})
    assert r.status_code in (200, 201)
    sess = r.json().get("session_id") or r.json().get("id")

    # 5. Get mastery summary
    r = await c.get(f"/api/v1/students/{sid}/mastery")
    assert r.status_code == 200
    assert "overall_score" in r.json()

    # 6. Retrieve learning context
    r = await c.post(
        "/api/v1/retrieval/retrieve",
        json={
            "student_id": sid,
            "session_id": sess,
            "concept_tag": "newtons-laws",
            "error_category": "concept_misunderstood",
        },
    )
    assert r.status_code == 200

    # 7. Generate practice session
    r = await c.post(
        "/api/v1/practice/generate",
        json={
            "student_id": sid,
            "session_id": sess,
            "target_concept": "newtons-laws",
            "error_category": "concept_misunderstood",
            "question_count": 3,
        },
    )
    assert r.status_code == 200

    # 8. Get valid test question IDs first
    r = await c.get("/api/v1/questions/test")
    assert r.status_code == 200
    all_test_qs = r.json()
    assert len(all_test_qs) > 0
    test_q_ids = [q["id"] for q in all_test_qs[:2]]
    assert len(test_q_ids) == 2

    # 9. Create an assessment
    r = await c.post(
        "/api/v1/assessment/",
        json={
            "student_id": sid,
            "subject": "Physics",
            "question_ids": test_q_ids,
            "time_limit_minutes": 30,
        },
    )
    assert r.status_code in (200, 201)

    # 10. Get analytics
    r = await c.get(f"/api/v1/analytics/student/{sid}")
    assert r.status_code == 200
