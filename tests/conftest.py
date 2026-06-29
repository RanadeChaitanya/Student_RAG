import uuid
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from suraj_dada.config.loader import get_config
from suraj_dada.database.models import AppQuestion, Base, MasteryScore, Student
from suraj_dada.embeddings.generator import EmbeddingGenerator
from suraj_dada.embeddings.service import EmbeddingService
from suraj_dada.embeddings.storage import VectorStoreService
from suraj_dada.graph.store import ConceptGraphStore
from suraj_dada.question_bank.app_questions import AppQuestionService
from suraj_dada.student.mastery import MasteryService
from suraj_dada.student.profile import StudentProfileService
from suraj_dada.student.session_memory import SessionMemoryService


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(db_session):
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.fixture
def config():
    return get_config()


@pytest.fixture
def concept_graph():
    store = ConceptGraphStore()
    store._nodes = {
        "newtons-laws": type(
            "obj",
            (),
            {
                "id": "newtons-laws",
                "subject": "Physics",
                "topic": "Laws of Motion",
                "subtopic": "Newton's Laws",
                "display_name": "Newton's Laws",
                "difficulty": 2,
                "prerequisites": [],
            },
        )(),
        "kinematics-1d": type(
            "obj",
            (),
            {
                "id": "kinematics-1d",
                "subject": "Physics",
                "topic": "Kinematics",
                "subtopic": "Motion in 1D",
                "display_name": "Kinematics 1D",
                "difficulty": 2,
                "prerequisites": [],
            },
        )(),
    }
    return store


@pytest_asyncio.fixture
async def seeded_db(session_factory):
    async with session_factory() as session:
        s = Student(
            id=str(uuid.uuid4()),
            name="Test Student",
            grade="12",
            board="CBSE",
            exam_target="JEE Advanced 2026",
            language="english",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(s)
        ms = MasteryScore(
            student_id=s.id,
            subject="Physics",
            topic="Kinematics",
            subtopic="Motion in 1D",
            score=45.0,
            confidence=0.6,
            attempts=3,
            last_updated=datetime.now(UTC),
        )
        session.add(ms)
        ms2 = MasteryScore(
            student_id=s.id,
            subject="Physics",
            topic="Laws of Motion",
            subtopic="Newton's Laws",
            score=70.0,
            confidence=0.7,
            attempts=2,
            last_updated=datetime.now(UTC),
        )
        session.add(ms2)
        q = AppQuestion(
            id=1,
            subject="physics",
            topic="kinematics",
            subtopic="motion in 1d",
            difficulty=2,
            question_type="mcq",
            question_text="Test?",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
            correct_answer="A",
            explanation="test",
            tags="",
            source="test",
            is_active=True,
            created_at=datetime.now(UTC),
        )
        session.add(q)
        await session.commit()
        yield session, s.id


@pytest_asyncio.fixture
async def student_profile(session_factory):
    return StudentProfileService(session_factory)


@pytest_asyncio.fixture
async def mastery_service(session_factory, config):
    return MasteryService(session_factory, config)


@pytest_asyncio.fixture
async def session_memory(session_factory):
    return SessionMemoryService(session_factory)


@pytest_asyncio.fixture
async def app_questions(session_factory):
    return AppQuestionService(session_factory)


@pytest_asyncio.fixture
def embedding_service(tmp_path):
    gen = EmbeddingGenerator(dimension=64)
    store = VectorStoreService(dimension=64, index_path=str(tmp_path / "test_index.bin"))
    return EmbeddingService(gen, store)
