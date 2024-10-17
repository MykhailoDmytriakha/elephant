from fastapi import FastAPI

from src.api.routes import tasks, user_queries
from src.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(user_queries.router, prefix="/user-queries", tags=["user-queries"])


@app.get("/")
async def root():
    return {"message": "Welcome to the Elephant API"}
