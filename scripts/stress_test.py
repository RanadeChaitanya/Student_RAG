import asyncio, httpx, time, sys, statistics, uuid

P = "/api/v1"
passed = failed = 0
errors = []

def check(name, ok):
    global passed, failed
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}")
    if ok:
        passed += 1
    else:
        failed += 1
        errors.append(name)

async def stress_test():
    global passed, failed
    print("=" * 70)
    print("  COMPREHENSIVE STRESS TEST -- Studob Platform")
    print("=" * 70)
    start = time.time()

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=30) as c:
        # -- Setup --
        r = await c.get(f"{P}/students/")
        if r.status_code != 200:
            print("FATAL: Server not responding")
            return
        students = r.json()
        sid = students[0]["id"] if students else None
        if not sid:
            print("FATAL: No students found")
            return
        print(f"\n  Target: student {sid[:8]}... | {len(students)} total students\n")

        # --------------------------------------------------
        # PHASE 1: Sequential endpoint validation (all endpoints, 3 reps each)
        # --------------------------------------------------
        print("--- Phase 1: Sequential endpoint validation ---")

        sequential_tests = [
            ("GET /health", lambda: c.get("/health")),
            ("GET /students", lambda: c.get(f"{P}/students/")),
            ("GET /students/{id}", lambda: c.get(f"{P}/students/{sid}")),
            ("GET /students/{id}/mastery", lambda: c.get(f"{P}/students/{sid}/mastery")),
            ("GET /students/{id}/weak-topics", lambda: c.get(f"{P}/students/{sid}/weak-topics")),
            ("GET /questions/app", lambda: c.get(f"{P}/questions/app")),
            ("GET /questions/test", lambda: c.get(f"{P}/questions/test")),
            ("GET /sessions/student/{id}/all", lambda: c.get(f"{P}/sessions/student/{sid}/all")),
            ("GET /sessions/student/{id}/active", lambda: c.get(f"{P}/sessions/student/{sid}/active")),
            ("GET /diagnosis/student/{id}/history", lambda: c.get(f"{P}/diagnosis/student/{sid}/history?limit=50")),
            ("GET /diagnosis/student/{id}/patterns", lambda: c.get(f"{P}/diagnosis/student/{sid}/patterns")),
            ("GET /analytics/student/{id}", lambda: c.get(f"{P}/analytics/student/{sid}")),
            ("GET /graph/full-graph", lambda: c.get(f"{P}/graph/full-graph")),
            ("GET /graph/concepts", lambda: c.get(f"{P}/graph/concepts")),
            ("GET /graph/concepts/{id}", lambda: c.get(f"{P}/graph/concepts/kinematics-1d")),
            ("GET /graph/concepts/{id}/chain", lambda: c.get(f"{P}/graph/concepts/kinematics-1d/chain")),
            ("GET /graph/concepts/{id}/gaps/{student}", lambda: c.get(f"{P}/graph/concepts/kinematics-1d/gaps/{sid}")),
            ("GET /retrieval/health", lambda: c.get(f"{P}/retrieval/health")),
            ("GET /students/404 (expected 404)", lambda: c.get(f"{P}/students/nonexistent-id-00000")),
        ]

        # Get a session ID if available
        r = await c.get(f"{P}/sessions/student/{sid}/all")
        sessions = r.json() if r.status_code == 200 else []
        if sessions:
            sess_id = sessions[0]["id"]
            sequential_tests.append(("GET /analytics/session/{id}", lambda: c.get(f"{P}/analytics/session/{sess_id}")))

        for name, fn in sequential_tests:
            for rep in range(3):
                r = await fn()
                ok = r.status_code < 500 and (r.status_code != 404 or "nonexistent" in name or "404" in name)
                if not ok:
                    check(f"{name} (rep {rep+1}) got {r.status_code}", False)
                    break
            else:
                check(f"{name} (3x)", True)

        # --------------------------------------------------
        # PHASE 2: Data integrity checks
        # --------------------------------------------------
        print("\n--- Phase 2: Data integrity checks ---")

        # Students
        r = await c.get(f"{P}/students/")
        slist = r.json()
        check(f"Students count >= 1", len(slist) >= 1)
        ids = [s["id"] for s in slist]
        check(f"All students have unique IDs", len(ids) == len(set(ids)))
        check(f"Student has name field", all("name" in s for s in slist))
        check(f"Student has grade field", all("grade" in s for s in slist))
        check(f"Boards present", len(set(s.get("board","") for s in slist)) >= 2)

        # Mastery
        r = await c.get(f"{P}/students/{sid}/mastery")
        m = r.json()
        check(f"Mastery has overall_score", "overall_score" in m)
        check(f"Mastery has subject_breakdown", "subject_breakdown" in m)
        check(f"Mastery has weak_topics", "weak_topics" in m)
        check(f"Mastery has strengths", "strengths" in m)

        # Questions
        r = await c.get(f"{P}/questions/app")
        aq = r.json()
        check(f"App questions >= 80", len(aq) >= 80)
        check(f"App Q has question_text", all("question_text" in q for q in aq))
        check(f"App Q has options", all("options" in q for q in aq))
        check(f"App Q spans 3 subjects", len(set(q.get("subject","") for q in aq)) >= 3)

        r = await c.get(f"{P}/questions/test")
        tq = r.json()
        check(f"Test questions == 50", len(tq) == 50)
        check(f"Test Q has year", all("year" in q for q in tq))

        # Sessions
        r = await c.get(f"{P}/sessions/student/{sid}/all")
        sess_list = r.json()
        check(f"Session count >= 5", len(sess_list) >= 5)
        check(f"Session has session_type", all("session_type" in s for s in sess_list))
        check(f"Session has questions_count", all("questions_count" in s for s in sess_list))
        has_practice = any(s.get("session_type") == "practice" for s in sess_list)
        has_assessment = any(s.get("session_type") == "assessment" for s in sess_list)
        check(f"Has practice sessions", has_practice)
        check(f"Has assessment sessions", has_assessment)

        # Graph
        r = await c.get(f"{P}/graph/full-graph")
        g = r.json()
        check(f"Graph has nodes >= 40", len(g.get("nodes", [])) >= 40)
        check(f"Graph has edges", len(g.get("edges", [])) > 0)

        r = await c.get(f"{P}/graph/concepts")
        clist = r.json()
        check(f"Concept list >= 40 items", len(clist) >= 40)

        # Analytics
        r = await c.get(f"{P}/analytics/student/{sid}")
        a = r.json()
        check(f"Analytics has overall_mastery", "overall_mastery" in a)
        check(f"Analytics has weak_topics", "weak_topics" in a)
        check(f"Analytics has strengths", "strengths" in a)
        check(f"Analytics has practice_recommendation", "practice_recommendation" in a)

        # --------------------------------------------------
        # PHASE 3: Practice flow
        # --------------------------------------------------
        print("\n--- Phase 3: Practice flow ---")

        concepts = ["kinematics-1d", "newtons-laws", "work-energy", "electrostatics", "thermodynamics"]

        for concept in concepts:
            sess_tag = f"stress-practice-{concept}-{int(time.time())}"
            r = await c.post(f"{P}/practice/generate", json={
                "student_id": sid,
                "session_id": sess_tag,
                "target_concept": concept,
                "error_category": "concept_misunderstood",
                "question_count": 5,
            })
            if r.status_code == 200:
                pr = r.json()
                pid = pr.get("practice_session_id")
                qs = pr.get("questions", [])
                check(f"Practice gen [{concept}] = {len(qs)} Qs", len(qs) > 0)

                if qs:
                    qid = qs[0]["id"]
                    r1 = await c.get(f"{P}/practice/hint/{qid}")
                    check(f"Hint [{concept}]", r1.status_code == 200)
                    r2 = await c.get(f"{P}/practice/explanation/{qid}")
                    check(f"Explanation [{concept}]", r2.status_code == 200)

                if pid and qs:
                    r3 = await c.post(f"{P}/practice/{pid}/result", json={
                        "student_id": sid,
                        "attempts": [
                            {"question_id": q["id"], "subtopic": "General",
                             "is_correct": i % 2 == 0, "response_time_seconds": 20 + i * 5,
                             "hints_used": 0, "retry_count": 0, "is_recurrence": False,
                             "subject": "Physics", "topic": "Practice"}
                            for i, q in enumerate(qs[:3])
                        ],
                    })
                    check(f"Practice result [{concept}]", r3.status_code == 200)
            else:
                check(f"Practice gen [{concept}]", False)

        # --------------------------------------------------
        # PHASE 4: Assessment flow
        # --------------------------------------------------
        print("\n--- Phase 4: Assessment flow ---")

        r = await c.post(f"{P}/assessment/", json={
            "student_id": sid, "subject": "physics",
            "topic": "Kinematics", "time_limit_minutes": 30,
        })
        check(f"Assessment create", r.status_code == 201)
        if r.status_code == 201:
            ar = r.json()
            aid = ar.get("id")
            qs = ar.get("questions", [])
            check(f"Assessment has questions", len(qs) >= 3)

            for q in qs:
                r = await c.post(f"{P}/assessment/{aid}/answer", json={
                    "question_id": q["id"], "student_answer": "B",
                    "response_time_seconds": 20,
                })
                check(f"Answer Q{q['id']}", r.status_code in (200, 201))

            r = await c.post(f"{P}/assessment/{aid}/complete")
            check(f"Assessment complete", r.status_code == 200)
            if r.status_code == 200:
                comp = r.json()
                check(f"Complete has score_percentage", "score_percentage" in comp)
                check(f"Complete has attempted > 0", comp.get("attempted", 0) > 0)

            r = await c.get(f"{P}/assessment/{aid}")
            check(f"Assessment GET", r.status_code == 200)

        # --------------------------------------------------
        # PHASE 5: Concurrent burst
        # --------------------------------------------------
        print("\n--- Phase 5: Concurrent burst (100 parallel reads) ---")
        burst_paths = [
            f"{P}/students/",
            f"{P}/students/{sid}/mastery",
            f"{P}/questions/app",
            f"{P}/questions/test",
            f"{P}/graph/full-graph",
            f"{P}/graph/concepts",
            f"{P}/diagnosis/student/{sid}/patterns",
            f"{P}/analytics/student/{sid}",
            "/health",
        ]
        tasks = [c.get(burst_paths[i % len(burst_paths)]) for i in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        ok = sum(1 for r in results if isinstance(r, httpx.Response) and r.status_code < 500)
        check(f"100 concurrent reads", ok >= 95)

        # --------------------------------------------------
        # PHASE 6: Heavy concurrent practice gen
        # --------------------------------------------------
        print(f"\n--- Phase 6: Concurrent practice gen (10x) ---")
        tasks = [
            c.post(f"{P}/practice/generate", json={
                "student_id": sid,
                "session_id": f"concurrent-{i}-{int(time.time())}",
                "target_concept": concepts[i % len(concepts)],
                "error_category": "concept_misunderstood",
                "question_count": 3,
            })
            for i in range(10)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        ok = sum(1 for r in results if isinstance(r, httpx.Response) and r.status_code == 200)
        check(f"10 concurrent practice gen", ok >= 8)

        # --------------------------------------------------
        # PHASE 7: Heavy concurrent assessments
        # --------------------------------------------------
        print(f"\n--- Phase 7: Concurrent assessments (5x) ---")
        topics = ["Kinematics", "Laws of Motion", "Work Energy Power", "Electrostatics", "Thermodynamics"]
        tasks = [
            c.post(f"{P}/assessment/", json={
                "student_id": sid, "subject": "physics",
                "topic": topics[i], "time_limit_minutes": 30,
            })
            for i in range(5)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        ok = sum(1 for r in results if isinstance(r, httpx.Response) and r.status_code == 201)
        check(f"5 concurrent assessment creates", ok >= 3)

        # --------------------------------------------------
        # PHASE 8: Mixed workload
        # --------------------------------------------------
        print(f"\n--- Phase 8: Mixed workload (30 requests, varied types) ---")
        mixed_tasks = []
        for i in range(30):
            choice = i % 6
            if choice == 0:
                mixed_tasks.append(c.get(f"{P}/students/"))
            elif choice == 1:
                mixed_tasks.append(c.get(f"{P}/questions/app"))
            elif choice == 2:
                mixed_tasks.append(c.get(f"{P}/graph/full-graph"))
            elif choice == 3:
                mixed_tasks.append(c.get(f"{P}/analytics/student/{sid}"))
            elif choice == 4:
                mixed_tasks.append(c.get(f"{P}/diagnosis/student/{sid}/patterns"))
            else:
                mixed_tasks.append(c.get("/health"))
        results = await asyncio.gather(*mixed_tasks, return_exceptions=True)
        ok = sum(1 for r in results if isinstance(r, httpx.Response) and r.status_code < 500)
        check(f"30 mixed requests", ok >= 28)

        # --------------------------------------------------
        # PHASE 9: Student CRUD
        # --------------------------------------------------
        print(f"\n--- Phase 9: Student CRUD ---")
        r = await c.post(f"{P}/students/", json={
            "name": "Stress Test User",
            "grade": "12", "board": "CBSE",
            "exam_target": "JEE Advanced 2026",
            "language": "english",
        })
        check(f"Student create", r.status_code in (200, 201))
        new_id = r.json().get("id", "") if r.status_code in (200, 201) else ""

        if new_id:
            r = await c.get(f"{P}/students/{new_id}")
            check(f"Student GET new", r.status_code == 200)

            r = await c.put(f"{P}/students/{new_id}", json={
                "name": "Stress Test Updated",
                "grade": "12", "board": "CBSE",
            })
            check(f"Student update", r.status_code in (200, 201))

            r = await c.delete(f"{P}/students/{new_id}")
            check(f"Student delete", r.status_code in (200, 204))

    # --------------------------------------------------
    # RESULTS
    # --------------------------------------------------
    elapsed = time.time() - start
    total = passed + failed
    print(f"\n{'=' * 70}")
    print(f"  FINAL RESULTS: {passed}/{total} passed, {failed} failed")
    print(f"  Duration: {elapsed:.1f}s")
    if errors:
        print(f"\n  FAILURES ({len(errors)}):")
        for e in errors:
            print(f"    - {e}")
    rate = passed / total * 100 if total else 0
    print(f"  Success rate: {rate:.1f}%")
    print(f"{'=' * 70}")
    return failed == 0

if __name__ == "__main__":
    ok = asyncio.run(stress_test())
    sys.exit(0 if ok else 1)

