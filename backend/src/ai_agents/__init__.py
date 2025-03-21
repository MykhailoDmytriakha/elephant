"""
Agent modules for interacting with language models in specific ways.
"""
import logging

# Configure loggers to ignore DEBUG messages for common noisy modules
logging.getLogger("httpcore.connection").setLevel(logging.INFO)
logging.getLogger("httpcore.http11").setLevel(logging.INFO)
logging.getLogger("openai._base_client").setLevel(logging.INFO)
logging.getLogger("openai.agents").setLevel(logging.INFO)

# Export utility functions for easy access
from src.ai_agents.utils import detect_language, get_language_instruction 

# Export planning agent functionality
from src.ai_agents.planning_agent import generate_network_plan 