from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.exception_handlers import register_exception_handlers
from app.helpers.all_routers import include_routers
from app.helpers.database import engine
from app.models.db import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Quiz Engine", lifespan=lifespan)

register_exception_handlers(app)
include_routers(app)
