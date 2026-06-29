import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .engine import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _uuid() -> str:
    return str(uuid.uuid4())


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    grade: Mapped[str] = mapped_column(String(50), nullable=False)
    exam_target: Mapped[str | None] = mapped_column(String(255), nullable=True)
    board: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="english")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    mastery_scores: Mapped[list["MasteryScore"]] = relationship(
        "MasteryScore", back_populates="student", cascade="all, delete-orphan"
    )
    attempts: Mapped[list["Attempt"]] = relationship(
        "Attempt", back_populates="student", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="student", cascade="all, delete-orphan"
    )
    mistake_records: Mapped[list["MistakeRecord"]] = relationship(
        "MistakeRecord", back_populates="student", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Student(id={self.id!r}, name={self.name!r}, grade={self.grade!r})>"


class MasteryScore(Base):
    __tablename__ = "mastery_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    subtopic: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    student: Mapped["Student"] = relationship("Student", back_populates="mastery_scores")

    def __repr__(self) -> str:
        return f"<MasteryScore(id={self.id}, student_id={self.student_id!r}, subject={self.subject!r}, topic={self.topic!r}, subtopic={self.subtopic!r}, score={self.score})>"  # noqa: E501


class AppQuestion(Base):
    __tablename__ = "app_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    subtopic: Mapped[str] = mapped_column(String(255), nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str] = mapped_column(String(500), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="app")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    def __repr__(self) -> str:
        return f"<AppQuestion(id={self.id}, subject={self.subject!r}, topic={self.topic!r}, difficulty={self.difficulty})>"  # noqa: E501


class TestQuestion(Base):
    __tablename__ = "test_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    subtopic: Mapped[str] = mapped_column(String(255), nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str] = mapped_column(String(500), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    exam_type: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    def __repr__(self) -> str:
        return f"<TestQuestion(id={self.id}, subject={self.subject!r}, exam_type={self.exam_type!r}, year={self.year})>"  # noqa: E501


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    response_time_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    hints_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    answered_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    student: Mapped["Student"] = relationship("Student", back_populates="attempts")

    def __repr__(self) -> str:
        return f"<Attempt(id={self.id}, student_id={self.student_id!r}, question_id={self.question_id}, is_correct={self.is_correct})>"  # noqa: E501


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    session_type: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    questions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mastery_delta: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    student: Mapped["Student"] = relationship("Student", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session(id={self.id!r}, student_id={self.student_id!r}, session_type={self.session_type!r})>"  # noqa: E501


class MistakeRecord(Base):
    __tablename__ = "mistake_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    question_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    error_category: Mapped[str] = mapped_column(String(100), nullable=False)
    concept_tag: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    diagnosis_detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    student: Mapped["Student"] = relationship("Student", back_populates="mistake_records")

    def __repr__(self) -> str:
        return f"<MistakeRecord(id={self.id}, student_id={self.student_id!r}, error_category={self.error_category!r}, concept_tag={self.concept_tag!r})>"  # noqa: E501


class ConceptNode(Base):
    __tablename__ = "concept_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    subtopic: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    prerequisites: Mapped[list | None] = mapped_column(JSON, nullable=True)
    difficulty: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    misconceptions: Mapped[list["Misconception"]] = relationship(
        "Misconception", back_populates="concept", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ConceptNode(id={self.id}, display_name={self.display_name!r}, subject={self.subject!r}, topic={self.topic!r})>"  # noqa: E501


class Misconception(Base):
    __tablename__ = "misconceptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concept_id: Mapped[int] = mapped_column(Integer, ForeignKey("concept_nodes.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    error_pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    related_error_categories: Mapped[list | None] = mapped_column(JSON, nullable=True)

    concept: Mapped["ConceptNode"] = relationship("ConceptNode", back_populates="misconceptions")

    def __repr__(self) -> str:
        return f"<Misconception(id={self.id}, concept_id={self.concept_id}, error_pattern={self.error_pattern!r})>"  # noqa: E501
