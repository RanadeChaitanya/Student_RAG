import pytest

from suraj_dada.exceptions import NotFoundError
from suraj_dada.schemas.student import StudentCreate


class TestStudentProfile:
    async def test_create_student(self, student_profile):
        data = StudentCreate(
            name="New Student",
            grade="12",
            board="CBSE",
            exam_target="JEE Advanced",
            language="english",
        )
        result = await student_profile.create_student(data)
        assert result.name == "New Student"
        assert result.id is not None

    async def test_get_student_not_found(self, student_profile):
        with pytest.raises(NotFoundError):
            await student_profile.get_student("nonexistent")

    async def test_list_students(self, student_profile, seeded_db):
        students = await student_profile.list_students()
        assert len(students) >= 1

    async def test_get_student_by_name_found(self, student_profile, seeded_db):
        _, sid = seeded_db
        result = await student_profile.get_student(sid)
        assert result is not None
        assert result.name == "Test Student"

    async def test_get_student_by_name_nonexistent(self, student_profile):
        result = await student_profile.get_student_by_name("Nobody")
        assert result is None

    async def test_update_student(self, student_profile, seeded_db):
        _, sid = seeded_db
        from suraj_dada.schemas.student import StudentUpdate

        updated = await student_profile.update_student(sid, StudentUpdate(grade="12 Pass"))
        assert updated.grade == "12 Pass"

    async def test_delete_student(self, student_profile, seeded_db, session_factory):
        _, sid = seeded_db
        await student_profile.delete_student(sid)
        with pytest.raises(NotFoundError):
            await student_profile.get_student(sid)
