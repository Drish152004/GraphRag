from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
from jose import jwt

from backend.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, SECRET_KEY
from backend.database import get_cursor
from backend.schemas import LoginRequest, SignupRequest, UserResponse


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))


def _create_access_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def signup_user(data: SignupRequest) -> tuple[UserResponse, str]:
    with get_cursor(dict_cursor=True) as (conn, cur):
        cur.execute("SELECT id FROM users WHERE email = %s", (str(data.email),))
        if cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        hashed = _hash_password(data.password)
        cur.execute(
            """
            INSERT INTO users (username, email, password)
            VALUES (%s, %s, %s)
            RETURNING id, username, email
            """,
            (data.username, str(data.email), hashed),
        )
        row = cur.fetchone()
        conn.commit()

    user = UserResponse(id=row["id"], username=row["username"], email=row["email"])
    token = _create_access_token(user.id, str(user.email))
    return user, token


def login_user(data: LoginRequest) -> tuple[UserResponse, str]:
    with get_cursor(dict_cursor=True) as (_, cur):
        cur.execute(
            """
            SELECT id, username, email, password
            FROM users
            WHERE email = %s
            """,
            (str(data.email),),
        )
        row = cur.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not _verify_password(data.password, row["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    user = UserResponse(id=row["id"], username=row["username"], email=row["email"])
    token = _create_access_token(user.id, str(user.email))
    return user, token
