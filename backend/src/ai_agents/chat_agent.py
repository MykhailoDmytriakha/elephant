import logging
from typing import AsyncGenerator, List, Any, Optional
import json 

from src.model.task import Task
from src.ai_agents.utils import detect_language, get_language_instruction
from src.ai_agents.tools.filesystem_tools import filesystem_tools_list
from src.ai_agents.tools.cognitive_tools import cognitive_tools_list
from src.ai_agents.executor_agent import create_executor_agent
from agents.run_context import RunContextWrapper # type: ignore
logger = logging.getLogger(__name__)

# Try to import the OpenAI Agents SDK
try:
    from agents import Agent, Runner, handoff  # type: ignore
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

@function_tool
def get_task_context(wrapper: RunContextWrapper[Task]) -> str:
    """
    Retrieves relevant context and details about the current task.
    """
    logger.info("Agent requested task context using the tool.")
    try:
        return wrapper.context['task'].model_dump_json()
    except Exception as e:
        logger.error(f"Error getting task context: {e}", exc_info=True)
        return f'{{"error": "Failed to retrieve task context: {str(e)}"}}'

@function_tool
def log_subtask_id_before_handoff(wrapper: RunContextWrapper[Task], subtask_id: str) -> str:
    """Logs the subtask ID before handoff.
    Use this tool ONLY when you have a specific subtask ID to hand off to the ExecutorAgent.
    
    Args:
        subtask_id: The subtask ID to hand off to the ExecutorAgent.
    """
    logger.info(f"Agent requested handoff to ExecutorAgent with subtask ID: {subtask_id}")
    wrapper.context['subtask_id'] = subtask_id
    return f"Next step is for ExecutorAgent to work on subtask with ID: {subtask_id}"

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
        # --- Static Instructions Block ---
        instructions = f"""
        **Big Overview: The Elephant Project**

        You are part of the Elephant project, an AI system designed to understand complex user requests (tasks) and break them down into manageable, executable steps for AI agents or robotic systems. The project follows a structured pipeline:
        1. Context Gathering (Initial phase before this chat)
        2. Task Scope Formulation (5W+H: What, Why, Who, Where, When, How)
        3. Ideal Final Result (IFR) Definition
        4. Requirements Definition
        5. Network Plan Generation (Stages and dependencies)
        6. Hierarchical Task Decomposition (Stage -> Work -> ExecutableTask -> Subtask)
        The user already done genereate all required Stages, and ready to work on exectuion. Details about current state of the project are available in the `get_task_context()` tool.

        **Your Role: Chat Assistant**

        You are a specialized AI assistant for software development tasks within the Elephant project. Your main goal is to assist the user **after** the initial task context has been gathered and the high-level plan (Network Plan with Stages) has been generated. You help the user understand the generated plan, discuss specific stages or upcoming tasks, and answer questions about the project based on the established context.

        **Execution Handoff Workflow:**
        Your primary role is assisting with understanding the plan and context. However, when the user indicates they want to **execute** something, you must prepare and hand off to the specialized `ExecutorAgent`.

        1.  **Detect Execution Intent:** Look for keywords ("execute", "run", "implement", "do", "perform", "start", "work on", "put in progress") or phrases ("execute the next subtask", "run the next step", "start the next one", "proceed", "continue").

        2.  **Determine Target Subtask ID:**
            *   **If the user provides a specific subtask ID (e.g., `ST-123456`):** Use that ID directly for the handoff.
            *   **If the user requests the "next" subtask (or uses similar implicit phrasing):**
                a.  You MUST call the `get_task_context()` tool to retrieve the full task details, including the `network_plan`.
                b.  Parse the returned task JSON. Iterate through `task.network_plan.stages`, then `stage.work_packages`, then `work.tasks`, and finally `executable_task.subtasks`.
                c.  Find the **first** subtask you encounter that has `status == PENDING`.
                d.  **If a PENDING subtask ID is found:** This is your target subtask ID. **BEFORE initiating the handoff**, you MUST call the `log_subtask_id_before_handoff(subtask_id=FOUND_SUBTASK_ID)` tool with the ID you found.
                e.  **If NO PENDING subtask is found after checking the entire plan:** Do NOT hand off. Inform the user that there are no pending subtasks available to execute.

        3.  **Initiate Handoff:** Once you have a **specific target subtask ID** (either provided by the user or found and logged by you), use the handoff capability to transfer control to the `ExecutorAgent`. The `ExecutorAgent` *requires* a specific ID to function, which it expects to find logged in the context.

        **Important:** Do NOT hand off without a specific `subtask_id` being logged via the `log_subtask_id_before_handoff` tool.

        **Available Tools:**
        *   `get_task_context()`: Retrieves detailed information about the current task (scope, requirements, **network_plan**, etc.). **Crucial for finding the "next" subtask.**
        *   `log_subtask_id_before_handoff(subtask_id: str)`: Logs the specific subtask ID you intend to hand off. **MUST be called before handoff if you determined the subtask ID yourself.**
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
        *   **Cognitive Tools:** (For planning, analysis, and information processing)
            *   `evaluate_plan_feasibility(plan_description, constraints)`: Evaluates if a plan is feasible given constraints. Use this when you need to assess whether a proposed approach is viable.
            *   `identify_required_resources(task_description, current_context)`: Lists resources needed for a task. Helps identify what's necessary to complete a task successfully.
            *   `analyze_potential_risks(action_description, context)`: Analyzes risks of an action. Use this to identify potential issues before they occur.
            *   `break_down_complex_task(task_description, max_depth)`: Breaks down complex tasks into sub-tasks. Useful for planning and organization.
            *   `verify_step_completion(step_description, evidence)`: Verifies if a step is completed based on evidence. Helps validate progress.
            *   `compare_alternative_approaches(goal, approaches)`: Compares different approaches to a goal. Use when multiple solutions exist.
            *   `synthesize_information(information_pieces, desired_output_format)`: Combines information into cohesive output. Great for summarizing or organizing data.
        *   **IMPORTANT SECURITY NOTE:** You MUST NOT attempt to access or modify files outside the directory mentioned by `list_allowed_directory()`. All paths provided to filesystem tools MUST be relative to that directory.

        **How to Respond:**
        1.  **Be Concise & Technical:** Provide clear, helpful, and technically sound information.
        2.  **Explain Reasoning:** Briefly explain the 'why' behind your suggestions or questions.
        3.  **Use Task Context:** You have access to details about the current task (description, scope, requirements, IFR, plan elements like Stages, Works, Tasks, Subtasks etc.). Use the `get_task_context()` tool **if you need specific information** about the task's requirements, scope, ideal result, or plan details to answer the user's current question effectively, **OR if you need to find the next pending subtask ID for an execution request**. This information isn't always readily available from the conversation history. **Crucially, also use this tool if the user asks to perform an action based on a specific plan element, asks for details about a plan element (e.g., its contents, purpose, or associated files mentioned in the plan), asks about a specific subtask ID (e.g., 'tell me about ST-123'), or asks about the origin or responsibility for a task-related resource *as defined within the task's plan or requirements*, and you don't already have this information.** **IMPORTANT VERIFICATION STEP:** Before describing, referencing, or attempting to hand off *any* specific subtask ID mentioned by the user, you **MUST FIRST** call `get_task_context` to verify that subtask ID actually exists in the current plan and to retrieve its details, unless you have already confirmed its existence via `get_task_context` earlier in *this specific turn*. Do not assume existence based on naming patterns. This verification step is critical even if the user seems certain about the ID. This is particularly important if the question relates to a recently discussed or failed task element. Do not call `get_task_context` preemptively for general conversation. For example, use the tool if the user asks about task requirements, asks about a *specific* subtask ID like 'what is S1_W1_ET1_ST5?', asks what a file mentioned in the plan should contain, or inquires about the planned source of a specific resource. If the user asks a general programming question unrelated to the specific task details, you don't need the tool.
        4.  **Use Filesystem Tools:** If the user asks to read, write, list, or manipulate files *related to the task* (e.g., read a config file mentioned in requirements, list generated artifacts), use the appropriate filesystem tool. Always verify the allowed directory first using `list_allowed_directory()` if unsure. Ensure paths are relative.
        5.  **Use Cognitive Tools:** When the user needs assistance with planning, analysis, risk assessment, or breaking down complex tasks, use the appropriate cognitive tool. These tools help with:
            *   Evaluating feasibility of plans or approaches
            *   Identifying necessary resources for tasks
            *   Analyzing risks before implementation
            *   Breaking down complex tasks into manageable steps
            *   Comparing alternative approaches
            *   Synthesizing or organizing information
            Use these tools proactively when the user is struggling with complex problems or needs assistance with planning.
        6.  **Recognize Execution Requests & Handoff:** If the user asks you to execute, implement, run, perform, or start a task/subtask:
            *   If a specific `subtask_id` is given, hand off immediately to the `ExecutorAgent`.
            *   If the user asks for the "next" subtask, follow the **Execution Handoff Workflow** above: call `get_task_context`, find the first PENDING subtask ID, call `log_subtask_id_before_handoff` with that ID, and then hand off. If no pending subtask is found, inform the user.
            *   **Crucial:** Only hand off when you have a *specific* `subtask_id` and have called `log_subtask_id_before_handoff`.
        7.  **Code Examples:** If asked about code relevant to the task or general concepts, provide specific, correct examples.
        8.  **Honesty:** If you don't know something, state it clearly. Before concluding you don't know or providing a generic answer, consider if the necessary information might be within the task details or accessible via filesystem tools. If the question relates to the task's specifics (e.g., requirements, scope, file contents specified by the plan, details of plan elements like subtasks, **or the planned origin/responsibility for a resource**) and you lack the answer, **you MUST use the `get_task_context` tool to retrieve the necessary details before proceeding or stating you cannot fulfill the request.** Only provide generic descriptions if the task context does not contain specific details. If the question relates to file content within the allowed directory *not* specified by the plan, consider using `read_file` or `list_directory`. Don't invent answers.
        9.  **Language:** Respond in the language detected from the user's input ({user_language}).

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

        # Create the executor agent for handoff
        executor_agent = create_executor_agent()
        
        # Create handoff to executor agent - fixed implementation
        # According to the OpenAI Agents SDK documentation, handoff only requires the agent parameter
        executor_handoff = handoff(agent=executor_agent)

        # Create the agent with instructions and ALL tools
        agent = Agent(
            name="ChatAgent",
            instructions=instructions,
            model=model,
            tools=[get_task_context, log_subtask_id_before_handoff] + filesystem_tools_list + cognitive_tools_list,
            handoffs=[executor_handoff]
        )

        runner = Runner()
        logger.info(f"---> REQUEST OPENAI **ChatAgent** ({user_language}) with Agent SDK")

        # Stream the response
        if final_message_list:
            result = runner.run_streamed(agent, final_message_list, context={"task": task})
            event_count = 0
            content_chunk_count = 0
            async for event in result.stream_events():
                event_count += 1
                # logger.debug(f"Stream Event: {event}")
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
                elif event.type == "run_item_stream_event":
                    # Show tool call and results in real-time
                    try:
                        from agents import ItemHelpers
                        if event.item.type == "tool_call_item":
                            # Получаем имя агента
                            agent_name = "unknown agent"
                            if hasattr(result, 'current_agent') and hasattr(result.current_agent, 'name'):
                                agent_name = result.current_agent.name
                            
                            # Получаем имя инструмента
                            if hasattr(event, 'name') and event.name == "tool_called":
                                tool_name = event.item.raw_item.name if hasattr(event.item.raw_item, 'name') else "unknown tool"
                            else:
                                tool_name = "unknown tool"
                                
                            # Формируем сообщение с указанием агента и инструмента
                            tool_message = f"[Agent {agent_name} called tool: {tool_name}]\n"
                            agent_response_accumulator += tool_message
                            yield tool_message
                        elif event.item.type == "handoff_call_item":
                            # Handle handoff item start
                            agent_name = "unknown agent #1"
                            if hasattr(result, 'current_agent') and hasattr(result.current_agent, 'name'):
                                agent_name = result.current_agent.name
                            
                            # Determine target agent's name from the handoff item
                            target_agent = "unknown agent #2"
                            if hasattr(event.item, 'raw_item') and hasattr(event.item.raw_item, 'name'):
                                target_name_match = event.item.raw_item.name
                                if 'transfer_to_' in target_name_match.lower():
                                    target_agent = target_name_match.replace('transfer_to_', '')
                            
                            # Log handoff initiation message
                            handoff_init_message = f"[Agent {agent_name} is initiating handoff to {target_agent}]\n-----------------------------------\n"
                            agent_response_accumulator += handoff_init_message
                            yield handoff_init_message
                        elif event.item.type == "tool_call_output_item":
                            if hasattr(event.item, 'output'):
                                # Получаем имя агента
                                agent_name = "unknown agent"
                                if hasattr(result, 'current_agent') and hasattr(result.current_agent, 'name'):
                                    agent_name = result.current_agent.name
                                
                                # Format the tool output in a user-friendly way
                                tool_output = str(event.item.output)
                                if len(tool_output) > 500:  # Truncate very long outputs
                                    tool_output = tool_output
                                tool_result = f"[Agent {agent_name} tool result:] \n{tool_output}\n-----------------------------------\n"
                                agent_response_accumulator += tool_result
                                yield tool_result
                    except Exception as e:
                        logger.error(f"Error processing run_item_stream_event: {str(e)}", exc_info=True)

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