import pytest

from studob.exceptions import NotFoundError


class TestMasteryService:
    async def test_get_mastery_summary(self, mastery_service, seeded_db):
        session, sid = seeded_db
        summary = await mastery_service.get_mastery_summary(sid)
        assert summary.student_id == sid
        assert 0 <= summary.overall_score <= 100
        assert len(summary.weak_topics) >= 0
        assert len(summary.strengths) >= 0

    async def test_update_mastery_new_topic(self, mastery_service, seeded_db, session_factory):
        _, sid = seeded_db
        signals = {
            "correctness": 1.0,
            "response_time_ratio": 0.5,
            "hints_used_count": 0,
            "retry_count": 0,
            "recurrence_flag": 0,
            "subject": "Chemistry",
            "topic": "Mole Concept",
        }
        updated = await mastery_service.update_mastery(sid, "Mole Concept", signals)
        assert updated.score > 0

    async def test_update_mastery_correct_boost(self, mastery_service, seeded_db):
        _, sid = seeded_db
        signals = {
            "correctness": 1.0,
            "response_time_ratio": 0.3,
            "hints_used_count": 0,
            "retry_count": 0,
            "recurrence_flag": 0,
            "subject": "Physics",
            "topic": "Kinematics",
        }
        updated = await mastery_service.update_mastery(sid, "Motion in 1D", signals)
        assert updated.score > 45.0

    async def test_update_mastery_wrong_penalty(self, mastery_service, seeded_db):
        _, sid = seeded_db
        signals = {
            "correctness": 0.0,
            "response_time_ratio": 2.0,
            "hints_used_count": 3,
            "retry_count": 2,
            "recurrence_flag": 1,
            "subject": "Physics",
            "topic": "Kinematics",
        }
        updated = await mastery_service.update_mastery(sid, "Motion in 1D", signals)
        assert updated.score < 45.0

    async def test_identify_weak_topics(self, mastery_service, seeded_db):
        _, sid = seeded_db
        weak = await mastery_service.identify_weak_topics(sid)
        assert isinstance(weak, list)

    async def test_get_mastery_not_found(self, mastery_service):
        with pytest.raises(NotFoundError):
            await mastery_service.get_mastery("nonexistent", "Motion in 1D")
