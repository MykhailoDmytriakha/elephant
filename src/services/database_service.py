import json
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List

from src.core.config import settings
from src.model.task import Task


class DatabaseService:
    def __init__(self):
        self.db_path = settings.DATABASE_URL
        self._initialize_db()

    @contextmanager
    def get_connection(self):
        connection = sqlite3.connect(self.db_path)
        try:
            yield connection
        finally:
            connection.close()

    def _initialize_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    origin_query TEXT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    task_json TEXT NOT NULL
                )
            ''')
            conn.commit()

    def insert_user_query(self, task_id: str, origin_query: str) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_queries (task_id, origin_query)
                VALUES (?, ?)
            ''', (task_id, origin_query))
            conn.commit()
            # Fetch the inserted row
            inserted_id = cursor.lastrowid
            cursor.execute('SELECT * FROM user_queries WHERE id = ?', (inserted_id,))
            row = cursor.fetchone()
            return {"id": row[0], "task_id": row[1], "origin_query": row[2]}

    def insert_task(self, task: Task):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            task_id = task.id
            task_json = json.dumps(task.to_dict(), ensure_ascii=False)
            cursor.execute('''
                INSERT INTO tasks (task_id, task_json)
                VALUES (?, ?)
            ''', (task_id, task_json))
            conn.commit()

    def updated_task(self, task: Task):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            task_id = task.id
            task_json = json.dumps(task.to_dict(), ensure_ascii=False)
            cursor.execute('''
                UPDATE tasks SET task_json = ? WHERE task_id = ?
            ''', (task_json, task_id))
            conn.commit()

    def fetch_user_queries(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user_queries')
            rows = cursor.fetchall()
            return [{"id": row[0], "task_id": row[1], "origin_query": row[2]} for row in rows]

    def fetch_user_query_by_id(self, query_id: int) -> dict[str, Any] | None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user_queries WHERE id = ?', (query_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "task_id": row[1], "origin_query": row[2]}
            return None

    def fetch_user_queries_by_task_id(self, task_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user_queries WHERE task_id = ?', (task_id,))
            rows = cursor.fetchall()
            return [{"id": row[0], "task_id": row[1], "origin_query": row[2]} for row in rows]

    def fetch_tasks(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks')
            rows = cursor.fetchall()
            return [{"id": row[0], "task_id": row[1], "task_json": row[2]} for row in rows]
