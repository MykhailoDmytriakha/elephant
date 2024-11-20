from src.model.task import Task

TYPIFY_TASK_FUNCTIONS = [{
            "name": "typify_task",
            "description": "Analyze and classify the task according to specific criteria",
            "parameters": {
                "type": "object",
                "properties": {
                    "typification": {
                    "type": "object",
                        "properties": {
                            "classification": {
                                "description": "Classification of the task according to specific criteria",
                                "type": "object",
                                "properties": {
                                    "nature": {
                                        "description": "Classification of the task according to its nature",
                                        "type": "object",
                                        "properties": {
                                            "primary": {"type": "string", "enum": ["ANALYTICAL", "SYNTHETIC", "OPTIMIZATION", "TRANSFORMATION"]},
                                            "secondary": {"type": "array", "items": {"type": "string"}},
                                            "reasoning": {"type": "string"}
                                        },
                                        "required": ["primary", "secondary", "reasoning"]
                                    },
                                    "domain": {
                                        "description": "Classification of the task according to its domain",
                                        "type": "object",
                                        "properties": {
                                            "primary": {"type": "string", "enum": ["TECHNICAL", "BUSINESS", "EDUCATIONAL", "RESEARCH"]},
                                            "aspects": {"type": "array", "items": {"type": "string"}},
                                            "reasoning": {"type": "string"}
                                        },
                                        "required": ["primary", "aspects", "reasoning"]
                                    },
                                    "structure": {
                                        "description": "Classification of the task according to its structure: LINEAR (direct path), BRANCHING (multiple options), CYCLIC (repetitive), SYSTEMIC (complex)",
                                        "type": "object",
                                        "properties": {
                                            "type": {"type": "string", "enum": ["LINEAR", "BRANCHING", "CYCLIC", "SYSTEMIC"]},
                                            "characteristics": {"type": "array", "items": {"type": "string"}},
                                            "reasoning": {"type": "string"}
                                        },
                                        "required": ["type", "characteristics", "reasoning"]
                                    },
                                    "complexity_level": {
                                        "description": "Classification of the task according to its complexity level",
                                        "type": "object",
                                        "properties": {
                                            "level": {"type": "string", "enum": ["LEVEL_1 (simple task: solution is known and easy to apply)", "LEVEL_2 (complex task: requires adaptation of known solutions)", "LEVEL_3 (very complex task: requires combining several approaches)", "LEVEL_4 (task with high level of innovation: requires creation of a new solution within the current paradigm)", "LEVEL_5 (task with the highest level of innovation: requires creation of a fundamentally new solution, possibly changing the paradigm)"]},
                                            "factors": {"type": "array", "items": {"type": "string"}},
                                            "reasoning": {"type": "string"}
                                        },
                                        "required": ["level", "factors", "reasoning"]
                                    }
                                },
                                "required": ["nature", "domain", "structure", "complexity_level"]
                            },
                            "methodology": {
                                "description": "Classification of the task according to its methodology: TRIZ, Scientific Method, ARIZ, TOP-TRIZ, Design Thinking, Six Sigma, Agile, Systems Thinking, Lean, Theory of Constraints, Lateral Thinking, Root Cause Analysis",
                                "type": "object",
                                "properties": {
                                    "primary": {"type": "string"},
                                    "supporting": {"type": "array", "items": {"type": "string"}},
                                    "principles": {"type": "array", "items": {"type": "string"}},
                                    "selection_reasoning": {"type": "string"},
                                    "application_guidelines": {"type": "array", "items": {"type": "string"}}
                                },
                                "required": ["primary", "supporting", "principles", "selection_reasoning", "application_guidelines"]
                            },
                            "system_analysis": {
                                "description": "Analysis of the task in the context of the system hierarchy: micro - micro level (components, subsystems, system), meso - meso level (subsystems, system), macro - macro level (system)",
                                "type": "object",
                                "properties": {
                                    "system_level": {"type": "string", "enum": ["micro", "meso", "macro"]},
                                    "super_system": {
                                        "description": "Analysis of the super system (broader context)",
                                        "type": "object",
                                        "properties": {
                                            "components": {"type": "array", "items": {"type": "string"}},
                                            "interactions": {"type": "array", "items": {"type": "string"}}
                                        },
                                        "required": ["components", "interactions"]
                                    },
                                    "system": {
                                        "description": "Analysis of the system",
                                        "type": "object",
                                        "properties": {
                                            "components": {"type": "array", "items": {"type": "string"}},
                                            "interactions": {"type": "array", "items": {"type": "string"}}
                                        },
                                        "required": ["components", "interactions"]
                                    },
                                    "sub_systems": {
                                        "description": "Analysis of subsystems",
                                        "type": "object",
                                        "properties": {
                                            "components": {"type": "array", "items": {"type": "string"}},
                                            "interactions": {"type": "array", "items": {"type": "string"}}
                                        },
                                        "required": ["components", "interactions"]
                                    }
                                },
                                "required": ["system_level", "super_system", "system", "sub_systems"]
                            },
                            "solution_characteristics": {
                                "description": "Analysis of the required solution characteristics",
                                "type": "object",
                                "properties": {
                                    "required_resources": {"type": "array", "items": {"type": "string"}},
                                    "key_constraints": {"type": "array", "items": {"type": "string"}},
                                    "critical_factors": {"type": "array", "items": {"type": "string"}},
                                    "success_criteria": {"type": "array", "items": {"type": "string"}}
                                },
                                "required": ["required_resources", "key_constraints", "critical_factors", "success_criteria"]
                            },
                            "eta": {
                                "description": "Estimated time to complete the task",
                                "type": "object",
                                "properties": {"time": {"type": "string"}, "reasoning": {"type": "string"}},
                                "required": ["time", "reasoning"]
                            }
                        },
                        "required": ["classification", "methodology", "system_analysis", "solution_characteristics", "eta"]
                    }
                },
                "required": ["typification"]
            }
        }]

TYPIFY_TASK_TOOLS = [
    {
        "type": "function",
        "function": TYPIFY_TASK_FUNCTIONS[0],
        "strict": True
    }
]

def get_typify_task_prompt(task: Task) -> str:
    return f"""
        You are a Problem Typization Expert. Your task is to analyze the provided analysis results and classify the problem according to specific criteria.
        
        Input Analysis Results:
        Task: {task.task}
        Task description: {task.short_description}
        Task context: {task.context}
        Ideal Final Result: {task.analysis.get('ideal_final_result')}
        Parameters: {task.analysis.get('parameters')}
        Constraints: {task.analysis.get('constraints')}
        Current Limitations: {task.analysis.get('current_limitations')}
        Contradictions: {task.analysis.get('contradictions')}
        Available Resources: {task.analysis.get('available_resources')}
        Required Resources: {task.analysis.get('required_resources')}
        Missing Information: {task.analysis.get('missing_information')}

        Provide a comprehensive typization of this task following these steps:

        1. Classification:
            a) Nature Classification:
                - Determine if the task is primarily ANALYTICAL, SYNTHETIC, OPTIMIZATION, or TRANSFORMATION
                - Identify any secondary natures if the task is combined
                - Provide clear reasoning for your classification
            
            b) Domain Classification:
                - Identify the primary domain (TECHNICAL, BUSINESS, EDUCATIONAL, RESEARCH)
                - List any additional relevant domains
                - Explain domain relationships and why they apply
            
            c) Structure Classification:
                - Determine if the task structure is LINEAR, BRANCHING, CYCLIC, or SYSTEMIC
                - List key structural characteristics
                - Explain why this structure applies
            
            d) Complexity Level Assessment:
                - Assign a level from 1 to 5 based on TRIZ methodology
                - List complexity factors
                - Provide detailed reasoning for the assigned level

        2. Methodology Selection:
        - Select the most appropriate primary methodology
        - Identify supporting methodologies
        - List key principles to apply
        - Explain methodology selection rationale
        - Provide specific application guidelines

        3. System Analysis:
        - Determine the system level (micro/meso/macro)
        - Identify super-system components and interactions
        - List system components and their interactions
        - Describe sub-system elements and relationships

        4. Solution Characteristics:
        - List required resources
        - Identify key constraints
        - Define critical success factors
        - Establish success criteria

        5. Time Estimation:
        - Provide time estimate
        - Explain reasoning for the estimate

        Remember to be specific and provide clear reasoning for each classification and selection. Focus on practical applicability of your typization.
        """
