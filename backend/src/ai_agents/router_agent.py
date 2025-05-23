import logging
from typing import AsyncGenerator, List, Any, Optional, Dict
import json 
from enum import Enum
from datetime import datetime, timezone

from src.model.task import Task
from src.ai_agents.utils import detect_language, get_language_instruction
from src.ai_agents.chat_agent import stream_chat_with_agent_sdk
from src.ai_agents.autonomous_data_agent import stream_data_analysis_response
from src.ai_agents.agent_tracker import get_tracker, AgentTracker
from src.core.config import settings

# Google ADK imports
from google.adk.agents import Agent  # type: ignore
from google.adk.sessions import InMemorySessionService  # type: ignore
from google.adk.runners import Runner  # type: ignore
from google.genai import types  # type: ignore
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool  # type: ignore

logger = logging.getLogger(__name__)

class AgentType(Enum):
    GENERAL_CHAT = "general_chat"
    DATA_ANALYSIS = "data_analysis"
    CODE_DEVELOPMENT = "code_development"
    RESEARCH = "research"
    PLANNING = "planning"
    EXECUTOR = "executor"

def analyze_request_intent(user_message: str) -> Dict[str, Any]:
    """
    Analyzes user request to determine the best agent and approach.
    """
    message_lower = user_message.lower()
    
    # Data analysis keywords
    data_keywords = [
        'analyze', 'data', 'csv', 'excel', 'chart', 'graph', 'plot', 'visualization',
        'statistics', 'statistical', 'correlation', 'regression', 'dataset', 'dataframe',
        'pandas', 'numpy', 'patterns', 'trends', 'insights', 'dashboard'
    ]
    
    # Code development keywords
    code_keywords = [
        'code', 'program', 'script', 'function', 'class', 'python', 'javascript', 'sql',
        'algorithm', 'debug', 'refactor', 'implement', 'develop', 'programming',
        'software', 'application', 'api', 'framework'
    ]
    
    # Research keywords
    research_keywords = [
        'research', 'find information', 'search for', 'investigate', 'study', 'explore',
        'learn about', 'gather data', 'collect information', 'web search', 'sources'
    ]
    
    # Planning keywords
    planning_keywords = [
        'plan', 'strategy', 'roadmap', 'steps', 'process', 'workflow', 'approach',
        'methodology', 'framework', 'structure', 'organize', 'schedule'
    ]
    
    # Count keyword matches
    data_score = sum(1 for keyword in data_keywords if keyword in message_lower)
    code_score = sum(1 for keyword in code_keywords if keyword in message_lower)
    research_score = sum(1 for keyword in research_keywords if keyword in message_lower)
    planning_score = sum(1 for keyword in planning_keywords if keyword in message_lower)
    
    # Determine primary intent
    scores = {
        AgentType.DATA_ANALYSIS: data_score,
        AgentType.CODE_DEVELOPMENT: code_score,
        AgentType.RESEARCH: research_score,
        AgentType.PLANNING: planning_score
    }
    
    best_agent = max(scores.keys(), key=lambda k: scores[k])
    confidence = scores[best_agent] / len(user_message.split()) if len(user_message.split()) > 0 else 0
    
    # If confidence is low, use general chat agent
    if confidence < 0.1 or scores[best_agent] == 0:
        best_agent = AgentType.GENERAL_CHAT
        confidence = 1.0  # High confidence for general chat as fallback
    
    return {
        "agent_type": best_agent,
        "confidence": confidence,
        "scores": scores,
        "requires_workspace": best_agent in [AgentType.DATA_ANALYSIS, AgentType.CODE_DEVELOPMENT],
        "complexity": "high" if any(score > 2 for score in scores.values()) else "medium" if any(score > 0 for score in scores.values()) else "low"
    }

def create_agent_handoff_tool():
    """Creates a simple handoff function for Google ADK."""
    
    def handoff_to_specialist(agent_type: str, reason: str, context: str = "") -> str:
        """
        Hands off the conversation to a specialist agent.
        
        Args:
            agent_type: Type of specialist agent needed
            reason: Reason for the handoff
            context: Additional context for the specialist
        
        Returns:
            Handoff confirmation message
        """
        return f"🔄 Handing off to {agent_type} agent. Reason: {reason}. Context: {context}"
    
    return handoff_to_specialist

async def create_router_agent(task: Task, workspace_path: str) -> Agent:
    """
    Creates the intelligent router agent that decides which specialist to use.
    """
    
    # Create tools for the router
    tools = [create_agent_handoff_tool()]
    
    instruction = f"""You are an intelligent router agent that analyzes user requests and coordinates with specialist agents. Your role is to understand the user's intent and either handle simple requests yourself or route complex ones to the appropriate specialist.

**Your Workspace**: {workspace_path}

**Available Specialist Agents**:
1. **Data Analysis Agent** - For data analysis, visualization, statistics, CSV/Excel processing
2. **Code Development Agent** - For programming, scripting, debugging, software development
3. **Research Agent** - For web research, information gathering, investigation
4. **Planning Agent** - For creating plans, strategies, workflows, project organization
5. **General Chat Agent** - For general questions, simple tasks, conversation

**Your Decision Process**:
1. Analyze the user's request for intent and complexity
2. Determine if you can handle it yourself (simple questions, clarifications)
3. If specialized work is needed, use the handoff_to_specialist tool
4. Provide clear explanations of your routing decisions

**When to Route**:
- Data analysis, CSV processing, visualizations → Data Analysis Agent
- Code writing, debugging, programming → Code Development Agent  
- Web research, fact-finding → Research Agent
- Complex planning, strategy → Planning Agent
- General questions → Handle yourself or General Chat Agent

**Guidelines**:
- Be transparent about your routing decisions
- Provide context when handing off to specialists
- Handle simple clarifications yourself
- Always explain why you're choosing a particular specialist
- Route proactively for complex technical tasks

Be intelligent, helpful, and efficient in your routing decisions."""

    # Apply language preference
    user_language = detect_language(task.task or "")
    language_instruction = get_language_instruction(user_language)
    if language_instruction:
        instruction = f"{language_instruction}\n\n{instruction}"

    agent = Agent(
        name="intelligent_router_agent",
        model=LiteLlm(model=f"openai/{settings.OPENAI_MODEL}"),
        instruction=instruction,
        tools=tools
    )
    
    return agent

async def route_and_execute_request(task: Task, user_message: str, workspace_path: str, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    Routes user request to appropriate specialist agent based on intent analysis.
    Provides real-time execution trace and tool call monitoring.
    """
    # Get or create the tracker for this task/session
    from src.ai_agents.agent_tracker import get_tracker
    effective_session_id = session_id or f"session_{task.id}"
    tracker = get_tracker(str(task.id), effective_session_id)
    
    try:
        # Analyze the request to determine appropriate agent
        intent_analysis = analyze_request_intent(user_message)
        agent_type = AgentType(intent_analysis["agent_type"])
        confidence = intent_analysis["confidence"]
        
        # Log intent analysis
        tracker.log_activity(
            agent_name="Router",
            action_type="INTENT_ANALYSIS",
            description=f"Analyzed intent: {agent_type.value} (confidence: {confidence:.2f})",
            details={
                "detected_agent": agent_type.value,
                "confidence": confidence,
                "scores": {k.value: v for k, v in intent_analysis["scores"].items()},
                "complexity": intent_analysis["complexity"]
            }
        )
        
        logger.info(f"Request analysis: agent_type={agent_type}, confidence={confidence}")
        
        # Yield detailed routing information
        yield f"🔍 **Agent Routing Analysis**\n"
        yield f"📝 Request: {user_message[:100]}{'...' if len(user_message) > 100 else ''}\n"
        yield f"🤖 Selected Agent: **{agent_type.value.replace('_', ' ').title()}** (confidence: {confidence:.2f})\n"
        yield f"📊 Intent Scores: {', '.join([f'{k.value}: {v}' for k, v in intent_analysis['scores'].items() if v > 0])}\n"
        yield f"🏗️ Workspace: `{workspace_path}`\n\n"
        
        # Start real-time execution trace
        yield f"🔍 **Agent Execution Trace**\n"
        yield f"📋 Task: {str(task.id)}\n"
        yield f"🔗 Session: {session_id or f'session_{task.id}'}\n\n"
        
        # Route to appropriate agent based on analysis
        if agent_type == AgentType.DATA_ANALYSIS:
            tracker.log_agent_transfer(
                from_agent="Router",
                to_agent="Data Analysis Agent",
                reason=f"Data analysis request detected with confidence {confidence:.2f}",
                confidence_score=confidence
            )
            
            # Stream the agent transfer immediately
            yield f"🔗 **Agent Routing:**\n"
            yield f"  • Router → **Data Analysis Agent** (confidence: {confidence:.2f})\n"
            yield f"    Reason: Data analysis request detected with confidence {confidence:.2f}\n\n"
            
            yield f"🔍 Routing to **Data Analysis Agent**...\n\n"
            async for chunk in stream_data_analysis_response(task, user_message, workspace_path, session_id):
                yield chunk
                
        elif agent_type == AgentType.CODE_DEVELOPMENT:
            tracker.log_agent_transfer(
                from_agent="Router",
                to_agent="Code Development Agent",
                reason=f"Code development request detected with confidence {confidence:.2f}",
                confidence_score=confidence
            )
            
            # Stream the agent transfer immediately
            yield f"🔗 **Agent Routing:**\n"
            yield f"  • Router → **Code Development Agent** (confidence: {confidence:.2f})\n"
            yield f"    Reason: Code development request detected with confidence {confidence:.2f}\n\n"
            
            yield f"💻 Routing to **Code Development Agent**...\n\n"
            # For now, route to general chat agent with coding focus
            async for chunk in stream_chat_with_agent_sdk(task, f"[CODE DEVELOPMENT FOCUS] {user_message}", session_id=session_id):
                yield chunk
                
        elif agent_type == AgentType.RESEARCH:
            tracker.log_agent_transfer(
                from_agent="Router",
                to_agent="Research Agent",
                reason=f"Research request detected with confidence {confidence:.2f}",
                confidence_score=confidence
            )
            
            # Stream the agent transfer immediately
            yield f"🔗 **Agent Routing:**\n"
            yield f"  • Router → **Research Agent** (confidence: {confidence:.2f})\n"
            yield f"    Reason: Research request detected with confidence {confidence:.2f}\n\n"
            
            yield f"🔬 Routing to **Research Agent**...\n\n"
            # For now, route to general chat agent with research focus
            async for chunk in stream_chat_with_agent_sdk(task, f"[RESEARCH FOCUS] {user_message}", session_id=session_id):
                yield chunk
                
        elif agent_type == AgentType.PLANNING:
            tracker.log_agent_transfer(
                from_agent="Router",
                to_agent="Planning Agent",
                reason=f"Planning request detected with confidence {confidence:.2f}",
                confidence_score=confidence
            )
            
            # Stream the agent transfer immediately
            yield f"🔗 **Agent Routing:**\n"
            yield f"  • Router → **Planning Agent** (confidence: {confidence:.2f})\n"
            yield f"    Reason: Planning request detected with confidence {confidence:.2f}\n\n"
            
            yield f"📋 Routing to **Planning Agent**...\n\n"
            # For now, route to general chat agent with planning focus
            async for chunk in stream_chat_with_agent_sdk(task, f"[PLANNING FOCUS] {user_message}", session_id=session_id):
                yield chunk
                
        else:  # AgentType.GENERAL_CHAT or fallback
            tracker.log_agent_transfer(
                from_agent="Router",
                to_agent="General Chat Agent",
                reason=f"General chat or fallback (confidence: {confidence:.2f})",
                confidence_score=confidence
            )
            
            # Stream the agent transfer immediately
            yield f"🔗 **Agent Routing:**\n"
            yield f"  • Router → **General Chat Agent** (confidence: {confidence:.2f})\n"
            yield f"    Reason: General chat or fallback (confidence: {confidence:.2f})\n\n"
            
            yield f"💬 Routing to **General Chat Agent**...\n\n"
            async for chunk in stream_chat_with_agent_sdk(task, user_message, session_id=session_id):
                yield chunk
        
        # Log completion
        tracker.log_activity(
            agent_name="Router",
            action_type="REQUEST_COMPLETED",
            description="Request processing completed successfully"
        )
        
        # Show final execution summary
        total_time = (datetime.now(timezone.utc) - tracker.start_time).total_seconds()
        yield f"\n\n⏱️ **Execution Summary:** Completed in {total_time:.2f}s\n"
        yield f"🛠️ **Tools Used:** {len(tracker.tool_calls)} tool calls\n"
        yield f"📝 **Activities:** {len(tracker.activities)} logged activities\n"
                
    except Exception as e:
        tracker.log_activity(
            agent_name="Router",
            action_type="ERROR",
            description=f"Error in routing: {str(e)}",
            success=False,
            error_message=str(e)
        )
        
        logger.error(f"Error in routing agent: {str(e)}", exc_info=True)
        yield f"⚠️ Error in routing: {str(e)}. Falling back to general chat agent...\n\n"
        
        # Fallback to general chat agent
        try:
            tracker.log_agent_transfer(
                from_agent="Router",
                to_agent="General Chat Agent (Fallback)",
                reason=f"Fallback due to error: {str(e)}"
            )
            async for chunk in stream_chat_with_agent_sdk(task, user_message, session_id=session_id):
                yield chunk
        except Exception as fallback_error:
            tracker.log_activity(
                agent_name="Router",
                action_type="FALLBACK_ERROR",
                description=f"Fallback also failed: {str(fallback_error)}",
                success=False,
                error_message=str(fallback_error)
            )
            logger.error(f"Fallback error: {str(fallback_error)}", exc_info=True)
            yield f"⚠️ System error: {str(fallback_error)}"

async def stream_intelligent_router_response(task: Task, user_message: str, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    Main entry point for intelligent routing system.
    Creates workspace and routes to appropriate specialist agent.
    """
    try:
        # Import workspace creation from chat_agent
        from src.ai_agents.chat_agent import create_workspace_for_task
        
        # Create workspace for this task
        workspace_path = create_workspace_for_task(str(task.id))
        
        # Route and execute the request
        async for chunk in route_and_execute_request(task, user_message, workspace_path, session_id):
            yield chunk
            
    except Exception as e:
        logger.error(f"Error in intelligent router: {str(e)}", exc_info=True)
        yield f"⚠️ Router error: {str(e)}" 