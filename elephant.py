import json
import os
from dotenv import load_dotenv
from src.task import Task
from src.problem_analyzer import ProblemAnalyzer
from src.openai_service import OpenAiService
from src.user_interaction import UserInteraction

def main():
    load_dotenv()
    
    openai_service = OpenAiService(os.getenv("OPENAI_API_KEY"))
    problem_analyzer = ProblemAnalyzer(openai_service)
    user_interaction = UserInteraction()

    origin_query = user_interaction.greeting()

    task = Task(origin_query)

    problem_analyzer.analyze(task)

    print(f"Task ID: {task.id}")
    print(f"State: {task.state}")
    print(f"Analysis results:")
    print(json.dumps(task.analysis, indent=2))

if __name__ == "__main__":
    main()
