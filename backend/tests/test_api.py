import pytest
import requests
import subprocess
import time
import signal
import os
import logging

logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

@pytest.fixture(scope="session", autouse=True)
def start_app():
    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to the backend directory
    backend_dir = os.path.dirname(current_dir)
    # Path to the src directory
    src_dir = os.path.join(backend_dir, "src")
    
    # Print debugging information
    print(f"Current working directory: {os.getcwd()}")
    print(f"Backend directory: {backend_dir}")
    print(f"Src directory: {src_dir}")
    print(f"Files in src directory: {os.listdir(src_dir)}")
    
    # Start the application
    process = subprocess.Popen(
        ["uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=backend_dir
    )
    
    # Wait for the app to start
    max_retries = 5
    for _ in range(max_retries):
        try:
            requests.get(f"{BASE_URL}/")
            break
        except requests.ConnectionError:
            time.sleep(2)
    else:
        pytest.fail("Failed to start the application")
    
    yield  # This is where the testing happens
    
    # Shutdown the app after tests
    process.send_signal(signal.SIGINT)
    process.wait()

def test_get_all_user_queries():
    response = requests.get(f"{BASE_URL}/user-queries")
    print(f"RESULT_RESPONSE: test_get_all_user_queries: {response.json()}")
    assert response.status_code == 200
    # [{'id': 1, 'task_id': 'd6f9ce2e-472e-4ea6-8359-cff5042e04af', 'origin_query': 'что такое блокчейн?'}, {'id': 2, 'task_id': 'ae3c15d9-62dc-4c46-bb90-c0ad56e67f17', 'origin_query': 'как работает интерне?'}, {'id': 3, 'task_id': 'c0719c00-376d-4398-83d6-150d628ac50b', 'origin_query': 'как работает интернет?'}, {'id': 4, 'task_id': 'eacaaeb9-5d9c-425d-a50c-88a943547de1', 'origin_query': 'как работает интернет?'}, {'id': 5, 'task_id': '52f95776-004b-4136-b165-9786e08bdbd1', 'origin_query': 'как со 100 дол сделать 1000'}, {'id': 6, 'task_id': '1c2c0a37-ecf4-4343-bae0-12c217f5312f', 'origin_query': 'я хочу дать ребенку задание для финансовой грамотности с 1 дол сделать 100'}, {'id': 7, 'task_id': '12b6e628-e4b8-433e-add6-9d325cb0b02e', 'origin_query': 'ребенку по финансовой грамоности дали задание 1 доллар превратить в 100. нужны шаги как это сделать'}, {'id': 8, 'task_id': '3e005624-4afd-4c80-b0d3-f004ecb90880', 'origin_query': 'ребенку по финансовой грамоности дали задание 1 доллар превратить в 100. нужны шаги как это сделать'}, {'id': 9, 'task_id': '19727c58-95cc-4c3b-b5df-db39206a8b09', 'origin_query': 'как написать программу'}, {'id': 10, 'task_id': 'c06965b2-6020-4f37-9191-089cbb1df0ec', 'origin_query': 'о чем 40 глава книги пророка Исаии?'}, {'id': 11, 'task_id': 'c6503884-ce15-4628-9f26-4173ad6aa492', 'origin_query': 'изучить исаии 40 главу'}, {'id': 12, 'task_id': 'd29184be-09a5-482c-a5ee-c5edbd33869c', 'origin_query': 'изучить исаии 40 главу'}, {'id': 13, 'task_id': '7c0425bf-a8ae-47b4-a5db-7e4f777044da', 'origin_query': 'изучить исаии 40 главу'}, {'id': 14, 'task_id': 'a4ae2179-3856-45ab-8dec-a5c61137e351', 'origin_query': 'хочу понять стих из Библии о крещении для мертвых'}, {'id': 15, 'task_id': 'b0282457-224e-4b43-8e59-dfa9809f642c', 'origin_query': 'как работает интернет?'}, {'id': 16, 'task_id': '6f61c34d-f09a-4fd8-abcb-098a7609313c', 'origin_query': 'проверка апи'}, {'id': 17, 'task_id': '1ea6cf53-9cf3-4f8d-9547-6f6ea6ef9bcd', 'origin_query': 'есть технологии по декомпозировки задач, нужно сделать алгоритм декомпозиции'}, {'id': 18, 'task_id': '7d49ecbf-082a-4e80-8eb7-40044bdb3d6c', 'origin_query': 'меня интересует методолгия или алгоритм декомпозиции задача (любой задачи)'}, {'id': 19, 'task_id': '3ef5f0ef-5b96-4a4a-b8c7-991e53324899', 'origin_query': 'меня интересует методолгия или алгоритм декомпозиции задача (любой задачи). я работаю над приложение которое будет это делать, хочу научиться работать с AI агентами'}, {'id': 20, 'task_id': 'b993ffb3-9c3b-4b97-a15b-15710af41b98', 'origin_query': 'как нужно анализировать любую проблему?'}, {'id': 21, 'task_id': '03cdc014-9518-4e84-af82-14a45ad40dea', 'origin_query': '(2+2) * 3 + 17 * (4-12) + x = 0'}, {'id': 22, 'task_id': 'de16728f-835c-4f8f-a12a-15dc3057912f', 'origin_query': 'What is the status of my order?'}, {'id': 23, 'task_id': '5e87a9fc-7a12-4c43-95ee-b43735ccda97', 'origin_query': 'how blockchain works?'}, {'id': 24, 'task_id': 'cb84526b-1848-4c68-afc4-a25355a78d05', 'origin_query': 'how blockchain works?'}, {'id': 25, 'task_id': '2f2f9040-3cb6-4df8-8ae3-09b4ba58371d', 'origin_query': 'how blockchain works?'}, {'id': 26, 'task_id': '1b0e9d38-39cb-4525-bb2c-34a6beaab78b', 'origin_query': 'how blockchain works?'}, {'id': 27, 'task_id': 'a6045a33-ad6a-40ee-8ce0-a6df5bc0368c', 'origin_query': 'how blockchain works?'}, {'id': 28, 'task_id': '95d55aed-c8c8-433b-99c6-bb78aaa3c6b7', 'origin_query': 'how blockchain works?'}, {'id': 29, 'task_id': 'ec371df8-ba7b-406c-af6e-d19c48f6df77', 'origin_query': 'how blockchain works?'}, {'id': 30, 'task_id': 'bc35504a-dfe7-4e2b-8cdb-1da03e78458f', 'origin_query': 'how blockchain works?'}, {'id': 31, 'task_id': '2c360062-2174-4b00-9c90-de00c9f68f76', 'origin_query': 'how blockchain works?'}, {'id': 32, 'task_id': 'df28d185-993a-41a4-ab86-996c6b720af6', 'origin_query': 'how blockchain works?'}, {'id': 33, 'task_id': '583ef0d6-2386-4c75-9d51-e8cc35c3c2d6', 'origin_query': 'how blockchain works?'}]
    # Add more assertions based on expected response structure
    assert len(response.json()) > 0

def test_create_user_query():
    payload = {"query": "how blockchain works?"}
    response = requests.post(f"{BASE_URL}/user-queries", json=payload)
    print(f"RESULT_RESPONSE: test_create_user_query: {response.json()}")
    assert response.status_code == 200
    
    # {'id': 34, 'task_id': '0fb17886-b70d-44b8-bfbe-911fa77ba673', 'origin_query': 'how blockchain works?'}
    # Add assertions to check the response content
    assert response.json()["id"] > 0
    assert response.json()["task_id"] is not None
    assert response.json()["origin_query"] == payload["query"]

def test_get_task():
    task_id = "2f2f9040-3cb6-4df8-8ae3-09b4ba58371d"  # You might want to create this dynamically
    response = requests.get(f"{BASE_URL}/tasks/{task_id}")
    print(f"RESULT_RESPONSE: test_get_task: {response.json()}")
    assert response.status_code == 200
    
    # {'id': '2f2f9040-3cb6-4df8-8ae3-09b4ba58371d', 'sub_level': 0, 'created_at': '2024-10-21T01:09:41.283945', 'updated_at': '2024-10-21T01:44:01.411790', 'state': '1.2. context', 'context': '', 'is_context_sufficient': True, 'task': '', 'short_description': 'how blockchain works?', 'user_interaction': [], 'analysis': {}, 'concepts': {}, 'sub_tasks': [], 'parent_task': None}
    # Add assertions to verify task details
    assert response.json()["id"] == task_id
    assert response.json()["sub_level"] == 0
    assert response.json()["created_at"] is not None
    assert response.json()["updated_at"] is not None
    assert response.json()["state"] == "1.2. context"
    assert response.json()["context"] == ""
    assert response.json()["is_context_sufficient"] is True

def test_clarify_context():
    task_id = "2f2f9040-3cb6-4df8-8ae3-09b4ba58371d"
    payload = {}  # Add necessary context data
    response = requests.put(f"{BASE_URL}/tasks/{task_id}/context", json=payload)
    print(f"RESULT_RESPONSE: test_clarify_context: {response.json()}")
    assert response.status_code == 200
    # Add assertions for successful context update

def test_analyze_task():
    task_id = "2f2f9040-3cb6-4df8-8ae3-09b4ba58371d"
    response = requests.post(f"{BASE_URL}/tasks/{task_id}/analyze")
    print(f"RESULT_RESPONSE: test_analyze_task: {response.json()}")
    assert response.status_code == 200
    # Add assertions for successful analysis
