from fastapi import Depends

from src.services.openai_service import OpenAIService
from src.services.problem_analyzer import ProblemAnalyzer
from src.services.file_storage_service import FileStorageService


def get_openai_service() -> OpenAIService:
    return OpenAIService()


def get_file_storage_service() -> FileStorageService:
    return FileStorageService()


def get_problem_analyzer(
        openai_service: OpenAIService = Depends(get_openai_service),
        storage_service: FileStorageService = Depends(get_file_storage_service)
) -> ProblemAnalyzer:
    return ProblemAnalyzer(openai_service, storage_service)
