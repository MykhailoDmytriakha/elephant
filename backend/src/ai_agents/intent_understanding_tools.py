"""
Intent Understanding Tools for AI Agents

This module helps agents better understand user intents, especially when users reference
specific task IDs like S1_W1_ET1_ST1, and provides proper context checking for both
workspace and database.

Problem solved: Agents not understanding specific task references and not checking both sources.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from src.ai_agents.workspace_manager import get_workspace_manager
from src.ai_agents.agent_tracker import get_tracker

logger = logging.getLogger(__name__)

class IntentUnderstandingTools:
    """Tools for better understanding user intents"""
    
    def __init__(self, task_id: str, session_id: str):
        self.task_id = task_id
        self.session_id = session_id
        self.workspace_manager = get_workspace_manager()
        self.tracker = get_tracker(task_id, session_id)
    
    def parse_task_reference(self, user_message: str) -> Optional[Dict[str, str]]:
        """
        Parses task references like S1_W1_ET1_ST1 from user message.
        
        Args:
            user_message: User's message to parse
            
        Returns:
            Dictionary with parsed components or None if no match
        """
        # Pattern for task references: S1_W1_ET1_ST1
        pattern = r'([Ss]\d+)_([Ww]\d+)_([EeTt]+\d+)_([Ss][Tt]\d+)'
        match = re.search(pattern, user_message)
        
        if match:
            stage_id = match.group(1).upper()
            work_id = stage_id + "_" + match.group(2).upper()
            executable_task_id = work_id + "_" + match.group(3).upper()
            subtask_id = executable_task_id + "_" + match.group(4).upper()
            
            return {
                "full_reference": match.group(0),
                "stage_id": stage_id,
                "work_id": work_id,
                "executable_task_id": executable_task_id,
                "subtask_id": subtask_id,
                "type": "subtask"
            }
        
        # Pattern for executable task references: S1_W1_ET1
        pattern = r'([Ss]\d+)_([Ww]\d+)_([EeTt]+\d+)(?!_[Ss][Tt])'
        match = re.search(pattern, user_message)
        
        if match:
            stage_id = match.group(1).upper()
            work_id = stage_id + "_" + match.group(2).upper()
            executable_task_id = work_id + "_" + match.group(3).upper()
            
            return {
                "full_reference": match.group(0),
                "stage_id": stage_id,
                "work_id": work_id,
                "executable_task_id": executable_task_id,
                "type": "executable_task"
            }
        
        return None
    
    def analyze_intent(self, user_message: str) -> Dict[str, Any]:
        """
        Analyzes user intent and provides structured understanding.
        
        Args:
            user_message: User's message
            
        Returns:
            Dictionary with intent analysis
        """
        message_lower = user_message.lower()
        
        # Check for task reference
        task_ref = self.parse_task_reference(user_message)
        
        # Check for status questions
        status_keywords = ['выполнена', 'выполнен', 'статус', 'status', 'completed', 'done', 'finished']
        asking_status = any(keyword in message_lower for keyword in status_keywords)
        
        # Check for check/verify keywords
        check_keywords = ['проверить', 'проверь', 'check', 'verify', 'посмотри', 'look']
        asking_check = any(keyword in message_lower for keyword in check_keywords)
        
        # Check for database/workspace references
        db_keywords = ['база', 'db', 'database', 'базе данных']
        workspace_keywords = ['workspace', 'воркспейс', 'папка', 'файл']
        
        mentions_db = any(keyword in message_lower for keyword in db_keywords)
        mentions_workspace = any(keyword in message_lower for keyword in workspace_keywords)
        
        return {
            "task_reference": task_ref,
            "asking_status": asking_status,
            "asking_check": asking_check,
            "mentions_database": mentions_db,
            "mentions_workspace": mentions_workspace,
            "should_check_both": task_ref and asking_status,  # If asking about specific task status
            "intent_type": self._determine_intent_type(task_ref, asking_status, asking_check)
        }
    
    def _determine_intent_type(self, task_ref: Optional[Dict], asking_status: bool, asking_check: bool) -> str:
        """Determines the primary intent type"""
        if task_ref and asking_status:
            return "task_status_inquiry"
        elif task_ref and asking_check:
            return "task_verification"
        elif asking_status:
            return "general_status_inquiry"
        elif asking_check:
            return "general_check"
        else:
            return "general_chat"
    
    def check_task_completion_status(self, task_reference: Dict[str, str]) -> Dict[str, Any]:
        """
        Checks completion status of a specific task in both workspace and database.
        
        Args:
            task_reference: Parsed task reference
            
        Returns:
            Status information from both sources
        """
        workspace_status = self._check_workspace_status(task_reference)
        database_status = self._check_database_status(task_reference)
        
        result: Dict[str, Any] = {
            "workspace_status": workspace_status,
            "database_status": database_status,
            "summary": "no_evidence"  # Default value
        }
        
        # Create summary based on evidence found
        workspace_exists = workspace_status.get("evidence_found", False)
        db_exists = database_status.get("evidence_found", False)
        
        if workspace_exists and db_exists:
            result["summary"] = "completed_both"
        elif workspace_exists and not db_exists:
            result["summary"] = "completed_workspace_only"
        elif not workspace_exists and db_exists:
            result["summary"] = "completed_database_only"
        else:
            result["summary"] = "no_evidence"
        
        return result
    
    def _check_workspace_status(self, task_ref: Dict[str, str]) -> Dict[str, Any]:
        """Check workspace for evidence of task completion"""
        workspace_path = self.workspace_manager.get_workspace_path(self.task_id)
        
        # For S1_W1_ET1_ST1, we expect config.yml file creation
        if task_ref["subtask_id"] == "S1_W1_ET1_ST1":
            config_path = f"{workspace_path}/config/config.yml"
            try:
                with open(config_path, 'r') as f:
                    content = f.read()
                
                return {
                    "evidence_found": True,
                    "evidence_type": "config_file",
                    "file_path": config_path,
                    "file_content": content[:200] + "..." if len(content) > 200 else content,
                    "details": "Found config.yml file in workspace config directory"
                }
            except FileNotFoundError:
                return {
                    "evidence_found": False,
                    "evidence_type": "missing_file",
                    "expected_path": config_path,
                    "details": "Config.yml file not found in expected location"
                }
        
        # Generic check for other tasks
        return {
            "evidence_found": False,
            "evidence_type": "not_implemented",
            "details": f"Workspace check not implemented for {task_ref['subtask_id']}"
        }
    
    def _check_database_status(self, task_ref: Dict[str, str]) -> Dict[str, Any]:
        """Check database for task status"""
        # This would connect to actual database
        # For now, returning placeholder
        return {
            "evidence_found": False,
            "evidence_type": "not_implemented",
            "details": f"Database check not implemented for {task_ref['subtask_id']}"
        }
    
    def generate_smart_response(self, user_message: str) -> str:
        """
        Generates a smart response based on intent analysis.
        
        Args:
            user_message: User's original message
            
        Returns:
            Structured response with proper checking
        """
        intent = self.analyze_intent(user_message)
        
        if intent["intent_type"] == "task_status_inquiry":
            task_ref = intent.get("task_reference")
            if not task_ref:
                return "Не удалось найти ссылку на задачу в сообщении."
                
            status = self.check_task_completion_status(task_ref)
            
            response = f"## 🔍 Статус задачи {task_ref.get('full_reference', 'Unknown')}\n\n"
            
            # Workspace status
            ws_status = status.get("workspace_status", {})
            if ws_status.get("evidence_found", False):
                response += f"✅ **В workspace**: ВЫПОЛНЕНА\n"
                response += f"   • {ws_status.get('details', 'No details')}\n"
                if 'file_path' in ws_status:
                    response += f"   • Файл: `{ws_status['file_path']}`\n"
            else:
                response += f"❌ **В workspace**: НЕ НАЙДЕНО\n"
                response += f"   • {ws_status.get('details', 'No details')}\n"
            
            # Database status
            db_status = status.get("database_status", {})
            response += f"\n🗄️ **В базе данных**: {db_status.get('details', 'No details')}\n"
            
            # Summary
            summary = status.get("summary", "no_evidence")
            if summary == "completed_workspace_only":
                response += f"\n**ВЫВОД**: Задача выполнена в workspace, но не зафиксирована в БД"
            elif summary == "no_evidence":
                response += f"\n**ВЫВОД**: Нет свидетельств выполнения задачи"
            
            return response
        
        else:
            return f"Понял запрос как: {intent['intent_type']}. Могу помочь с более детальной проверкой."
    
    def check_task_from_message(self, user_message: str) -> Dict[str, Any]:
        """
        Wrapper function that handles complete task checking flow from user message.
        This prevents the argument error by properly parsing the message first.
        
        Args:
            user_message: User's message containing task reference
            
        Returns:
            Complete analysis and status check result
        """
        # Parse the task reference from the message
        task_ref = self.parse_task_reference(user_message)
        
        if not task_ref:
            return {
                "error": "No task reference found in message",
                "message": user_message,
                "success": False
            }
        
        # Analyze intent
        intent = self.analyze_intent(user_message)
        
        # Check completion status
        status = self.check_task_completion_status(task_ref)
        
        return {
            "success": True,
            "task_reference": task_ref,
            "intent_analysis": intent,
            "completion_status": status,
            "smart_response": self.generate_smart_response(user_message)
        }

    def update_task_status_from_message(self, user_message: str) -> Dict[str, Any]:
        """
        Update task status by extracting task reference from user message.
        This is a safe wrapper that handles the complete flow.
        
        Args:
            user_message: User's message containing task reference or update intent
            
        Returns:
            Update result with success status
        """
        # Parse the task reference from the message
        task_ref = self.parse_task_reference(user_message)
        
        if not task_ref:
            # Default to S1_W1_ET1_ST1 if no task reference found
            task_reference = "S1_W1_ET1_ST1"
            self.tracker.log_activity(
                agent_name="IntentUnderstanding",
                action_type="DEFAULT_TASK",
                description=f"No task reference found in message, defaulting to {task_reference}"
            )
        else:
            task_reference = task_ref["full_reference"]
            self.tracker.log_activity(
                agent_name="IntentUnderstanding", 
                action_type="TASK_PARSED",
                description=f"Extracted task reference: {task_reference}"
            )
        
        # Import task execution tools
        from src.ai_agents.task_execution_tools import TaskExecutionTools
        
        # Create task execution tools instance
        execution_tools = TaskExecutionTools(self.task_id, self.session_id)
        
        # Execute the complete task flow to mark as complete
        try:
            result = execution_tools.mark_last_checked_task_complete(task_reference)
            
            self.tracker.log_activity(
                agent_name="IntentUnderstanding",
                action_type="TASK_UPDATE",
                description=f"Updated task {task_reference} status: {result.get('final_status', 'Unknown')}"
            )
            
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "task_id": task_reference,
                "error": str(e),
                "summary": f"Failed to update task status: {str(e)}"
            }
            
            self.tracker.log_activity(
                agent_name="IntentUnderstanding",
                action_type="TASK_UPDATE_ERROR", 
                description=f"Error updating task {task_reference}: {str(e)}"
            )
            
            return error_result

def create_intent_understanding_tools(task_id: str, session_id: str) -> List:
    """Creates intent understanding tools for better user interaction"""
    intent_tools = IntentUnderstandingTools(task_id, session_id)
    
    return [
        intent_tools.parse_task_reference,
        intent_tools.analyze_intent,
        intent_tools.check_task_from_message,  # Use safe wrapper instead of direct method
        intent_tools.generate_smart_response,
        intent_tools.update_task_status_from_message
    ] 