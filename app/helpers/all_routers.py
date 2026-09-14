from fastapi import FastAPI

from app.routers.attempt import router as attempt_router
from app.routers.auth import router as auth_router
from app.routers.leaderboard import router as leaderboard_router
from app.routers.question import router as question_router
from app.routers.quiz import router as quiz_router
from app.routers.user import router as user_router

routers = [
    (auth_router, "/auth", ["Auth"]),
    (user_router, "/users", ["Users"]),
    (quiz_router, "/quizzes", ["Quizzes"]),
    (question_router, "", ["Questions"]),
    (attempt_router, "", ["Attempts"]),
    (leaderboard_router, "", ["Leaderboard"]),
]


def include_routers(app: FastAPI):
    for router, prefix, tags in routers:
        app.include_router(router, prefix=prefix, tags=tags)
