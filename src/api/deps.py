from fastapi import Depends

from src.services.database_service import DatabaseService
from src.services.openai_service import OpenAIService
from src.services.problem_analyzer import ProblemAnalyzer


def get_openai_service() -> OpenAIService:
    return OpenAIService()


def get_db_service() -> DatabaseService:
    return DatabaseService()


def get_problem_analyzer(
        openai_service: OpenAIService = Depends(get_openai_service),
        db_service: DatabaseService = Depends(get_db_service)
) -> ProblemAnalyzer:
    return ProblemAnalyzer(openai_service, db_service)
