"""
Multi-Agent System Configuration

This module defines the configuration and behavior settings for the autonomous multi-agent system.
It provides settings for agent behavior, workspace management, routing logic, and system capabilities.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

class AgentCapability(Enum):
    """Defines the core capabilities that agents can have"""
    FILE_OPERATIONS = "file_operations"
    WEB_RESEARCH = "web_research"
    DATA_ANALYSIS = "data_analysis"
    CODE_EXECUTION = "code_execution"
    COGNITIVE_ANALYSIS = "cognitive_analysis"
    TASK_DELEGATION = "task_delegation"
    VISUALIZATION = "visualization"
    DATABASE_ACCESS = "database_access"

class AgentBehavior(Enum):
    """Defines behavioral patterns for agents"""
    AUTONOMOUS = "autonomous"  # Acts independently with minimal guidance
    INTERACTIVE = "interactive"  # Asks for confirmation before major actions
    CONSERVATIVE = "conservative"  # Cautious approach, prefers safe operations
    AGGRESSIVE = "aggressive"  # Proactive, tries multiple approaches

@dataclass
class WorkspaceConfig:
    """Configuration for agent workspaces"""
    base_path: Optional[str] = None
    auto_create_subdirs: bool = True
    max_workspace_size_mb: int = 1000
    cleanup_on_completion: bool = False
    preserve_artifacts: bool = True
    standard_directories: List[str] = field(default_factory=lambda: [
        "data", "output", "temp", "scripts", "reports", "artifacts"
    ])

@dataclass
class AgentConfig:
    """Configuration for individual agents"""
    name: str
    agent_type: str
    capabilities: List[AgentCapability]
    behavior: AgentBehavior = AgentBehavior.AUTONOMOUS
    max_iterations: int = 10
    timeout_seconds: int = 300
    tools_enabled: bool = True
    memory_enabled: bool = True
    delegation_enabled: bool = True
    error_retry_count: int = 3

@dataclass
class RoutingConfig:
    """Configuration for intelligent routing"""
    enable_intelligent_routing: bool = True
    confidence_threshold: float = 0.3
    fallback_to_general: bool = True
    enable_multi_agent_collaboration: bool = True
    max_agent_chain_length: int = 5
    routing_explanation_level: str = "detailed"  # "none", "basic", "detailed"

@dataclass
class SystemConfig:
    """Overall system configuration"""
    # Core settings
    project_name: str = "Elephant Multi-Agent System"
    version: str = "1.0.0"
    debug_mode: bool = False
    
    # Workspace settings
    workspace: WorkspaceConfig = field(default_factory=WorkspaceConfig)
    
    # Routing settings
    routing: RoutingConfig = field(default_factory=RoutingConfig)
    
    # Security settings
    sandbox_mode: bool = True
    allowed_file_extensions: List[str] = field(default_factory=lambda: [
        ".txt", ".md", ".csv", ".json", ".py", ".js", ".html", ".css", ".xml"
    ])
    blocked_commands: List[str] = field(default_factory=lambda: [
        "rm -rf", "del /f", "format", "fdisk", "sudo rm"
    ])
    
    # Performance settings
    max_concurrent_agents: int = 3
    max_memory_usage_mb: int = 2048
    session_timeout_minutes: int = 60
    
    # Logging settings
    log_level: str = "INFO"
    log_agent_interactions: bool = True
    log_tool_usage: bool = True
    log_performance_metrics: bool = True

# Default agent configurations
DEFAULT_AGENT_CONFIGS = {
    "router_agent": AgentConfig(
        name="Intelligent Router",
        agent_type="router",
        capabilities=[AgentCapability.COGNITIVE_ANALYSIS, AgentCapability.TASK_DELEGATION],
        behavior=AgentBehavior.AUTONOMOUS,
        tools_enabled=True
    ),
    
    "general_chat_agent": AgentConfig(
        name="General Chat Assistant",
        agent_type="general_chat",
        capabilities=[
            AgentCapability.FILE_OPERATIONS,
            AgentCapability.WEB_RESEARCH,
            AgentCapability.COGNITIVE_ANALYSIS
        ],
        behavior=AgentBehavior.INTERACTIVE
    ),
    
    "data_analysis_agent": AgentConfig(
        name="Data Analysis Specialist",
        agent_type="data_analysis",
        capabilities=[
            AgentCapability.DATA_ANALYSIS,
            AgentCapability.VISUALIZATION,
            AgentCapability.FILE_OPERATIONS,
            AgentCapability.WEB_RESEARCH
        ],
        behavior=AgentBehavior.AUTONOMOUS,
        max_iterations=15
    ),
    
    "code_development_agent": AgentConfig(
        name="Code Development Specialist",
        agent_type="code_development",
        capabilities=[
            AgentCapability.CODE_EXECUTION,
            AgentCapability.FILE_OPERATIONS,
            AgentCapability.WEB_RESEARCH
        ],
        behavior=AgentBehavior.AUTONOMOUS
    ),
    
    "research_agent": AgentConfig(
        name="Research Specialist",
        agent_type="research",
        capabilities=[
            AgentCapability.WEB_RESEARCH,
            AgentCapability.COGNITIVE_ANALYSIS,
            AgentCapability.FILE_OPERATIONS
        ],
        behavior=AgentBehavior.AUTONOMOUS
    ),
    
    "planning_agent": AgentConfig(
        name="Planning Specialist",
        agent_type="planning",
        capabilities=[
            AgentCapability.COGNITIVE_ANALYSIS,
            AgentCapability.TASK_DELEGATION,
            AgentCapability.FILE_OPERATIONS
        ],
        behavior=AgentBehavior.INTERACTIVE
    )
}

class MultiAgentSystemConfig:
    """Main configuration manager for the multi-agent system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.system = SystemConfig()
        self.agents = DEFAULT_AGENT_CONFIGS.copy()
        
        if config_path and os.path.exists(config_path):
            self.load_from_file(config_path)
    
    def get_agent_config(self, agent_type: str) -> Optional[AgentConfig]:
        """Get configuration for a specific agent type"""
        return self.agents.get(agent_type)
    
    def update_agent_config(self, agent_type: str, config: AgentConfig):
        """Update configuration for a specific agent"""
        self.agents[agent_type] = config
    
    def is_capability_enabled(self, agent_type: str, capability: AgentCapability) -> bool:
        """Check if a specific capability is enabled for an agent"""
        config = self.get_agent_config(agent_type)
        return config is not None and capability in config.capabilities
    
    def get_workspace_path(self, task_id: str) -> str:
        """Get the workspace path for a task"""
        base_path = self.system.workspace.base_path or str(Path.cwd() / "agent_workspaces")
        return str(Path(base_path) / f"task_{task_id}")
    
    def is_file_allowed(self, filename: str) -> bool:
        """Check if a file extension is allowed"""
        file_ext = Path(filename).suffix.lower()
        return file_ext in self.system.allowed_file_extensions
    
    def is_command_blocked(self, command: str) -> bool:
        """Check if a command is blocked for security"""
        command_lower = command.lower()
        return any(blocked in command_lower for blocked in self.system.blocked_commands)
    
    def load_from_file(self, config_path: str):
        """Load configuration from a file (JSON/YAML)"""
        # Implementation for loading from file would go here
        pass
    
    def save_to_file(self, config_path: str):
        """Save configuration to a file"""
        # Implementation for saving to file would go here
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "system": self.system.__dict__,
            "agents": {k: v.__dict__ for k, v in self.agents.items()}
        }

# Global configuration instance
multi_agent_config = MultiAgentSystemConfig()

# Utility functions
def get_agent_capabilities(agent_type: str) -> List[AgentCapability]:
    """Get the capabilities for a specific agent type"""
    config = multi_agent_config.get_agent_config(agent_type)
    return config.capabilities if config else []

def is_autonomous_agent(agent_type: str) -> bool:
    """Check if an agent is configured for autonomous behavior"""
    config = multi_agent_config.get_agent_config(agent_type)
    return config is not None and config.behavior == AgentBehavior.AUTONOMOUS

def get_max_iterations(agent_type: str) -> int:
    """Get the maximum iterations allowed for an agent"""
    config = multi_agent_config.get_agent_config(agent_type)
    return config.max_iterations if config else 10

def should_enable_routing() -> bool:
    """Check if intelligent routing is enabled"""
    return multi_agent_config.system.routing.enable_intelligent_routing

def get_routing_confidence_threshold() -> float:
    """Get the confidence threshold for routing decisions"""
    return multi_agent_config.system.routing.confidence_threshold 