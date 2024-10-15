# src/database_service.py
import json
import sqlite3
from typing import Any, Dict, List

from src.task import Task


class DatabaseService:
    def __init__(self, db_path: str):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self._initialize_db()

    def _initialize_db(self):
        # Create tables if they don't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                origin_query TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                task_json TEXT NOT NULL
            )
        ''')
        self.connection.commit()

    def insert_user_query(self, task_id: str, origin_query: str):
        self.cursor.execute('''
            INSERT INTO user_queries (task_id, origin_query)
            VALUES (?, ?)
        ''', (task_id, origin_query))
        self.connection.commit()

    def insert_task(self, task: Task):
        task_id = task.id
        task_json = json.dumps(task.to_dict(), ensure_ascii=False)
        self.cursor.execute('''
            INSERT INTO tasks (task_id, task_json)
            VALUES (?, ?)
        ''', (task_id, task_json))
        self.connection.commit()

    def updated_task(self, task: Task):
        task_id = task.id
        task_json = json.dumps(task.to_dict(), ensure_ascii=False)
        self.cursor.execute('''
            UPDATE tasks SET task_json = ? WHERE task_id = ?
        ''', (task_json, task_id))
        self.connection.commit()

    def fetch_user_queries(self) -> List[Dict[str, Any]]:
        self.cursor.execute('SELECT * FROM user_queries')
        rows = self.cursor.fetchall()
        return [
            {"id": row[0], "task_id": row[1], "origin_query": row[2]}
            for row in rows
        ]

    def fetch_tasks(self) -> List[Dict[str, Any]]:
        self.cursor.execute('SELECT * FROM tasks')
        rows = self.cursor.fetchall()
        return [
            {"id": row[0], "task_id": row[1], "task_json": row[2]}
            for row in rows
        ]

    def close(self):
        self.connection.close()
