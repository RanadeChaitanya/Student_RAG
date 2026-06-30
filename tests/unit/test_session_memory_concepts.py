import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from studob.database.models import AppQuestion, Attempt, Base, Session, Student
from studob.student.session_memory import SessionMemoryService


@pytest.mark.asyncio
async def test_get_recent_concepts_returns_subtopic_names():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        student_id = str(uuid.uuid4())
        session.add(
            Student(
                id=student_id,
                name="Test",
                grade="12",
                board="CBSE",
                language="english",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        session.add(
            AppQuestion(
                id=100,
                subject="Physics",
                topic="Kinematics",
                subtopic="Motion in 1D",
                difficulty=2,
                question_type="mcq",
                question_text="Q",
                options={},
                correct_answer="A",
                explanation="E",
                tags="",
                source="test",
                is_active=True,
                created_at=datetime.now(UTC),
            )
        )
        session.add(
            AppQuestion(
                id=101,
                subject="Physics",
                topic="Kinematics",
                subtopic="Motion in 2D",
                difficulty=3,
                question_type="mcq",
                question_text="Q2",
                options={},
                correct_answer="B",
                explanation="E2",
                tags="",
                source="test",
                is_active=True,
                created_at=datetime.now(UTC),
            )
        )
        sess_id = str(uuid.uuid4())
        session.add(
            Session(
                id=sess_id,
                student_id=student_id,
                session_type="practice",
                started_at=datetime.now(UTC),
            )
        )
        session.add(
            Attempt(
                student_id=student_id,
                question_id=100,
                question_type="mcq",
                is_correct=True,
                session_id=sess_id,
                answered_at=datetime.now(UTC),
            )
        )
        session.add(
            Attempt(
                student_id=student_id,
                question_id=101,
                question_type="mcq",
                is_correct=False,
                session_id=sess_id,
                answered_at=datetime.now(UTC),
            )
        )
        await session.commit()

    svc = SessionMemoryService(factory)
    concepts = await svc.get_recent_concepts(student_id, limit=5)

    assert isinstance(concepts, list)
    assert len(concepts) > 0
    assert "Motion in 1D" in concepts or "Motion in 2D" in concepts
    assert all(isinstance(c, str) for c in concepts)
    assert not any(c.isdigit() for c in concepts)

    await engine.dispose()
