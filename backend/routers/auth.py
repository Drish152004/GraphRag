from fastapi import APIRouter

from backend.schemas import AuthResponse, LoginRequest, SignupRequest
from backend.services.auth_service import login_user, signup_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
def signup(payload: SignupRequest) -> AuthResponse:
    user, token = signup_user(payload)
    return AuthResponse(
        message="Signup successful.",
        access_token=token,
        user=user,
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    user, token = login_user(payload)
    return AuthResponse(
        message="Login successful.",
        access_token=token,
        user=user,
    )
