import logging
from typing import AsyncGenerator, List, Any, Optional, Dict
import json 
import time
import pandas as pd
import numpy as np
from pathlib import Path

from src.model.task import Task
from src.ai_agents.utils import detect_language, get_language_instruction
from src.ai_agents.tools.filesystem_tools import google_adk_filesystem_tools, create_tracked_filesystem_tools
from src.ai_agents.tools.cognitive_tools import google_adk_cognitive_tools, create_tracked_cognitive_tools
from src.ai_agents.tools.web_tools import google_adk_web_tools, create_tracked_web_tools
from src.ai_agents.agent_tracker import get_tracker
from src.core.config import settings

# Google ADK imports
from google.adk.agents import Agent  # type: ignore
from google.adk.sessions import InMemorySessionService  # type: ignore
from google.adk.runners import Runner  # type: ignore
from google.genai import types  # type: ignore
from google.adk.memory import InMemoryMemoryService  # type: ignore
from google.adk.tools import FunctionTool  # type: ignore
from google.adk.models.lite_llm import LiteLlm

logger = logging.getLogger(__name__)

# Create specialized data analysis tools
def analyze_csv_data(file_path: str, analysis_type: str = "overview") -> str:
    """
    Analyzes CSV data and provides insights.
    
    Args:
        file_path: Path to the CSV file to analyze
        analysis_type: Type of analysis ('overview', 'statistical', 'patterns', 'quality')
    
    Returns:
        Analysis results as a string
    """
    try:
        # Load the data
        df = pd.read_csv(file_path)
        
        if analysis_type == "overview":
            result = f"""Data Overview for {file_path}:
- Shape: {df.shape[0]} rows, {df.shape[1]} columns
- Columns: {list(df.columns)}
- Data types: {df.dtypes.to_dict()}
- Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB
- First 5 rows:
{df.head().to_string()}
"""
        elif analysis_type == "statistical":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            result = f"""Statistical Analysis for {file_path}:
- Numeric columns: {list(numeric_cols)}
- Summary statistics:
{df.describe().to_string()}
- Missing values: {df.isnull().sum().to_dict()}
"""
        elif analysis_type == "patterns":
            result = f"""Pattern Analysis for {file_path}:
- Unique values per column: {df.nunique().to_dict()}
- Duplicate rows: {df.duplicated().sum()}
- Correlation matrix (numeric columns):
{df.select_dtypes(include=[np.number]).corr().to_string()}
"""
        elif analysis_type == "quality":
            result = f"""Data Quality Analysis for {file_path}:
- Missing values: {df.isnull().sum().to_dict()}
- Duplicate rows: {df.duplicated().sum()}
- Data types consistency: {df.dtypes.to_dict()}
- Potential issues detected:
"""
            # Check for potential issues
            issues = []
            if df.isnull().any().any():
                issues.append("- Contains missing values")
            if df.duplicated().any():
                issues.append("- Contains duplicate rows")
            for col in df.columns:
                if df[col].dtype == 'object':
                    if df[col].str.strip().ne(df[col]).any():
                        issues.append(f"- Column '{col}' has leading/trailing whitespace")
            
            result += "\n".join(issues) if issues else "- No major issues detected"
        
        return result
    
    except Exception as e:
        return f"Error analyzing CSV file {file_path}: {str(e)}"

def create_data_visualization(file_path: str, chart_type: str, x_column: str, y_column: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """
    Creates data visualizations and saves them as files.
    
    Args:
        file_path: Path to the data file
        chart_type: Type of chart ('histogram', 'scatter', 'line', 'bar')
        x_column: Column for X-axis
        y_column: Column for Y-axis (optional for some chart types)
        output_path: Where to save the chart (optional)
    
    Returns:
        Status message
    """
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        df = pd.read_csv(file_path)
        
        plt.figure(figsize=(10, 6))
        
        if chart_type == "histogram":
            plt.hist(df[x_column], bins=30, alpha=0.7)
            plt.xlabel(x_column)
            plt.ylabel("Frequency")
            plt.title(f"Histogram of {x_column}")
            
        elif chart_type == "scatter" and y_column:
            plt.scatter(df[x_column], df[y_column], alpha=0.7)
            plt.xlabel(x_column)
            plt.ylabel(y_column)
            plt.title(f"Scatter plot: {x_column} vs {y_column}")
            
        elif chart_type == "line" and y_column:
            plt.plot(df[x_column], df[y_column])
            plt.xlabel(x_column)
            plt.ylabel(y_column)
            plt.title(f"Line plot: {x_column} vs {y_column}")
            
        elif chart_type == "bar":
            df[x_column].value_counts().plot(kind='bar')
            plt.xlabel(x_column)
            plt.ylabel("Count")
            plt.title(f"Bar chart of {x_column}")
        
        if not output_path:
            output_path = f"{Path(file_path).stem}_{chart_type}_{x_column}.png"
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"Chart saved to {output_path}"
        
    except Exception as e:
        return f"Error creating visualization: {str(e)}"

def perform_data_research(topic: str, data_sources: Optional[List[str]] = None) -> str:
    """
    Performs research on a data-related topic using web search and analysis.
    
    Args:
        topic: Research topic
        data_sources: Optional list of specific data sources to search
    
    Returns:
        Research summary
    """
    # This would integrate with web_tools for research
    research_summary = f"""Research Summary for: {topic}

Data Research Plan:
1. Web search for recent data and statistics
2. Identify credible data sources
3. Analyze trends and patterns
4. Compile findings into actionable insights

Topic: {topic}
Recommended data sources: {data_sources or ['government databases', 'academic papers', 'industry reports']}

Note: This is a framework for data research. Integration with web_tools would provide actual search results.
"""
    return research_summary

# Create specialized data analysis tools with tracking
def tracked_analyze_csv_data(file_path: str, analysis_type: str = "overview", task_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
    """Analyzed CSV data with tracking."""
    tracker = get_tracker(task_id, session_id) if task_id and session_id else None
    
    if tracker:
        tracker.log_tool_call("analyze_csv_data", {"file_path": file_path, "analysis_type": analysis_type})
    
    try:
        result = analyze_csv_data(file_path, analysis_type)
        if tracker:
            tracker.log_tool_call("analyze_csv_data", 
                                {"file_path": file_path, "analysis_type": analysis_type}, 
                                result=result[:200] + "..." if len(result) > 200 else result, 
                                success=True)
        return result
    except Exception as e:
        if tracker:
            tracker.log_tool_call("analyze_csv_data", 
                                {"file_path": file_path, "analysis_type": analysis_type}, 
                                success=False, error_message=str(e))
        raise

def tracked_create_data_visualization(file_path: str, chart_type: str, x_column: str, 
                                     y_column: Optional[str] = None, output_path: Optional[str] = None,
                                     task_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
    """Creates data visualizations with tracking."""
    tracker = get_tracker(task_id, session_id) if task_id and session_id else None
    
    params = {"file_path": file_path, "chart_type": chart_type, "x_column": x_column, "y_column": y_column}
    if tracker:
        tracker.log_tool_call("create_data_visualization", params)
    
    try:
        result = create_data_visualization(file_path, chart_type, x_column, y_column, output_path)
        if tracker:
            tracker.log_tool_call("create_data_visualization", params, result=result, success=True)
        return result
    except Exception as e:
        if tracker:
            tracker.log_tool_call("create_data_visualization", params, success=False, error_message=str(e))
        raise

def tracked_perform_data_research(topic: str, data_sources: Optional[List[str]] = None,
                                 task_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
    """Performs data research with tracking."""
    tracker = get_tracker(task_id, session_id) if task_id and session_id else None
    
    params = {"topic": topic, "data_sources": data_sources}
    if tracker:
        tracker.log_tool_call("perform_data_research", params)
    
    try:
        result = perform_data_research(topic, data_sources)
        if tracker:
            tracker.log_tool_call("perform_data_research", params, result=result[:200] + "..." if len(result) > 200 else result, success=True)
        return result
    except Exception as e:
        if tracker:
            tracker.log_tool_call("perform_data_research", params, success=False, error_message=str(e))
        raise

async def create_autonomous_data_agent(task: Task, workspace_path: str) -> Agent:
    """
    Creates a specialized autonomous data agent with data analysis capabilities.
    """
    
    # Combine all tools for the data agent
    all_tools = []
    
    # Create tracked data-specific tools for this task/session
    task_str = str(task.id)
    session_str = f"data_session_{task.id}"
    
    # Helper to create tracked version of our data functions
    def create_task_specific_tracked_tools():
        def tracked_analyze_csv_data_for_task(file_path: str, analysis_type: str = "overview") -> str:
            return tracked_analyze_csv_data(file_path, analysis_type, task_str, session_str)
        
        def tracked_create_data_visualization_for_task(file_path: str, chart_type: str, x_column: str, 
                                                      y_column: Optional[str] = None, output_path: Optional[str] = None) -> str:
            return tracked_create_data_visualization(file_path, chart_type, x_column, y_column, output_path, task_str, session_str)
        
        def tracked_perform_data_research_for_task(topic: str, data_sources: Optional[List[str]] = None) -> str:
            return tracked_perform_data_research(topic, data_sources, task_str, session_str)
        
        return [
            tracked_analyze_csv_data_for_task,
            tracked_create_data_visualization_for_task,
            tracked_perform_data_research_for_task
        ]
    
    # Add tracked data-specific tools
    all_tools.extend(create_task_specific_tracked_tools())
    
    # Add tracked filesystem tools for file operations
    all_tools.extend(create_tracked_filesystem_tools(task_str, session_str))
    
    # Add tracked cognitive tools for analysis and planning
    all_tools.extend(create_tracked_cognitive_tools(task_str, session_str))
    
    # Add tracked web tools for research
    all_tools.extend(create_tracked_web_tools(task_str, session_str))
    
    instruction = f"""You are an autonomous data analysis and research agent. You have access to a dedicated workspace and comprehensive tools for data analysis, visualization, and research.

**Your Workspace**: {workspace_path}
**Your Capabilities**:
- Load, analyze, and process CSV/Excel files
- Create data visualizations (charts, graphs, plots)
- Perform statistical analysis and pattern detection
- Conduct web research for data sources
- Generate insights and recommendations
- Create comprehensive reports

**Your Mission**:
- Understand data analysis requests deeply
- Proactively explore and analyze data
- Create meaningful visualizations
- Conduct research to enrich analysis
- Provide actionable insights
- Document your findings systematically

**Workflow**:
1. Understand the data analysis goal
2. Load and explore the data
3. Perform appropriate analysis
4. Create visualizations if helpful
5. Research context and benchmarks
6. Generate insights and recommendations
7. Save results in organized format

**Guidelines**:
- Always start with data quality assessment
- Create appropriate visualizations for insights
- Use statistical methods when relevant
- Research context for better interpretation
- Document your analysis process
- Save all outputs in the workspace
- Handle errors gracefully and try alternatives

Be proactive, thorough, and insightful in your data analysis approach."""

    # Apply language preference
    user_language = detect_language(task.task or "")
    language_instruction = get_language_instruction(user_language)
    if language_instruction:
        instruction = f"{language_instruction}\n\n{instruction}"

    agent = Agent(
        name="autonomous_data_agent",
        model=LiteLlm(model=f"openai/{settings.OPENAI_MODEL}"),
        instruction=instruction,
        tools=all_tools
    )
    
    return agent

async def stream_data_analysis_response(task: Task, user_message: str, workspace_path: str, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    Stream response from autonomous data analysis agent with detailed tracking.
    """
    tracker = get_tracker(str(task.id), session_id or f"session_{task.id}")
    
    try:
        # Log data agent activation
        tracker.log_activity(
            agent_name="Data Analysis Agent",
            action_type="AGENT_ACTIVATED",
            description="Data Analysis Agent started processing request",
            details={"workspace_path": workspace_path, "user_message": user_message[:100]}
        )
        
        # Create and configure agent
        data_agent = await create_autonomous_data_agent(task, workspace_path)
        
        # Create session service for Google ADK
        session_service = InMemorySessionService()
        runner = Runner(
            agent=data_agent,
            app_name=settings.PROJECT_NAME,
            session_service=session_service
        )
        
        # Create session
        session = session_service.create_session(
            app_name=settings.PROJECT_NAME,
            user_id=f"data_agent_{task.id}",
            session_id=session_id or f"data_session_{task.id}",
            state={"workspace_path": workspace_path, "task_id": str(task.id), "agent_type": "data_agent"}
        )
        
        # Log agent execution start
        tracker.log_activity(
            agent_name="Data Analysis Agent",
            action_type="EXECUTION_START",
            description="Starting agent execution with Google ADK"
        )
        
        # Stream response with detailed tool usage tracking
        yield f"🔬 **Data Analysis Agent Activated**\n"
        yield f"📊 Workspace: `{workspace_path}`\n"
        yield f"🛠️ Available tools: CSV analysis, data visualization, research\n\n"
        
        response_chunks = []
        
        # Create content for the user message
        content = types.Content(role='user', parts=[types.Part(text=user_message)])
        
        # Execute agent using run_async like in chat_agent
        async for event in runner.run_async(
            user_id=f"data_agent_{task.id}", 
            session_id=session.id, 
            new_message=content
        ):
            if event.is_final_response():
                text = event.content.parts[0].text if event.content and event.content.parts else ""
                response_chunks.append(text)
                yield text
        
        # Log completion
        full_response = "".join(response_chunks)
        tracker.log_activity(
            agent_name="Data Analysis Agent",
            action_type="EXECUTION_COMPLETED",
            description="Data analysis completed successfully",
            details={"response_length": len(full_response)}
        )
        
    except Exception as e:
        tracker.log_activity(
            agent_name="Data Analysis Agent",
            action_type="ERROR",
            description=f"Error in data analysis: {str(e)}",
            success=False,
            error_message=str(e)
        )
        
        logger.error(f"Error in autonomous data agent: {str(e)}", exc_info=True)
        yield f"⚠️ Error in data analysis agent: {str(e)}" 