import pytest

from suraj_dada.schemas.session import AttemptCreate


class TestSessionMemory:
    @pytest.mark.asyncio
    async def test_start_session(self, session_memory, seeded_db):
        _, sid = seeded_db
        session = await session_memory.start_session(sid, "practice")
        assert session.student_id == sid
        assert session.session_type == "practice"
        assert session.id is not None

    @pytest.mark.asyncio
    async def test_end_session(self, session_memory, seeded_db):
        _, sid = seeded_db
        session = await session_memory.start_session(sid, "test")
        ended = await session_memory.end_session(session.id)
        assert ended.ended_at is not None

    @pytest.mark.asyncio
    async def test_record_attempt(self, session_memory, seeded_db):
        _, sid = seeded_db
        session = await session_memory.start_session(sid, "practice")
        data = AttemptCreate(
            question_id=1,
            question_type="app",
            is_correct=True,
            response_time_seconds=15.0,
            hints_used=0,
            session_id=session.id,
        )
        attempt = await session_memory.record_attempt(session.id, data)
        assert attempt.question_id == 1
        assert attempt.is_correct is True

    @pytest.mark.asyncio
    async def test_get_session(self, session_memory, seeded_db):
        _, sid = seeded_db
        session = await session_memory.start_session(sid, "practice")
        fetched = await session_memory.get_session(session.id)
        assert fetched.id == session.id

    @pytest.mark.asyncio
    async def test_get_active_sessions(self, session_memory, seeded_db):
        _, sid = seeded_db
        await session_memory.start_session(sid, "practice")
        active = await session_memory.get_active_sessions(sid)
        assert len(active) >= 1
