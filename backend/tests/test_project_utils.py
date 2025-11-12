# backend/tests/test_project_utils.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
from src.utils.project_utils import generate_project_name
from src.services.openai_service import OpenAIService


@pytest.fixture
def mock_openai_service():
    """Mock OpenAI service."""
    service = MagicMock(spec=OpenAIService)
    service.generate_completion = AsyncMock()
    return service


@pytest.fixture
def temp_base_dir():
    """Create a temporary directory for testing."""
    import tempfile
    import shutil
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


class TestProjectUtils:

    @pytest.mark.asyncio
    async def test_generate_project_name_basic(self, mock_openai_service, temp_base_dir):
        """Test basic project name generation."""
        # Mock AI response
        mock_openai_service.generate_completion.return_value = "web_scraper_tool"

        name = await generate_project_name(
            "Create a web scraper tool",
            mock_openai_service,
            temp_base_dir
        )

        assert name == "web_scraper_tool"
        mock_openai_service.generate_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_project_name_with_collision(self, mock_openai_service, temp_base_dir):
        """Test name collision handling with numbering."""
        # Mock AI response
        mock_openai_service.generate_completion.return_value = "test_project"

        # Create existing directory
        (temp_base_dir / "test_project").mkdir()

        name = await generate_project_name(
            "Test project",
            mock_openai_service,
            temp_base_dir
        )

        assert name == "test_project_2"

    @pytest.mark.asyncio
    async def test_generate_project_name_multiple_collisions(self, mock_openai_service, temp_base_dir):
        """Test multiple collision handling."""
        # Mock AI response
        mock_openai_service.generate_completion.return_value = "test_project"

        # Create existing directories
        (temp_base_dir / "test_project").mkdir()
        (temp_base_dir / "test_project_2").mkdir()
        (temp_base_dir / "test_project_3").mkdir()

        name = await generate_project_name(
            "Test project",
            mock_openai_service,
            temp_base_dir
        )

        assert name == "test_project_4"

    @pytest.mark.asyncio
    async def test_generate_project_name_special_characters(self, mock_openai_service, temp_base_dir):
        """Test handling of special characters in AI response."""
        # Mock AI response with special characters
        mock_openai_service.generate_completion.return_value = "Build #1 app @ 2025!"

        name = await generate_project_name(
            "Build app",
            mock_openai_service,
            temp_base_dir
        )

        assert name == "build_1_app_2025"

    @pytest.mark.asyncio
    async def test_generate_project_name_cyrillic_input(self, mock_openai_service, temp_base_dir):
        """Test handling of Cyrillic input."""
        # Mock AI response for Cyrillic input
        mock_openai_service.generate_completion.return_value = "web_scraper_for_russian_site"

        name = await generate_project_name(
            "Создать веб-скрапер для русского сайта",
            mock_openai_service,
            temp_base_dir
        )

        assert name == "web_scraper_for_russian_site"

    @pytest.mark.asyncio
    async def test_generate_project_name_empty_response(self, mock_openai_service, temp_base_dir):
        """Test handling of empty AI response."""
        # Mock empty response
        mock_openai_service.generate_completion.return_value = ""

        name = await generate_project_name(
            "Empty query",
            mock_openai_service,
            temp_base_dir
        )

        assert name == "unnamed_project"

    @pytest.mark.asyncio
    async def test_generate_project_name_ai_failure(self, mock_openai_service, temp_base_dir):
        """Test fallback when AI fails."""
        # Mock AI failure
        mock_openai_service.generate_completion.side_effect = Exception("AI failed")

        name = await generate_project_name(
            "Test query",
            mock_openai_service,
            temp_base_dir
        )

        # Should generate hash-based name
        assert name.startswith("project_")
        assert len(name) == 16  # "project_" + 8 chars
