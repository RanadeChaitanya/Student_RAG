from fastapi import APIRouter, HTTPException, Request

from studob.auth.service import AuthService
from studob.database.models import Student as StudentModel

router = APIRouter()


@router.post("/login")
async def login(request: Request, data: dict):
    name = data.get("name", "").strip()
    pin = data.get("pin", "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Name is required")

    db = request.app.state.context.db_engine
    async with db.get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(StudentModel).where(StudentModel.name == name)
        )
        student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=401, detail="Student not found")

    default_pin = getattr(student, "pin", "1234")
    if pin and pin != default_pin:
        raise HTTPException(status_code=401, detail="Invalid PIN")

    token = AuthService.create_token(student.id)
    return {
        "token": token,
        "student": {
            "id": student.id,
            "name": student.name,
            "grade": student.grade,
            "board": student.board,
            "exam_target": student.exam_target,
            "language": student.language,
        },
    }


@router.post("/verify")
async def verify_token(request: Request):
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    student_id = AuthService.validate_token(token)
    if not student_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"valid": True, "student_id": student_id}


@router.post("/logout")
async def logout(request: Request):
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""
    if token:
        AuthService.revoke_token(token)
    return {"ok": True}
