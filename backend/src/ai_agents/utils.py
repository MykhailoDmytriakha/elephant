import re
import logging

logger = logging.getLogger(__name__)

def detect_language(text: str) -> str:
    """
    Simple heuristic to detect language from text.
    Returns ISO language code or 'en' as default.
    
    Args:
        text: Text to analyze for language detection
        
    Returns:
        str: ISO language code (e.g., 'en', 'es', 'fr', etc.)
    """
    # This is a simplified detection - in production, you would want to use
    # a more robust language detection library
    
    if not text:
        return 'en'
    
    # Common non-English language patterns
    patterns = {
        'es': r'\b(el|la|los|las|un|una|y|o|que|en|con|por|para|como|está|ser|tener)\b',
        'fr': r'\b(le|la|les|un|une|des|et|ou|qui|que|dans|sur|pour|par|avec|est|être|avoir)\b',
        'de': r'\b(der|die|das|ein|eine|und|oder|ist|sein|haben|für|mit|auf|in|bei|von)\b',
        'ru': r'[а-яА-Я]',
        'zh': r'[\u4e00-\u9fff]',
        'ja': r'[\u3040-\u309f\u30a0-\u30ff]',
    }
    
    # Check for language patterns
    for lang, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            # logger.debug(f"Detected language: {lang}")
            return lang
    
    # Default to English
    return 'en'

def get_language_instruction(language: str) -> str:
    """
    Generate language-specific instructions for agents based on detected language.
    
    Args:
        language: ISO language code
        
    Returns:
        str: Instructions for agents to respond in the appropriate language
    """
    if language == 'en':
        return ""
        
    return f"""
    IMPORTANT: The user's request appears to be in a language other than English (detected: {language}).
    Please formulate your response in the same language as the user's original request.
    Use the user's language patterns and terminology from their initial description.
    RESPONSE IN `{language}` LANGUAGE.
    """ 