"""End-to-end API test script."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import uvicorn

from studob.api.app import app

BASE = "http://127.0.0.1:8000"


async def test():
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="error")
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())
    await asyncio.sleep(3)

    results = {}
    async with httpx.AsyncClient(base_url=BASE, timeout=10, follow_redirects=True) as c:
        r = await c.get("/health")
        results["health"] = (r.status_code, "")
        print(f"[OK] health: {r.status_code}")

        r = await c.get("/api/v1/students/")
        students = r.json() if r.status_code == 200 else []
        results["students_list"] = (r.status_code, len(students))
        print(f"[OK] students list: {r.status_code} count={len(students)}")
        sid = students[0]["id"] if students else None

        r = await c.get("/api/v1/questions/app", params={"subject": "Physics"})
        qs = r.json() if r.status_code == 200 else []
        results["questions"] = (r.status_code, len(qs) if isinstance(qs, list) else 0)
        print(f"[OK] questions: {r.status_code} count={len(qs) if isinstance(qs, list) else 0}")

        if not sid:
            print("[FAIL] no student found")
            return

        r = await c.post("/api/v1/sessions/", json={"student_id": sid, "session_type": "practice"})
        results["create_session"] = (r.status_code, r.text[:100])
        if r.status_code in (200, 201):
            sess = r.json().get("session_id") or r.json().get("id")
            print(f"[OK] create session: {r.status_code} sess_id={sess}")
        else:
            print(f"[FAIL] create session: {r.status_code} {r.text[:200]}")
            return

        r = await c.get(f"/api/v1/students/{sid}/mastery")
        results["mastery"] = (r.status_code, r.json() if r.status_code == 200 else None)
        score = r.json().get("overall_score") if r.status_code == 200 else "error"
        print(f"[OK] mastery: {r.status_code} overall={score}")

        # Diagnosis: POST /diagnose (not /analyze)
        r = await c.post(
            "/api/v1/diagnosis/diagnose",
            json={
                "student_id": sid,
                "question_id": 1,
                "question_type": "app",
                "response_text": "A",
                "response_time_seconds": 30.0,
                "hints_used": 0,
                "session_id": sess,
            },
        )
        results["diagnosis"] = (r.status_code, r.text[:100])
        print(f"[OK] diagnosis: {r.status_code}")

        # Retrieval: POST /retrieve with concept_tag, error_category (not query, top_k)
        r = await c.post(
            "/api/v1/retrieval/retrieve",
            json={
                "student_id": sid,
                "session_id": sess,
                "concept_tag": "newtons-laws",
                "error_category": "concept_misunderstood",
            },
        )
        results["retrieval"] = (r.status_code, r.text[:100])
        print(f"[OK] retrieval: {r.status_code}")

        # Practice: POST /generate with target_concept, error_category, question_count
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
        results["practice"] = (r.status_code, r.text[:100])
        print(f"[OK] practice: {r.status_code}")

        # Assessment: POST / (not /create). Requires question_ids: List[int]
        r = await c.post(
            "/api/v1/assessment/",
            json={
                "student_id": sid,
                "subject": "Physics",
                "question_ids": [1, 2],
                "time_limit_minutes": 30,
            },
        )
        results["assessment"] = (r.status_code, r.text[:100])
        if r.status_code in (200, 201):
            aid = r.json().get("id")
            print(f"[OK] create assessment: {r.status_code} id={aid}")
        else:
            print(f"[OK] assessment: {r.status_code}")

        # Analytics: GET /student/{student_id} (singular)
        r = await c.get(f"/api/v1/analytics/student/{sid}")
        results["analytics"] = (r.status_code, r.text[:100])
        print(f"[OK] analytics: {r.status_code}")

    server.should_exit = True
    await task
    print("\n=== ALL TESTS DONE ===")
    for k, (code, _) in results.items():
        status = "PASS" if code in (200, 201, 204) else "FAIL"
        print(f"  {status} {k}: {code}")


if __name__ == "__main__":
    asyncio.run(test())
