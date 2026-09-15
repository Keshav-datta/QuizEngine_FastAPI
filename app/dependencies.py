from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.helpers.database import get_db
from app.helpers.security import decode_access_token
from app.models.db.user import User,UserRole
from app.repositories.attempt_repository import AttemptRepo
from app.repositories.leaderboard_repository import LeaderboardRepo
from app.repositories.question_repository import QuestionRepo
from app.repositories.quiz_repository import QuizRepo
from app.repositories.user_repository import UserRepo
from app.services.attempt_service import AttemptService
from app.services.auth_service import AuthService
from app.services.leaderboard_service import LeaderboardService
from app.services.question_service import QuestionService
from app.services.quiz_service import QuizService
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
db_dependency = Annotated[AsyncSession, Depends(get_db)]


def get_user_repo(db: db_dependency):
    return UserRepo(db)


def get_quiz_repo(db: db_dependency):
    return QuizRepo(db)


def get_question_repo(db: db_dependency):
    return QuestionRepo(db)


def get_attempt_repo(db: db_dependency):
    return AttemptRepo(db)


def get_leaderboard_repo(db: db_dependency):
    return LeaderboardRepo(db)


def get_auth_service(user_repo: UserRepo = Depends(get_user_repo)):
    return AuthService(user_repo)


def get_quiz_service(
    quiz_repo: QuizRepo = Depends(get_quiz_repo),
    question_repo: QuestionRepo = Depends(get_question_repo)
):
    return QuizService(quiz_repo, question_repo)


def get_question_service(
    question_repo: QuestionRepo = Depends(get_question_repo),
    quiz_repo: QuizRepo = Depends(get_quiz_repo)
):
    return QuestionService(question_repo, quiz_repo)


def get_attempt_service(
    attempt_repo: AttemptRepo = Depends(get_attempt_repo),
    quiz_repo: QuizRepo = Depends(get_quiz_repo),
    question_repo: QuestionRepo = Depends(get_question_repo)
):
    return AttemptService(attempt_repo, quiz_repo, question_repo)


def get_leaderboard_service(
    repo: LeaderboardRepo = Depends(get_leaderboard_repo),
    quiz_repo: QuizRepo = Depends(get_quiz_repo)
):
    return LeaderboardService(repo, quiz_repo)

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repo: UserRepo = Depends(get_user_repo)
) -> User:
    try:
        payload = decode_access_token(token)
        public_id = UUID(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        ) from exc

    user = await user_repo.get_by_public_id(public_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists"
        )

    return user


async def get_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user
