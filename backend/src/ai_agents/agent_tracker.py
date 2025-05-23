import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)

@dataclass
class AgentActivity:
    """Класс для отслеживания активности агента"""
    timestamp: str
    agent_name: str
    action_type: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class ToolCall:
    """Класс для отслеживания вызовов инструментов"""
    timestamp: str
    tool_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None

@dataclass
class AgentTransfer:
    """Класс для отслеживания передач между агентами"""
    timestamp: str
    from_agent: str
    to_agent: str
    reason: str
    context: Dict[str, Any] = field(default_factory=dict)
    confidence_score: Optional[float] = None

class AgentTracker:
    """Централизованный трекер активности агентов"""
    
    def __init__(self, task_id: str, session_id: str):
        self.task_id = task_id
        self.session_id = session_id
        self.activities: List[AgentActivity] = []
        self.tool_calls: List[ToolCall] = []
        self.agent_transfers: List[AgentTransfer] = []
        self.start_time = datetime.now(timezone.utc)
        self.current_agent = "Router"
        
    def _get_timestamp(self) -> str:
        """Получить текущий timestamp"""
        return datetime.now(timezone.utc).isoformat()
    
    def log_activity(self, agent_name: str, action_type: str, description: str, 
                    details: Optional[Dict[str, Any]] = None, success: bool = True, 
                    error_message: Optional[str] = None) -> None:
        """Логирование активности агента"""
        activity = AgentActivity(
            timestamp=self._get_timestamp(),
            agent_name=agent_name,
            action_type=action_type,
            description=description,
            details=details or {},
            success=success,
            error_message=error_message
        )
        self.activities.append(activity)
        logger.info(f"Agent Activity: {agent_name} - {action_type} - {description}")
    
    def log_tool_call(self, tool_name: str, parameters: Optional[Dict[str, Any]] = None,
                     result: Optional[str] = None, success: bool = True,
                     error_message: Optional[str] = None, 
                     execution_time_ms: Optional[float] = None) -> None:
        """Логирование вызова инструмента"""
        tool_call = ToolCall(
            timestamp=self._get_timestamp(),
            tool_name=tool_name,
            parameters=parameters or {},
            result=result,
            success=success,
            error_message=error_message,
            execution_time_ms=execution_time_ms
        )
        self.tool_calls.append(tool_call)
        logger.info(f"Tool Call: {tool_name} - {'Success' if success else 'Failed'}")
    
    def log_agent_transfer(self, from_agent: str, to_agent: str, reason: str,
                          context: Optional[Dict[str, Any]] = None, 
                          confidence_score: Optional[float] = None) -> None:
        """Логирование передачи между агентами"""
        transfer = AgentTransfer(
            timestamp=self._get_timestamp(),
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason,
            context=context or {},
            confidence_score=confidence_score
        )
        self.agent_transfers.append(transfer)
        self.current_agent = to_agent
        logger.info(f"Agent Transfer: {from_agent} → {to_agent} (reason: {reason})")
    
    def get_summary(self) -> Dict[str, Any]:
        """Получить сводку по всей активности"""
        total_time = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "total_time_seconds": total_time,
            "current_agent": self.current_agent,
            "total_activities": len(self.activities),
            "total_tool_calls": len(self.tool_calls),
            "total_transfers": len(self.agent_transfers),
            "agents_used": list(set([transfer.to_agent for transfer in self.agent_transfers] + ["Router"])),
            "tools_used": list(set([call.tool_name for call in self.tool_calls])),
            "success_rate": {
                "activities": sum(1 for a in self.activities if a.success) / len(self.activities) if self.activities else 1.0,
                "tool_calls": sum(1 for t in self.tool_calls if t.success) / len(self.tool_calls) if self.tool_calls else 1.0
            }
        }
    
    def format_trace(self) -> str:
        """Форматировать полную трассировку выполнения"""
        trace_lines = [
            "🔍 **Agent Execution Trace**",
            f"📋 Task: {self.task_id}",
            f"🔗 Session: {self.session_id}",
            f"⏱️ Duration: {(datetime.now(timezone.utc) - self.start_time).total_seconds():.2f}s",
            ""
        ]
        
        # Agent transfers
        if self.agent_transfers:
            trace_lines.append("�� **Agent Routing:**")
            for transfer in self.agent_transfers:
                confidence = f" (confidence: {transfer.confidence_score:.2f})" if transfer.confidence_score else ""
                trace_lines.append(f"  • {transfer.from_agent} → **{transfer.to_agent}**{confidence}")
                trace_lines.append(f"    Reason: {transfer.reason}")
            trace_lines.append("")
        
        # Tool calls
        if self.tool_calls:
            trace_lines.append("🛠️ **Tools Used:**")
            tool_summary = {}
            for call in self.tool_calls:
                if call.tool_name not in tool_summary:
                    tool_summary[call.tool_name] = {"count": 0, "success": 0}
                tool_summary[call.tool_name]["count"] += 1
                if call.success:
                    tool_summary[call.tool_name]["success"] += 1
            
            for tool, stats in tool_summary.items():
                success_rate = stats["success"] / stats["count"]
                status = "✅" if success_rate == 1.0 else "⚠️" if success_rate > 0.5 else "❌"
                trace_lines.append(f"  • {status} {tool}: {stats['count']} calls ({stats['success']}/{stats['count']} successful)")
            trace_lines.append("")
        
        # Recent activities
        if self.activities:
            trace_lines.append("📝 **Recent Activities:**")
            for activity in self.activities[-5:]:  # Show last 5 activities
                status = "✅" if activity.success else "❌"
                trace_lines.append(f"  • {status} [{activity.agent_name}] {activity.description}")
            trace_lines.append("")
        
        return "\n".join(trace_lines)
    
    def to_json(self) -> str:
        """Экспорт в JSON формат"""
        return json.dumps({
            "summary": self.get_summary(),
            "activities": [activity.__dict__ for activity in self.activities],
            "tool_calls": [call.__dict__ for call in self.tool_calls],
            "agent_transfers": [transfer.__dict__ for transfer in self.agent_transfers]
        }, indent=2)

# Глобальный реестр трекеров
_trackers: Dict[str, AgentTracker] = {}

def get_tracker(task_id: str, session_id: str) -> AgentTracker:
    """Получить или создать трекер для задачи"""
    key = f"{task_id}_{session_id}"
    if key not in _trackers:
        _trackers[key] = AgentTracker(task_id, session_id)
    return _trackers[key]

def remove_tracker(task_id: str, session_id: str) -> None:
    """Удалить трекер"""
    key = f"{task_id}_{session_id}"
    if key in _trackers:
        del _trackers[key] 