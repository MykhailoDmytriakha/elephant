import json
import os

from dotenv import load_dotenv

from src.database_service import DatabaseService
from src.openai_service import OpenAiService
from src.problem_analyzer import ProblemAnalyzer
from src.task import Task
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


def print_task_tree(task: Task, indent: str = ""):
    complexity = task.analysis.get('complexity', 'N/A')
    print(f"{indent}├────── Description: {task.task}")
    print(f"{indent}│       Complexity: {complexity}")
    print(f"{indent}│       SUB-LEVEL: {task.sub_level}")

    # Print sub-tasks
    for i, sub_task in enumerate(task.sub_tasks):
        if i == len(task.sub_tasks) - 1:
            # Last sub-task
            print(f"{indent}│   │")
            print_task_tree(sub_task, indent + "    ")
        else:
            # Not the last sub-task
            print(f"{indent}│   │")
            print_task_tree(sub_task, indent + "│   ")


def print_task(task: Task):
    print(f"{json.dumps(task.to_dict(), indent=2, ensure_ascii=False)}")


def main():
    load_dotenv()

    openai_service = OpenAiService(os.getenv("OPENAI_API_KEY"))
    db_service = DatabaseService("data/tasks.db")
    problem_analyzer = ProblemAnalyzer(openai_service, db_service)
    user_interaction = UserInteraction()

    origin_query = user_interaction.greeting()
    task = Task()
    task.short_description = origin_query

    db_service.insert_task(task)
    db_service.insert_user_query(task.id, origin_query)

    problem_analyzer.clarify_context(task)
    problem_analyzer.analyze(task)
    problem_analyzer.decompose(task)

    problem_analyzer.concept_formation(task)

    print("\nTask Tree:")
    print_task_tree(task)

    print("\nTask Info:")
    print_task(task)


if __name__ == "__main__":
    main()
