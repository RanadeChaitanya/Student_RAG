import asyncio
import sys
import time

import httpx

P = "/api/v1"
passed = 0
failed = 0
errors = []

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        msg = f"  FAIL  {name} {detail}"
        print(msg)
        errors.append(msg)

async def test_all():
    global passed, failed
    start = time.time()
    sess_id = f"test-practice-{int(time.time())}"
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=15) as c:

        # ── Health ──
        r = await c.get("/health")
        check("GET /health returns 200", r.status_code == 200)
        if r.status_code == 200:
            data = r.json()
            check("/health has status=healthy", data.get("status") == "healthy")

        # ── Students ──
        r = await c.get(f"{P}/students/")
        check("GET /students/ returns 200", r.status_code == 200)
        students = r.json()
        check(f"GET /students/ has >= 50 students", len(students) >= 50)
        first_student = students[0]
        sid = first_student["id"]
        check("Student has id field", "id" in first_student)
        check("Student has name field", "name" in first_student)
        check("Student has grade field", "grade" in first_student)
        check("Student has exam_target field", "exam_target" in first_student)

        r = await c.get(f"{P}/students/{sid}")
        check("GET /students/{id} returns 200", r.status_code == 200)
        s = r.json()
        check("Student detail matches id", s.get("id") == sid)
        check("Student has exam_target", s.get("exam_target") in ["JEE_Main", "JEE_Advanced"])

        r = await c.get(f"{P}/students/{sid}/mastery")
        check("GET /students/{id}/mastery returns 200", r.status_code == 200)
        m = r.json()
        check("Mastery has overall_score", "overall_score" in m)
        check("Mastery has subject_breakdown", "subject_breakdown" in m)
        check("Mastery has weak_topics", "weak_topics" in m)
        check("Mastery has strengths", "strengths" in m)

        r = await c.get(f"{P}/students/{sid}/weak-topics")
        check("GET /students/{id}/weak-topics returns 200", r.status_code == 200)
        wt = r.json()
        check("Weak topics is a list", isinstance(wt, list))

        r = await c.get(f"{P}/students/nonexistent-id-12345")
        check("GET /students/nonexistent returns 404", r.status_code == 404)

        # ── Questions ──
        r = await c.get(f"{P}/questions/app")
        check("GET /questions/app returns 200", r.status_code == 200)
        app_qs = r.json()
        check(f"App questions count >= 80", len(app_qs) >= 80)
        if app_qs:
            check("App question has id", "id" in app_qs[0])
            check("App question has question_text", "question_text" in app_qs[0])
            check("App question has options", "options" in app_qs[0])

        r = await c.get(f"{P}/questions/test")
        check("GET /questions/test returns 200", r.status_code == 200)
        test_qs = r.json()
        check(f"Test questions count > 0", len(test_qs) > 0)
        if test_qs:
            check("Test question has year", "year" in test_qs[0])
            check("Test question has exam_type", "exam_type" in test_qs[0])
            check("Test question has exam_type in [JEE_Main,JEE_Advanced]", test_qs[0]["exam_type"] in ["JEE_Main", "JEE_Advanced"])

        # ── Sessions ──
        r = await c.get(f"{P}/sessions/student/{sid}/all")
        check("GET /sessions/student/{id}/all returns 200", r.status_code == 200)
        sessions = r.json()
        check(f"Student has sessions (>=5)", len(sessions) >= 5)
        if sessions:
            s0 = sessions[0]
            check("Session has session_type", "session_type" in s0)
            check("Session has questions_count", "questions_count" in s0)
            check("Session has correct_count", "correct_count" in s0)
            check("Session has started_at", "started_at" in s0)
            assessment_sessions = [s for s in sessions if s["session_type"] == "assessment"]
            check(f"Student has assessment sessions (>=1)", len(assessment_sessions) >= 1)
            practice_sessions = [s for s in sessions if s["session_type"] == "practice"]
            check(f"Student has practice sessions (>=1)", len(practice_sessions) >= 1)

        r = await c.get(f"{P}/sessions/student/{sid}/active")
        check("GET /sessions/student/{id}/active returns 200", r.status_code == 200)

        # ── Practice ──
        r = await c.post(f"{P}/practice/generate", json={
            "student_id": sid, "session_id": sess_id,
            "target_concept": "Motion in 1D", "error_category": "concept_misunderstood",
            "difficulty_band": "adaptive", "question_count": 5,
        })
        check("POST /practice/generate returns 200", r.status_code == 200)
        pg = r.json()
        check("Practice gen has practice_session_id", "practice_session_id" in pg)
        check("Practice gen has questions list", "questions" in pg)
        if pg.get("questions"):
            check("Practice gen has some questions", len(pg["questions"]) > 0)
            q0 = pg["questions"][0]
            check("Practice question has id", "id" in q0)
            check("Practice question has question_text", "question_text" in q0)
            check("Practice question has options", "options" in q0)

        r = await c.get(f"{P}/practice/hint/1")
        check("GET /practice/hint/{id} returns 200", r.status_code == 200)
        hint = r.json()
        check("Hint has question_id", "question_id" in hint)
        check("Hint has hint text", "hint" in hint)

        r = await c.get(f"{P}/practice/explanation/1")
        check("GET /practice/explanation/{id} returns 200", r.status_code == 200)
        expl = r.json()
        check("Explanation has question_id", "question_id" in expl)
        check("Explanation has text", "explanation" in expl)

        r = await c.post(f"{P}/practice/{sess_id}/result", json={
            "student_id": sid,
            "attempts": [
                {"question_id": 1, "subtopic": "Motion in 1D", "is_correct": True, "response_time_seconds": 25, "hints_used": 0, "retry_count": 0, "is_recurrence": False, "subject": "Physics", "topic": "Kinematics"},
                {"question_id": 2, "subtopic": "Motion in 1D", "is_correct": False, "response_time_seconds": 60, "hints_used": 1, "retry_count": 0, "is_recurrence": False, "subject": "Physics", "topic": "Kinematics"},
            ],
        })
        check("POST /practice/{id}/result returns 200", r.status_code == 200)
        pr = r.json()
        check("Practice result has practice_session_id", "practice_session_id" in pr)
        check("Practice result has mastery_delta", "mastery_delta" in pr)
        check("Practice result has weak_topics_remaining", "weak_topics_remaining" in pr)

        # ── Assessment ──
        r = await c.post(f"{P}/assessment/", json={
            "student_id": sid, "subject": "physics",
            "topic": "Kinematics", "time_limit_minutes": 30,
        })
        check("POST /assessment/ returns 201", r.status_code == 201)
        ar = r.json()
        check("Assessment has id", "id" in ar)
        check("Assessment has questions", "questions" in ar)
        assessment_id = ar["id"]
        questions = ar.get("questions", [])
        check(f"Assessment has >=3 questions", len(questions) >= 3)

        if questions:
            q1 = questions[0]
            r = await c.post(f"{P}/assessment/{assessment_id}/answer", json={
                "question_id": q1.get("id", q1.get("question_id")),
                "student_answer": "A", "response_time_seconds": 30,
            })
            check("POST /assessment/{id}/answer returns 200/201", r.status_code in [200, 201])

        r = await c.post(f"{P}/assessment/{assessment_id}/complete")
        check("POST /assessment/{id}/complete returns 200", r.status_code == 200)
        comp = r.json()
        check("Assessment complete has score_percentage", "score_percentage" in comp or "score" in comp)

        r = await c.get(f"{P}/assessment/{assessment_id}")
        check("GET /assessment/{id} returns 200", r.status_code == 200)

        # ── Diagnosis ──
        r = await c.get(f"{P}/diagnosis/student/{sid}/history?limit=20")
        check("GET /diagnosis/student/{id}/history returns 200", r.status_code == 200)
        dh = r.json()
        check("Diagnosis history is a list", isinstance(dh, list))

        r = await c.get(f"{P}/diagnosis/student/{sid}/patterns")
        check("GET /diagnosis/student/{id}/patterns returns 200", r.status_code == 200)
        dp = r.json()
        check("Diagnosis patterns is a list", isinstance(dp, list))
        if dp:
            check("Pattern has error_category", "error_category" in dp[0])
            check("Pattern has count", "count" in dp[0])

        # ── Analytics ──
        r = await c.get(f"{P}/analytics/student/{sid}")
        check("GET /analytics/student/{id} returns 200", r.status_code == 200)
        an = r.json()
        check("Analytics has overall_mastery", "overall_mastery" in an)
        check("Analytics has average_qconf", "average_qconf" in an)
        check("Analytics has weak_topics", "weak_topics" in an)
        check("Analytics has strengths", "strengths" in an)
        check("Analytics has practice_recommendation", "practice_recommendation" in an)

        if sessions:
            r = await c.get(f"{P}/analytics/session/{sessions[0]['id']}")
            check("GET /analytics/session/{id} returns 200", r.status_code == 200)
            sr = r.json()
            check("Session report has session_id", "session_id" in sr)
            check("Session report has accuracy_percent", "accuracy_percent" in sr)

        # ── Concept Graph ──
        r = await c.get(f"{P}/graph/full-graph")
        check("GET /graph/full-graph returns 200", r.status_code == 200)
        fg = r.json()
        check("Full graph has nodes", "nodes" in fg)
        check("Full graph has edges", "edges" in fg)
        check(f"Full graph has >=40 nodes", len(fg.get("nodes", [])) >= 40)

        r = await c.get(f"{P}/graph/concepts")
        check("GET /graph/concepts returns 200", r.status_code == 200)
        concepts = r.json()
        check(f"Concepts list has >=40 items", len(concepts) >= 40)

        r = await c.get(f"{P}/graph/concepts/newtons-laws")
        check("GET /graph/concepts/{id} exists returns 200", r.status_code == 200)
        r = await c.get(f"{P}/graph/concepts/nonexistent-concept")
        check("GET /graph/concepts/{id} missing returns 404", r.status_code == 404)

        r = await c.get(f"{P}/graph/concepts/newtons-laws/chain")
        check("GET /graph/concepts/{id}/chain returns 200", r.status_code == 200)
        chain = r.json()
        check("Chain is a list", isinstance(chain, list))

        r = await c.get(f"{P}/graph/concepts/newtons-laws/gaps/{sid}")
        check("GET /graph/concepts/{id}/gaps/{student} returns 200", r.status_code == 200)

        # ── Retrieval ──
        r = await c.get(f"{P}/retrieval/health")
        check("GET /retrieval/health returns 200", r.status_code == 200)

        # ── Edge Cases ──
        r = await c.get(f"{P}/students/invalid-uuid-format")
        check("GET /students invalid id returns 4xx", r.status_code >= 400)

        # ── Data Integrity Checks ──
        r = await c.get(f"{P}/students/")
        all_students = r.json()
        check("All students have unique IDs", len(set(s["id"] for s in all_students)) == len(all_students))
        boards = set(s["board"] for s in all_students)
        check(f"Multiple boards present ({len(boards)})", len(boards) >= 3)
        grades = set(s["grade"] for s in all_students)
        check("Grades 11 and 12 both present", "11" in grades and "12" in grades)

        r = await c.get(f"{P}/questions/app")
        all_app = r.json()
        subjects = set(q["subject"] for q in all_app)
        check(f"App questions span {len(subjects)} subjects", len(subjects) >= 2)

        r = await c.get(f"{P}/students/{sid}/mastery")
        mastery = r.json()
        wt = mastery.get("weak_topics", [])
        st = mastery.get("strengths", [])
        check(f"Student has weak topics identified", len(wt) > 0)
        check(f"Student has strengths identified", len(st) > 0)

    elapsed = time.time() - start
    print(f"\n{'='*50}")
    print(f"RESULTS: {passed} passed, {failed} failed, {passed+failed} total")
    print(f"Duration: {elapsed:.1f}s")
    if errors:
        print(f"\nFailures:")
        for e in errors:
            print(e)
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(test_all())
    sys.exit(0 if success else 1)
