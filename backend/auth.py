"""
Legacy CLI entry point. Prefer the FastAPI server:

    uvicorn backend.main:app --reload --port 8000
"""

from backend.database import init_db
from backend.schemas import LoginRequest, SignupRequest
from backend.services.auth_service import login_user, signup_user


def _run_cli() -> None:
    init_db()
    print("\n========== GRAPH RAG AUTH (CLI) ==========\n")
    print("1. Sign Up")
    print("2. Login")
    choice = input("\nEnter choice: ")

    if choice == "1":
        username = input("Enter username: ")
        email = input("Enter email: ")
        password = input("Enter password: ")
        user, _ = signup_user(SignupRequest(username=username, email=email, password=password))
        print(f"\nSignup successful. Welcome {user.username}")
    elif choice == "2":
        email = input("Enter email: ")
        password = input("Enter password: ")
        user, _ = login_user(LoginRequest(email=email, password=password))
        print(f"\nLogin successful. Welcome back {user.username}")
    else:
        print("\nInvalid option.")


if __name__ == "__main__":
    _run_cli()
