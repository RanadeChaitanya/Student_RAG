import secrets
import time
from collections import defaultdict

_STORE: dict[str, dict] = {}  # token -> {student_id, created_at}


class AuthService:
    SECRET_LENGTH = 32
    TOKEN_TTL = 86400 * 7  # 7 days

    @classmethod
    def create_token(cls, student_id: str) -> str:
        token = secrets.token_hex(cls.SECRET_LENGTH)
        _STORE[token] = {"student_id": student_id, "created_at": time.time()}
        return token

    @classmethod
    def validate_token(cls, token: str) -> str | None:
        data = _STORE.get(token)
        if not data:
            return None
        if time.time() - data["created_at"] > cls.TOKEN_TTL:
            del _STORE[token]
            return None
        return data["student_id"]

    @classmethod
    def revoke_token(cls, token: str) -> None:
        _STORE.pop(token, None)
