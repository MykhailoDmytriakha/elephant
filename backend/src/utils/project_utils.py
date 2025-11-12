# backend/src/utils/project_utils.py
import re
import os
from pathlib import Path
from typing import Union
from src.services.openai_service import OpenAIService


async def generate_project_name(query: str, openai_service: OpenAIService, base_dir: Path) -> str:
    """
    Generate a unique, descriptive project folder name using AI.

    Args:
        query: User query to generate name from
        openai_service: OpenAI service instance
        base_dir: Base directory for projects

    Returns:
        Unique project name in snake_case format
    """
    # Generate base name using AI
    base_name = await _generate_base_name(query, openai_service)

    # Ensure uniqueness by checking existing directories
    project_name = base_name
    counter = 1

    while (base_dir / project_name).exists():
        counter += 1
        project_name = f"{base_name}_{counter}"

    return project_name


async def _generate_base_name(query: str, openai_service: OpenAIService) -> str:
    """
    Generate base project name using OpenAI API.

    Args:
        query: User query
        openai_service: OpenAI service instance

    Returns:
        Snake_case project name
    """
    prompt = f"""Given the following user query, generate a concise project folder name:
- Use 3-6 words maximum
- Format: snake_case (lowercase with underscores)
- English only, descriptive of the project
- No special characters except underscore
- Be specific and clear

User Query: "{query}"

Output only the folder name, nothing else."""

    try:
        response = await openai_service.generate_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.3
        )

        # Extract and clean the response
        name = response.strip().lower()

        # Remove any special characters and ensure snake_case
        name = re.sub(r'[^a-z0-9_]', '_', name)
        name = re.sub(r'_+', '_', name).strip('_')

        # Ensure it's not empty and has reasonable length
        if not name or len(name) < 3:
            name = "unnamed_project"
        elif len(name) > 50:
            name = name[:50].rstrip('_')

        return name

    except Exception as e:
        # Fallback to a simple hash-based name if AI fails
        import hashlib
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        return f"project_{query_hash}"
