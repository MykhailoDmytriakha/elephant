from src.model.task import Task
import json

CLARIFYING_QUESTIONS_FUNCTIONS = [{
            "name": "generate_questions",
            "description": "Generate clarifying questions for the task",
            "parameters": {
                "type": "object",
                "properties": {
                    "questions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question_id": {"type": "string"},
                                "question": {"type": "string"},
                                "purpose": {"type": "string"},
                                "expected_value": {"type": "string"},
                                "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                                "dependencies": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["question_id", "question", "purpose", 
                                    "expected_value", "priority"]
                        }
                    },
                    "stop_criteria": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Conditions when to stop asking questions"
                    }
                },
                "required": ["questions", "stop_criteria"]
            }
        }]

CLARIFYING_QUESTIONS_TOOLS = [
    {
        "type": "function",
        "function": CLARIFYING_QUESTIONS_FUNCTIONS[0],
        "strict": True
    }
]

def get_clarifying_questions_prompt(task: Task) -> str:
    return f"""
        Based on the task analysis and typification:
        
        Analysis Results:
        - Missing Information: {task.analysis.get('missing_information', [])}
        - Parameters: {task.analysis.get('parameters', [])}
        - Constraints: {task.analysis.get('constraints', [])}
        
        Typification:
        {json.dumps(task.typification, indent=2)}
        
        Generate a set of clarifying questions that will:
        1. Fill gaps in missing information
        2. Understand user preferences and constraints
        3. Validate assumptions from analysis
        4. Gather information needed for approaches
        
        Questions should be:
        - Specific and focused
        - Prioritized by importance
        - Dependent on previous answers where relevant
        - Aimed at gathering actionable information
        
        Include stop criteria that indicate when enough information 
        has been gathered to proceed with approaches generation.
        """