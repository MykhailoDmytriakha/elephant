# src/ai_agents/tools/web_tools.py
import logging
import requests
import json
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urljoin
import time
from bs4 import BeautifulSoup

try:
    from agents import function_tool # type: ignore
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    logging.warning("OpenAI Agents SDK not installed. Web tools might not be directly callable by agents.")
    AGENTS_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)

def _format_error(tool_name: str, message: str) -> str:
    """Formats consistent error messages for web tools."""
    return f"Error in {tool_name}: {message}"

if AGENTS_SDK_AVAILABLE:
    @function_tool
    def search_web(query: str, num_results: int = 5) -> str:
        """
        Searches the web using DuckDuckGo's instant answer API and returns search results.
        This is a basic implementation - for production use, consider integrating with
        Google Custom Search API, Bing Search API, or other professional search services.

        Args:
            query: The search query string
            num_results: Number of results to return (default: 5, max: 10)

        Returns:
            A formatted string containing search results or an error message starting with 'Error:'.
        """
        logger.info(f"Tool executed: search_web (Query: {query}, Results: {num_results})")
        
        try:
            # Limit results to reasonable range
            num_results = min(max(1, num_results), 10)
            
            # Use DuckDuckGo instant answer API (free but limited)
            # Note: This is a simple implementation. For production, use proper search APIs
            search_url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; ElephantBot/1.0)'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            
            # Add instant answer if available
            if data.get('Abstract'):
                results.append({
                    'title': data.get('AbstractSource', 'DuckDuckGo Instant Answer'),
                    'snippet': data.get('Abstract', ''),
                    'url': data.get('AbstractURL', ''),
                    'type': 'instant_answer'
                })
            
            # Add related topics
            for topic in data.get('RelatedTopics', [])[:num_results-len(results)]:
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append({
                        'title': topic.get('FirstURL', '').split('/')[-1].replace('_', ' ') if topic.get('FirstURL') else 'Related Topic',
                        'snippet': topic.get('Text', ''),
                        'url': topic.get('FirstURL', ''),
                        'type': 'related_topic'
                    })
            
            if not results:
                return f"No search results found for query: '{query}'"
            
            # Format results
            formatted_results = [f"Search results for '{query}':\n"]
            for i, result in enumerate(results[:num_results], 1):
                formatted_results.append(f"{i}. {result['title']}")
                if result['snippet']:
                    formatted_results.append(f"   {result['snippet'][:200]}{'...' if len(result['snippet']) > 200 else ''}")
                if result['url']:
                    formatted_results.append(f"   URL: {result['url']}")
                formatted_results.append("")  # Empty line between results
            
            logger.info(f"Successfully retrieved {len(results)} search results for query: {query}")
            return "\n".join(formatted_results)
            
        except requests.RequestException as e:
            logger.error(f"Network error during web search: {e}")
            return _format_error("search_web", f"Network error: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse search response: {e}")
            return _format_error("search_web", f"Failed to parse search response: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error during web search: {e}")
            return _format_error("search_web", f"Unexpected error: {e}")

    @function_tool
    def fetch_webpage(url: str, extract_text_only: bool = True) -> str:
        """
        Fetches content from a webpage and optionally extracts just the text content.

        Args:
            url: The URL to fetch
            extract_text_only: If True, extracts only text content (default). If False, returns raw HTML.

        Returns:
            The webpage content or an error message starting with 'Error:'.
        """
        logger.info(f"Tool executed: fetch_webpage (URL: {url}, Text Only: {extract_text_only})")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; ElephantBot/1.0)'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            if extract_text_only:
                # Use BeautifulSoup to extract text content
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text and clean it up
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                # Limit text length
                if len(text) > 5000:
                    text = text[:5000] + "... [Content truncated]"
                
                logger.info(f"Successfully fetched and extracted text from: {url}")
                return f"Text content from {url}:\n\n{text}"
            else:
                # Return raw HTML (limited length)
                html = response.text
                if len(html) > 10000:
                    html = html[:10000] + "... [HTML truncated]"
                
                logger.info(f"Successfully fetched HTML from: {url}")
                return f"HTML content from {url}:\n\n{html}"
                
        except requests.RequestException as e:
            logger.error(f"Network error fetching webpage '{url}': {e}")
            return _format_error("fetch_webpage", f"Network error: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error fetching webpage '{url}': {e}")
            return _format_error("fetch_webpage", f"Unexpected error: {e}")

    @function_tool
    def check_url_status(url: str) -> str:
        """
        Checks if a URL is accessible and returns basic information about it.

        Args:
            url: The URL to check

        Returns:
            Status information about the URL or an error message starting with 'Error:'.
        """
        logger.info(f"Tool executed: check_url_status (URL: {url})")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; ElephantBot/1.0)'
            }
            
            start_time = time.time()
            response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
            response_time = time.time() - start_time
            
            info = {
                "URL": url,
                "Status Code": response.status_code,
                "Status": "Accessible" if response.status_code < 400 else "Error",
                "Response Time": f"{response_time:.2f} seconds",
                "Content Type": response.headers.get('content-type', 'Unknown'),
                "Content Length": response.headers.get('content-length', 'Unknown'),
                "Last Modified": response.headers.get('last-modified', 'Unknown'),
                "Server": response.headers.get('server', 'Unknown')
            }
            
            if response.history:
                info["Redirects"] = f"{len(response.history)} redirect(s)"
                info["Final URL"] = response.url
            
            info_str = "\n".join([f"- {k}: {v}" for k, v in info.items()])
            
            logger.info(f"Successfully checked URL status: {url} (Status: {response.status_code})")
            return f"URL Status Information:\n{info_str}"
            
        except requests.RequestException as e:
            logger.error(f"Error checking URL status '{url}': {e}")
            return _format_error("check_url_status", f"Network error: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error checking URL status '{url}': {e}")
            return _format_error("check_url_status", f"Unexpected error: {e}")

else:
    def _format_error_sdk_unavailable(tool_name: str, message: str) -> str:
        """Formats consistent error messages when SDK is unavailable."""
        return f"Error in {tool_name}: {message} (Reason: OpenAI Agents SDK not installed)"

    def search_web(query: str, num_results: int = 5) -> str:
        return _format_error_sdk_unavailable("search_web", "Operation failed")
    
    def fetch_webpage(url: str, extract_text_only: bool = True) -> str:
        return _format_error_sdk_unavailable("fetch_webpage", "Operation failed")
    
    def check_url_status(url: str) -> str:
        return _format_error_sdk_unavailable("check_url_status", "Operation failed")

web_tools_list = [
    search_web,
    fetch_webpage,
    check_url_status,
]

# Google ADK compatible functions (without decorators)
def _search_web(query: str, num_results: int = 5) -> str:
    """Searches the web using DuckDuckGo and returns formatted results."""
    logger.info(f"Tool executed: search_web (Query: {query}, Results: {num_results})")
    
    try:
        # Limit results to reasonable range
        num_results = min(max(1, num_results), 10)
        
        # Use DuckDuckGo instant answer API (free but limited)
        search_url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; ElephantBot/1.0)'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        
        # Add instant answer if available
        if data.get('Abstract'):
            results.append({
                'title': data.get('AbstractSource', 'DuckDuckGo Instant Answer'),
                'snippet': data.get('Abstract', ''),
                'url': data.get('AbstractURL', ''),
                'type': 'instant_answer'
            })
        
        # Add related topics
        for topic in data.get('RelatedTopics', [])[:num_results-len(results)]:
            if isinstance(topic, dict) and 'Text' in topic:
                results.append({
                    'title': topic.get('FirstURL', '').split('/')[-1].replace('_', ' ') if topic.get('FirstURL') else 'Related Topic',
                    'snippet': topic.get('Text', ''),
                    'url': topic.get('FirstURL', ''),
                    'type': 'related_topic'
                })
        
        if not results:
            return f"No search results found for query: '{query}'"
        
        # Format results
        formatted_results = [f"Search results for '{query}':\n"]
        for i, result in enumerate(results[:num_results], 1):
            formatted_results.append(f"{i}. {result['title']}")
            if result['snippet']:
                formatted_results.append(f"   {result['snippet'][:200]}{'...' if len(result['snippet']) > 200 else ''}")
            if result['url']:
                formatted_results.append(f"   URL: {result['url']}")
            formatted_results.append("")  # Empty line between results
        
        logger.info(f"Successfully retrieved {len(results)} search results for query: {query}")
        return "\n".join(formatted_results)
        
    except requests.RequestException as e:
        logger.error(f"Network error during web search: {e}")
        return _format_error("search_web", f"Network error: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse search response: {e}")
        return _format_error("search_web", f"Failed to parse search response: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error during web search: {e}")
        return _format_error("search_web", f"Unexpected error: {e}")

def _fetch_webpage(url: str, extract_text_only: bool = True) -> str:
    """Fetches content from a webpage and optionally extracts just the text content."""
    logger.info(f"Tool executed: fetch_webpage (URL: {url}, Text Only: {extract_text_only})")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; ElephantBot/1.0)'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        if extract_text_only:
            # Use BeautifulSoup to extract text content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it up
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit text length
            if len(text) > 5000:
                text = text[:5000] + "... [Content truncated]"
            
            logger.info(f"Successfully fetched and extracted text from: {url}")
            return f"Text content from {url}:\n\n{text}"
        else:
            # Return raw HTML (limited length)
            html = response.text
            if len(html) > 10000:
                html = html[:10000] + "... [HTML truncated]"
            
            logger.info(f"Successfully fetched HTML from: {url}")
            return f"HTML content from {url}:\n\n{html}"
            
    except requests.RequestException as e:
        logger.error(f"Network error fetching webpage '{url}': {e}")
        return _format_error("fetch_webpage", f"Network error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error fetching webpage '{url}': {e}")
        return _format_error("fetch_webpage", f"Unexpected error: {e}")

# Google ADK compatible tools (simple functions)
google_adk_web_tools = [
    _search_web,
    _fetch_webpage,
]

# Tracked web tools for enhanced monitoring
def create_tracked_web_tools(task_id: str, session_id: str):
    """Creates web tools with tracking for specific task/session."""
    from src.ai_agents.agent_tracker import get_tracker
    import time
    
    tracker = get_tracker(task_id, session_id)
    
    def tracked_search_web(query: str, num_results: int = 5) -> str:
        start_time = time.time()
        try:
            result = _search_web(query, num_results)
            execution_time = (time.time() - start_time) * 1000
            tracker.log_tool_call("search_web", 
                                {"query": query, "num_results": num_results}, 
                                result[:200] + "..." if len(result) > 200 else result, True, None, execution_time)
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            tracker.log_tool_call("search_web", 
                                {"query": query, "num_results": num_results}, 
                                None, False, str(e), execution_time)
            raise
    
    def tracked_fetch_webpage(url: str, extract_text_only: bool = True) -> str:
        start_time = time.time()
        try:
            result = _fetch_webpage(url, extract_text_only)
            execution_time = (time.time() - start_time) * 1000
            tracker.log_tool_call("fetch_webpage", 
                                {"url": url, "extract_text_only": extract_text_only}, 
                                result[:200] + "..." if len(result) > 200 else result, True, None, execution_time)
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            tracker.log_tool_call("fetch_webpage", 
                                {"url": url, "extract_text_only": extract_text_only}, 
                                None, False, str(e), execution_time)
            raise
    
    return [
        tracked_search_web,
        tracked_fetch_webpage,
    ]