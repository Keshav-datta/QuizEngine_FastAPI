from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: UUID
    name: str
    score: float
    submitted_at: datetime
