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

# Uvicorn logging is configured in the LOGGING_CONFIG below

from fastapi import FastAPI
from src.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes.user_queries_routes import router as user_queries_router
from src.api.routes.tasks_routes import router as tasks_router
from src.api.routes.task_context_routes import router as task_context_router
from src.api.routes.util_routes import router as util_router

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
    level=logging.INFO,  # Enable INFO level to see uvicorn access logs
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

# Configure uvicorn access log to use our format
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.setLevel(logging.INFO)

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
app.include_router(user_queries_router, prefix="/api/v1/user-queries", tags=["User Queries"])
app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(task_context_router, prefix="/api/v1/tasks", tags=["Task Context"])
app.include_router(util_router, prefix="/api/v1/utils", tags=["Utilities"])
# Add other routes as needed

if __name__ == "__main__":
    # Custom logging configuration for uvicorn
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "access": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        },
    }

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=LOGGING_CONFIG,
        access_log=True
    )
