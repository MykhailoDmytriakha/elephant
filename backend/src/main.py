# backend/src/main.py
import sys
import os
from pathlib import Path
import nest_asyncio  # type: ignore
from contextlib import asynccontextmanager

# Apply nest_asyncio to allow nested event loops
# nest_asyncio.apply()

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Configure LiteLLM logging level to reduce verbosity
os.environ.setdefault("LITELLM_LOG", "ERROR")

# Disable Google ADK verbose logging
os.environ.setdefault("GOOGLE_ADK_LOG_LEVEL", "ERROR")
os.environ.setdefault("GOOGLE_CLOUD_LOG_LEVEL", "ERROR")

# Disable function call tracing and schema logging
os.environ.setdefault("ADK_DISABLE_FUNCTION_TRACE", "false")
os.environ.setdefault("ADK_DISABLE_SCHEMA_LOG", "true")

from fastapi import FastAPI
from src.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import user_queries_routes, tasks_routes, util_routes

import logging
import uvicorn

# Import litellm to configure it globally
try:
    import litellm
    litellm.set_verbose = False  # Disable verbose logging globally
except ImportError:
    pass  # litellm might not be available in all environments

# Configure basic logging
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO to WARNING to reduce verbosity
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

# Disable specific loggers that are too verbose
logging.getLogger("LiteLLM").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("litellm").setLevel(logging.ERROR)

# Disable Google ADK verbose logging
logging.getLogger("google.adk").setLevel(logging.ERROR)
logging.getLogger("google").setLevel(logging.ERROR)

# Keep only essential application logs
logging.getLogger("src.main").setLevel(logging.INFO)
logging.getLogger("uvicorn").setLevel(logging.WARNING)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("🚀 FastAPI application started successfully")
    yield
    # Shutdown logic (if needed)
    logger.info("📊 FastAPI application shutdown completed")

app = FastAPI(lifespan=lifespan)

# CORS configuration
origins = settings.cors_origins

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
