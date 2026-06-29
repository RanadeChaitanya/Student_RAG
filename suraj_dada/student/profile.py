import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from suraj_dada.database.models import Student
from suraj_dada.exceptions import NotFoundError
from suraj_dada.logging_setup import get_logger
from suraj_dada.schemas.student import StudentCreate, StudentResponse, StudentUpdate

logger = get_logger("student.profile")


class StudentProfileService:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def create_student(self, data: StudentCreate) -> StudentResponse:
        async with self._session_factory() as session:
            session: AsyncSession
            student = Student(
                id=str(uuid.uuid4()),
                name=data.name,
                grade=data.grade,
                exam_target=data.exam_target,
                board=data.board,
                language=data.language or "english",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            session.add(student)
            await session.commit()
            await session.refresh(student)
            logger.info("Created student", extra={"student_id": student.id})
            return StudentResponse.model_validate(student)

    async def get_student(self, student_id: str) -> StudentResponse:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(select(Student).where(Student.id == student_id))
            student = result.scalar_one_or_none()
            if student is None:
                raise NotFoundError("Student", student_id)
            return StudentResponse.model_validate(student)

    async def update_student(self, student_id: str, data: StudentUpdate) -> StudentResponse:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(select(Student).where(Student.id == student_id))
            student = result.scalar_one_or_none()
            if student is None:
                raise NotFoundError("Student", student_id)
            update_dict = data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(student, key, value)
            student.updated_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(student)
            logger.info("Updated student", extra={"student_id": student_id})
            return StudentResponse.model_validate(student)

    async def delete_student(self, student_id: str) -> None:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(select(Student).where(Student.id == student_id))
            student = result.scalar_one_or_none()
            if student is None:
                raise NotFoundError("Student", student_id)
            await session.delete(student)
            await session.commit()
            logger.info("Deleted student", extra={"student_id": student_id})

    async def list_students(self) -> list[StudentResponse]:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(select(Student))
            students = result.scalars().all()
            return [StudentResponse.model_validate(s) for s in students]

    async def get_student_by_name(self, name: str) -> StudentResponse | None:
        async with self._session_factory() as session:
            session: AsyncSession
            result = await session.execute(select(Student).where(Student.name == name))
            student = result.scalar_one_or_none()
            if student is None:
                return None
            return StudentResponse.model_validate(student)
