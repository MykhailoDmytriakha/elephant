from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class QueryStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UserQuery(BaseModel):
    query: str


class UserQueryCreate(UserQuery):
    id: int
    task_id: str
    status: QueryStatus
    created_at: datetime
    progress: int


class UserQueryDB(UserQueryCreate):
    pass


class UserQueryUpdate(BaseModel):
    query: Optional[str] = Field(None, description="Updated query text")
    task_id: Optional[str] = Field(None, description="Updated task ID")


class UserQueryInDB(UserQueryDB):
    pass
