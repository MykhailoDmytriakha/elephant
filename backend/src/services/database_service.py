import json
import sqlite3
import logging
from contextlib import contextmanager
from typing import Any, Dict, List
import os

from src.core.config import settings
from src.model.task import Task


logger = logging.getLogger(__name__)

class DatabaseService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            logger.info("Creating new DatabaseService instance")
            cls._instance = super(DatabaseService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once
        if not DatabaseService._initialized:
            self.db_path = settings.DATABASE_URL
            logger.info(f"Initializing DatabaseService with database path: {self.db_path}")
            logger.debug(f"Absolute database path: {os.path.abspath(self.db_path)}")
            logger.debug(f"Current working directory: {os.getcwd()}")
            self._initialize_db()
            DatabaseService._initialized = True

    @contextmanager
    def get_connection(self):
        connection = sqlite3.connect(self.db_path)
        try:
            yield connection
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            connection.close()

    def _initialize_db(self):
        logger.info("Initializing database tables")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_queries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT NOT NULL,
                        query TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        progress INTEGER NOT NULL,
                        FOREIGN KEY (task_id) REFERENCES tasks (id)
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
            logger.info("Database tables initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def insert_user_query(self, task_id: str, query: str, status: str, created_at: str, progress: float):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_queries (task_id, query, status, created_at, progress)
                VALUES (?, ?, ?, ?, ?)
            ''', (task_id, query, status, created_at, progress))
            conn.commit()
            return {
                "id": cursor.lastrowid,
                "task_id": task_id,
                "query": query,
                "status": status,
                "created_at": created_at,
                "progress": progress
            }

    def insert_task(self, task: Task) -> str:
        logger.info(f"Inserting task with ID: {task.id}")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                task_id = task.id
                task_json = json.dumps(task.to_dict(), ensure_ascii=False)
                cursor.execute('''
                    INSERT INTO tasks (task_id, task_json)
                    VALUES (?, ?)
                ''', (task_id, task_json))
                conn.commit()
                logger.info(f"Task inserted successfully. ID: {task.id}")
                return task.id
        except sqlite3.Error as e:
            logger.error(f"Error inserting task: {e}")
            raise

    def updated_task(self, task: Task):
        logger.info(f"Updating task with ID: {task.id}")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                task_id = task.id
                task_json = json.dumps(task.to_dict(), ensure_ascii=False)
                cursor.execute('''
                    UPDATE tasks SET task_json = ? WHERE task_id = ?
                ''', (task_json, task_id))
                conn.commit()
                logger.info(f"Task updated successfully. ID: {task.id}")
        except sqlite3.Error as e:
            logger.error(f"Error updating task: {e}")
            raise

    def fetch_user_queries(self):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row  # Enable row_factory to return sqlite3.Row objects
            cursor = conn.cursor()
            cursor.execute('SELECT id, task_id, query, status, created_at, progress FROM user_queries')
            rows = cursor.fetchall()
            return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

    def fetch_user_query_by_id(self, query_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, task_id, query, status, created_at, progress FROM user_queries WHERE id = ?', (query_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def fetch_user_queries_by_task_id(self, task_id: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, task_id, query, status, created_at, progress FROM user_queries WHERE task_id = ?', (task_id,))
            return [dict(row) for row in cursor.fetchall()]

    def fetch_tasks(self) -> List[Dict[str, Any]]:
        logger.info("Fetching all tasks")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tasks')
                rows = cursor.fetchall()
                logger.info(f"Fetched {len(rows)} tasks")
                return [{"id": row[0], "task_id": row[1], "task_json": row[2]} for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error fetching tasks: {e}")
            raise

    def fetch_task_by_id(self, task_id: str) -> Dict[str, Any] | None:
        logger.info(f"Fetching task with ID: {task_id}")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tasks WHERE task_id = ?', (task_id,))
                row = cursor.fetchone()
                if row:
                    logger.info(f"Task found. ID: {task_id}")
                    return {"id": row[0], "task_id": row[1], "task_json": row[2]}
                logger.info(f"Task not found. ID: {task_id}")
                return None
        except sqlite3.Error as e:
            logger.error(f"Error fetching task by ID: {e}")
            raise

    def delete_task_by_id(self, task_id: str) -> bool:
        """Delete a task by its ID"""
        logger.info(f"Deleting task with ID: {task_id}")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Fetch the task to check its level
                cursor.execute('SELECT task_json FROM tasks WHERE task_id = ?', (task_id,))
                task_row = cursor.fetchone()
                if not task_row:
                    logger.info(f"Task with ID {task_id} not found")
                    return False
                
                task_data = json.loads(task_row[0])
                is_top_level = task_data.get('sub_level', 0) == 0

                # Delete the task and its children
                cursor.execute('''
                    WITH RECURSIVE
                        subtasks(id) AS (
                            SELECT task_id FROM tasks WHERE task_id = ?
                            UNION ALL
                            SELECT t.task_id
                            FROM tasks t
                            JOIN subtasks s ON json_extract(t.task_json, '$.parent_id') = s.id
                        )
                    DELETE FROM tasks WHERE task_id IN subtasks
                ''', (task_id,))

                # If it's a top-level task, delete related user queries
                if is_top_level:
                    cursor.execute('DELETE FROM user_queries WHERE task_id = ?', (task_id,))

                conn.commit()
                
                deleted_count = cursor.rowcount
                logger.info(f"Deleted task and {deleted_count - 1} subtasks")
                return True

        except sqlite3.Error as e:
            logger.error(f"Error deleting task: {e}")
            return False
        
    def delete_all_tasks(self):
        logger.info("Deleting all tasks")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM tasks')
                conn.commit()
                logger.info("All tasks deleted successfully")
        except sqlite3.Error as e:
            logger.error(f"Error deleting all tasks: {e}")
    
    def delete_all_user_queries(self):
        logger.info("Deleting all user queries")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM user_queries')
                conn.commit()
                logger.info("All user queries deleted successfully")
        except sqlite3.Error as e:
            logger.error(f"Error deleting all user queries: {e}")

    def update_user_query_progress(self, task_id: str, progress: float):
        """Update the progress of a user query associated with a task"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_queries
                SET progress = ?
                WHERE task_id = ?
            ''', (progress, task_id))
            conn.commit()
            return cursor.rowcount > 0
