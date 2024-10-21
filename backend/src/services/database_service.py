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
    def __init__(self):
        self.db_path = settings.DATABASE_URL
        logger.info(f"Initializing DatabaseService with database path: {self.db_path}")
        logger.debug(f"Absolute database path: {os.path.abspath(self.db_path)}")
        logger.debug(f"Current working directory: {os.getcwd()}")
        self._initialize_db()

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
            logger.info("Database tables initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def insert_user_query(self, task_id: str, origin_query: str) -> Dict[str, Any]:
        logger.info(f"Inserting user query for task_id: {task_id}")
        if not task_id:
            raise ValueError("task_id cannot be None or empty")
        try:
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
                logger.info(f"User query inserted successfully. ID: {inserted_id}")
                return {"id": row[0], "task_id": row[1], "origin_query": row[2]}
        except sqlite3.Error as e:
            logger.error(f"Error inserting user query: {e}")
            raise

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

    def fetch_user_queries(self) -> List[Dict[str, Any]]:
        logger.info("Fetching all user queries")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM user_queries')
                rows = cursor.fetchall()
                logger.info(f"Fetched {len(rows)} user queries")
                return [{"id": row[0], "task_id": row[1], "origin_query": row[2]} for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error fetching user queries: {e}")
            raise

    def fetch_user_query_by_id(self, query_id: int) -> dict[str, Any] | None:
        logger.info(f"Fetching user query with ID: {query_id}")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM user_queries WHERE id = ?', (query_id,))
                row = cursor.fetchone()
                if row:
                    logger.info(f"User query found. ID: {query_id}")
                    return {"id": row[0], "task_id": row[1], "origin_query": row[2]}
                logger.info(f"User query not found. ID: {query_id}")
                return None
        except sqlite3.Error as e:
            logger.error(f"Error fetching user query by ID: {e}")
            raise

    def fetch_user_queries_by_task_id(self, task_id: str) -> List[Dict[str, Any]]:
        logger.info(f"Fetching user queries for task_id: {task_id}")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM user_queries WHERE task_id = ?', (task_id,))
                rows = cursor.fetchall()
                logger.info(f"Fetched {len(rows)} user queries for task_id: {task_id}")
                return [{"id": row[0], "task_id": row[1], "origin_query": row[2]} for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error fetching user queries by task_id: {e}")
            raise

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
