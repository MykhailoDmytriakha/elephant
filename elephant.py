import json
import os
from dotenv import load_dotenv
from src.task import Task
from src.problem_analyzer import ProblemAnalyzer
from src.openai_service import OpenAiService
from src.user_interaction import UserInteraction

def print_task_info(task: Task, indent: str = ""):
    print(f"{indent}Task ID: {task.id}")
    print(f"{indent}State: {task.state}")
    print(f"{indent}Analysis results:")
    print(json.dumps(task.analysis, indent=2))
    if task.sub_tasks:
        print(f"{indent}Sub-tasks:")
        for sub_task in task.sub_tasks:
            print_task_info(sub_task, indent + "  ")

def main():
    load_dotenv()
    
    openai_service = OpenAiService(os.getenv("OPENAI_API_KEY"))
    problem_analyzer = ProblemAnalyzer(openai_service)
    user_interaction = UserInteraction()

    origin_query = user_interaction.greeting()

    task = Task(origin_query)
    problem_analyzer.clarify_context(task)
    problem_analyzer.analyze(task)

    print(json.dumps(task.to_dict(), indent=2))

if __name__ == "__main__":
    main()