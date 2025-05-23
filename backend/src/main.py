# backend/src/main.py
import sys
import os
from pathlib import Path
import nest_asyncio  # type: ignore

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from fastapi import FastAPI
from src.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import user_queries_routes, tasks_routes, util_routes

import logging
import uvicorn

# Configure basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS configuration
origins = settings.FRONTEND_CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(user_queries_routes.router, prefix="/user-queries", tags=["User Queries"])
app.include_router(tasks_routes.router, prefix="/tasks", tags=["Tasks"])
app.include_router(util_routes.router, prefix="/utils", tags=["Utilities"])
# Add other routes as needed

# Startup event to log application start
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 FastAPI application started successfully")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
