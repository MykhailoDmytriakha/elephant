import logging
from typing import AsyncGenerator, List, Dict, Any, Optional
import json # Ensure json is imported

from src.model.task import Task
from src.ai_agents.utils import detect_language, get_language_instruction
# Import the filesystem tools
from src.ai_agents.filesystem_tools import filesystem_tools_list # Import the list

logger = logging.getLogger(__name__)

# Try to import the OpenAI Agents SDK
try:
    from agents import Agent, Runner  # type: ignore
    from agents.stream_events import StreamEvent, RunItemStreamEvent  # type: ignore
    from agents import function_tool # Add this import
    from src.core.config import settings
    model = settings.OPENAI_MODEL
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI Agents SDK not installed. Some functionality will be limited.")
    AGENTS_SDK_AVAILABLE = False

if not AGENTS_SDK_AVAILABLE:
    logger.error("OpenAI Agents SDK not installed.")
    raise ImportError("OpenAI Agents SDK not installed. Please install with `pip install openai-agents`")

async def stream_chat_response(task: Task, user_message: str, message_history: Optional[List[Any]] = None) -> AsyncGenerator[str, None]:
    """
    Streams a chat response for the given task and user message using Agent SDK.
    Includes filesystem tools if available.

    Args:
        task: The task to generate a response for
        user_message: The user's message to respond to
        message_history: Optional list of previous messages in the conversation

    Yields:
        Chunks of the response as they are generated
    """
    if not AGENTS_SDK_AVAILABLE:
        raise ImportError("OpenAI Agents SDK not installed")

    # Sanitize message history (same as before)
    sanitized_history = None
    if message_history:
        sanitized_history = []
        for msg in message_history:
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                sanitized_history.append({"role": msg.role, "content": msg.content})
            elif isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                sanitized_history.append({"role": msg['role'], "content": msg['content']})
            else:
                logger.warning(f"Skipping invalid message in history: {msg}")
                continue

    logger.info(f"Starting stream_chat_response for task {task.id}")

    async for content in stream_chat_with_agent_sdk(task, user_message, sanitized_history):
        yield content

async def stream_chat_with_agent_sdk(task: Task, user_message: str, message_history: Optional[List[Any]] = None) -> AsyncGenerator[str, None]:
    """
    Implementation of chat streaming using the Agent SDK.
    """
    # Log the user message
    logger.info(f"USER MESSAGE for Task {task.id}: {user_message}")

    # Helper function (same as before)
    def to_dict(msg):
         if hasattr(msg, 'model_dump'):
             return msg.model_dump()
         elif hasattr(msg, 'dict'):
             return msg.dict()
         elif isinstance(msg, dict): # Check if it's already a dict
             return msg # Return it directly
         # Only warn and return default if it's not a Pydantic model or dict
         logger.warning(f"Message type not directly convertible: {type(msg)}. Ensure history contains dicts or Pydantic models.")
         return {"role": "unknown", "content": "error: invalid message format"}


    user_language = detect_language(task.short_description or "")
    language_instruction = get_language_instruction(user_language)

    agent_response_accumulator = ""
    try:
        @function_tool
        def get_task_context() -> str:
            """Retrieves relevant context and details about the current software development task.
            Use this tool ONLY when you need specific information about the task's requirements,
            description, scope, or ideal result to answer the user's query effectively.
            Do not call this tool preemptively if the user's query doesn't require task details.
            """
            logger.info("Agent requested task context using the tool.")
            try:
                return task.model_dump_json()
            except Exception as e:
                logger.error(f"Error getting task context: {e}", exc_info=True)
                return f'{{"error": "Failed to retrieve task context: {str(e)}"}}'

        # --- Static Instructions Block ---
        # UPDATED Instructions to include filesystem tools
        instructions = f"""
        **Big Overview: The Elephant Project**

        You are part of the Elephant project, an AI system designed to understand complex user requests (tasks) and break them down into manageable, executable steps for AI agents or robotic systems. The project follows a structured pipeline:
        1. Context Gathering (Initial phase before this chat)
        2. Task Scope Formulation (5W+H: What, Why, Who, Where, When, How)
        3. Ideal Final Result (IFR) Definition
        4. Requirements Definition
        5. Network Plan Generation (Stages and dependencies)
        6. Hierarchical Task Decomposition (Stage -> Work -> ExecutableTask -> Subtask)

        **Your Role: Chat Assistant**

        You are a specialized AI assistant for software development tasks within the Elephant project. Your main goal is to assist the user **after** the initial task context has been gathered and the high-level plan (Network Plan with Stages) has been generated. You help the user understand the generated plan, discuss specific stages or upcoming tasks, and answer questions about the project based on the established context.

        **Available Tools:**
        *   `get_task_context()`: Retrieves detailed information about the current task (scope, requirements, etc.). Use ONLY when specific task details are needed to answer the user.
        *   **Filesystem Tools (Operate ONLY within the allowed directory: '{str(settings.ALLOWED_BASE_DIR)}'):**
            *   `list_allowed_directory()`: Shows the base directory you can work within.
            *   `read_file(path: str)`: Reads content of a file relative to the allowed directory.
            *   `write_file(path: str, content: str)`: Writes/overwrites a file relative to the allowed directory. Assumes parent directory exists.
            *   `edit_file(path: str, edits: List[Dict[str, str]], dry_run: bool)`: Edits a file by applying a list of text replacements. Each edit specifies 'old_text' and 'new_text'. Returns a diff. Set dry_run to False to save changes.
            *   `create_directory(path: str)`: Creates a directory relative to the allowed directory (including parents).
            *   `list_directory(path: str)`: Lists files and subdirectories within a path relative to the allowed directory. Use '.' for the base directory.
            *   `directory_tree(path: str)`: Gets a JSON tree structure of a directory relative to the allowed directory. Use '.' for the base directory.
            *   `move_file(source: str, destination: str)`: Moves/renames a file/directory. Both paths are relative to the allowed directory.
            *   `search_files(path: str, pattern: str, case_sensitive: bool)`: Searches recursively using a glob pattern within a path relative to the allowed directory.
            *   `get_file_info(path: str)`: Gets metadata (size, type, modified time) for a file/directory relative to the allowed directory.
        *   **IMPORTANT SECURITY NOTE:** You MUST NOT attempt to access or modify files outside the directory mentioned by `list_allowed_directory()`. All paths provided to filesystem tools MUST be relative to that directory.

        **How to Respond:**
        1.  **Be Concise & Technical:** Provide clear, helpful, and technically sound information.
        2.  **Explain Reasoning:** Briefly explain the 'why' behind your suggestions or questions.
        3.  **Use Task Context:** You have access to details about the current task (description, scope, requirements, IFR, plan elements like Stages, Works, Tasks, Subtasks etc.). Use the `get_task_context()` tool **if you need specific information** about the task's requirements, scope, or ideal result to answer the user's current question effectively. **Crucially, also use this tool if the user asks you to perform an action based on a specific plan element (like executing a subtask with ID 'S1_W1_ET1_ST1') and you don't already know the details of that element.** Do not call it preemptively for general conversation. For example, if the user asks "What are the requirements for this task?" or "Execute subtask S1_W1_ET1_ST1", use the tool. If the user asks a general programming question, you don't need the tool.
        4.  **Use Filesystem Tools:** If the user asks to read, write, list, or manipulate files *related to the task* (e.g., read a config file mentioned in requirements, list generated artifacts), use the appropriate filesystem tool. Always verify the allowed directory first using `list_allowed_directory()` if unsure. Ensure paths are relative.
        5.  **Code Examples:** If asked about code relevant to the task or general concepts, provide specific, correct examples.
        6.  **Honesty:** If you don't know something, state it clearly. Before concluding you don't know, consider if the necessary information might be within the task details or accessible via filesystem tools. If the question relates to the task's specifics (e.g., requirements, scope, generated plan elements like subtasks) and you lack the answer, **you MUST use the `get_task_context` tool to retrieve the necessary details before proceeding or stating you cannot fulfill the request.** If the question relates to file content within the allowed directory, consider using `read_file` or `list_directory`. Don't invent answers.
        7.  **Language:** Respond in the language detected from the user's input ({user_language}).

        {language_instruction}
        """

        # --- Prepare message content ---
        final_message_list = []
        if message_history and len(message_history) > 0:
            history_dicts = []
            for i, msg in enumerate(message_history):
                msg_dict = to_dict(msg)
                if 'role' in msg_dict and 'content' in msg_dict:
                    history_dicts.append(msg_dict)

            current_message_in_history = any(
                msg.get("role") == "user" and msg.get("content") == user_message
                for msg in history_dicts
            )

            if not current_message_in_history:
                 final_message_list = history_dicts + [{"role": "user", "content": user_message}]
            else:
                final_message_list = history_dicts
        else:
            final_message_list = [{"role": "user", "content": user_message}]


        # Create the agent with instructions and ALL tools
        agent = Agent(
            name="ChatAssistantWithFilesystem", # New name
            instructions=instructions,
            model=model,
            tools=[get_task_context] + filesystem_tools_list # Combine tools
        )

        runner = Runner()
        logger.info(f"---> REQUEST OPENAI **ChatAssistantWithFilesystem** ({user_language}) with Agent SDK")

        # Stream the response
        if final_message_list:
            result = runner.run_streamed(agent, final_message_list)
            event_count = 0
            content_chunk_count = 0
            async for event in result.stream_events():
                event_count += 1
                if event.type == "raw_response_event":
                    try:
                        if hasattr(event, 'data') and type(event.data).__name__ == 'ResponseTextDeltaEvent':
                           if hasattr(event.data, 'delta') and event.data.delta:
                                content = event.data.delta
                                agent_response_accumulator += content # Accumulate the response
                                content_chunk_count += 1
                                yield content
                    except Exception as e:
                        logger.error(f"Error processing raw_response_event data: {str(e)}", exc_info=True)
                elif event.type != "agent_updated_stream_event" and event.type != "run_item_stream_event":
                     pass # logger.debug(f"Stream Event: {event.type}") # Log other events if needed

            logger.info(f"Finished processing stream events. Processed {event_count} total events, yielded {content_chunk_count} delta content chunks.")

    # Error handling
    except Exception as e:
        logger.error(f"Error in Agent SDK chat streaming: {str(e)}", exc_info=True)
        # Yield a JSON error chunk for the frontend to parse
        yield json.dumps({"error": f"Error generating response: {str(e)}"}) + "\n\n"
    finally:
        # Log the complete agent response
        logger.info(f"AGENT RESPONSE for Task {task.id}: {agent_response_accumulator}")
        # pass # logger.debug("Chat stream finished.")