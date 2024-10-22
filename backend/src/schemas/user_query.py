from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserQuery(BaseModel):
    query: str = Field(..., description="The user's query text")


class UserQueryDB(BaseModel):
    id: int = Field(..., description="The unique identifier for the user query")
    task_id: str = Field(..., description="The ID of the associated task")
    origin_query: str = Field(..., description="The original query text")

    class Config:
        from_attributes = True


class UserQueryCreate(BaseModel):
    id: int = Field(..., description="The unique identifier for the user query")
    task_id: str = Field(..., description="The ID of the associated task")
    origin_query: str = Field(..., description="The original query text")
    created_at: datetime = Field(..., description="The creation timestamp of the user query")

    class Config:
        from_attributes = True


class UserQueryUpdate(BaseModel):
    query: Optional[str] = Field(None, description="Updated query text")
    task_id: Optional[str] = Field(None, description="Updated task ID")


class UserQueryInDB(UserQueryDB):
    pass
