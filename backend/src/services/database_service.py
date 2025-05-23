import json
import sqlite3
import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional
import os
from datetime import datetime
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
        """
        Context manager for database connections.
        """
        connection = None
        try:
            connection = sqlite3.connect(self.db_path)
            yield connection
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
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
        task.updated_at = datetime.now().isoformat()
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
        """Fetch all user queries"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row  # Enable row_factory to return sqlite3.Row objects
                cursor = conn.cursor()
                cursor.execute('SELECT id, task_id, query, status, created_at, progress FROM user_queries')
                rows = cursor.fetchall()
                return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error fetching user queries: {e}")
            raise

    def fetch_user_query_by_id(self, query_id: int):
        """Fetch a user query by ID"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT id, task_id, query, status, created_at, progress FROM user_queries WHERE id = ?', (query_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error fetching user query by ID: {e}")
            raise

    def fetch_user_queries_by_task_id(self, task_id: str):
        """Fetch user queries by task ID"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT id, task_id, query, status, created_at, progress FROM user_queries WHERE task_id = ?', (task_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error fetching user queries by task ID: {e}")
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

    # ========================================
    # Task Status Update Methods
    # ========================================
    
    def update_subtask_status(self, task_id: str, subtask_reference: str, status: str, 
                             result: Optional[str] = None, error_message: Optional[str] = None,
                             started_at: Optional[str] = None, completed_at: Optional[str] = None) -> Dict[str, Any]:
        """
        Update a subtask's status and related fields within a task.
        
        Args:
            task_id: The task ID containing the subtask
            subtask_reference: Reference like "S1_W1_ET1_ST1" or subtask ID
            status: New status ("Pending", "In Progress", "Completed", "Failed", "Cancelled", "Waiting")
            result: Result string (for completed tasks)
            error_message: Error message (for failed tasks)
            started_at: ISO timestamp when started
            completed_at: ISO timestamp when completed
            
        Returns:
            Dict with success status and details
        """
        logger.info(f"Updating subtask {subtask_reference} status to {status} in task {task_id}")
        
        try:
            # Get the task
            task_data = self.fetch_task_by_id(task_id)
            if not task_data:
                return {
                    "success": False,
                    "error": f"Task {task_id} not found",
                    "task_id": task_id,
                    "subtask_reference": subtask_reference
                }
            
            # Parse task JSON
            task_json = json.loads(task_data['task_json'])
            
            # Find and update the subtask
            subtask_found = False
            update_result = self._find_and_update_subtask(
                task_json, subtask_reference, status, result, error_message, started_at, completed_at
            )
            
            if not update_result["found"]:
                return {
                    "success": False,
                    "error": f"Subtask {subtask_reference} not found in task {task_id}",
                    "task_id": task_id,
                    "subtask_reference": subtask_reference
                }
            
            # Update the task's updated_at timestamp
            task_json['updated_at'] = datetime.now().isoformat()
            
            # Save back to database
            with self.get_connection() as conn:
                cursor = conn.cursor()
                updated_task_json = json.dumps(task_json, ensure_ascii=False)
                cursor.execute('''
                    UPDATE tasks SET task_json = ? WHERE task_id = ?
                ''', (updated_task_json, task_id))
                conn.commit()
            
            logger.info(f"Successfully updated subtask {subtask_reference} status to {status}")
            
            return {
                "success": True,
                "task_id": task_id,
                "subtask_reference": subtask_reference,
                "old_status": update_result["old_status"],
                "new_status": status,
                "updated_fields": update_result["updated_fields"],
                "message": f"Subtask {subtask_reference} status updated from {update_result['old_status']} to {status}"
            }
            
        except Exception as e:
            error_msg = f"Error updating subtask status: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "task_id": task_id,
                "subtask_reference": subtask_reference
            }
    
    def _find_and_update_subtask(self, task_json: Dict[str, Any], subtask_reference: str, 
                                status: str, result: Optional[str] = None, error_message: Optional[str] = None,
                                started_at: Optional[str] = None, completed_at: Optional[str] = None) -> Dict[str, Any]:
        """
        Find and update a subtask within the task JSON structure.
        Handles both subtask IDs and references like "S1_W1_ET1_ST1".
        """
        network_plan = task_json.get('network_plan', {})
        stages = network_plan.get('stages', [])
        
        for stage in stages:
            work_packages = stage.get('work_packages', [])
            for work in work_packages:
                executable_tasks = work.get('tasks', [])
                for exec_task in executable_tasks:
                    subtasks = exec_task.get('subtasks', [])
                    for subtask in subtasks:
                        # Check if this is the target subtask (by ID or reference)
                        subtask_id = subtask.get('id', '')
                        subtask_matches = (
                            subtask_id == subtask_reference or
                            subtask_reference in subtask_id or
                            self._matches_subtask_reference(stage, work, exec_task, subtask, subtask_reference)
                        )
                        
                        if subtask_matches:
                            old_status = subtask.get('status', 'Pending')
                            updated_fields = []
                            
                            # Update status
                            subtask['status'] = status
                            updated_fields.append('status')
                            
                            # Update timestamps and fields based on status
                            current_time = datetime.now().isoformat()
                            
                            if status == "In Progress":
                                if not subtask.get('started_at') or started_at:
                                    subtask['started_at'] = started_at or current_time
                                    updated_fields.append('started_at')
                                # Clear completion fields
                                subtask.pop('completed_at', None)
                                subtask.pop('result', None)
                                subtask.pop('error_message', None)
                            
                            elif status in ["Completed", "Failed", "Cancelled"]:
                                if not subtask.get('completed_at') or completed_at:
                                    subtask['completed_at'] = completed_at or current_time
                                    updated_fields.append('completed_at')
                                
                                if status == "Completed" and result is not None:
                                    subtask['result'] = result
                                    updated_fields.append('result')
                                    subtask.pop('error_message', None)  # Clear error on success
                                
                                elif status == "Failed" and error_message is not None:
                                    subtask['error_message'] = error_message
                                    updated_fields.append('error_message')
                                    subtask.pop('result', None)  # Clear result on failure
                            
                            # Update started_at if provided
                            if started_at and status != "In Progress":
                                subtask['started_at'] = started_at
                                updated_fields.append('started_at')
                            
                            return {
                                "found": True,
                                "old_status": old_status,
                                "updated_fields": updated_fields,
                                "subtask_id": subtask_id
                            }
        
        return {"found": False}
    
    def _matches_subtask_reference(self, stage: Dict, work: Dict, exec_task: Dict, subtask: Dict, reference: str) -> bool:
        """
        Check if a subtask matches a reference pattern like "S1_W1_ET1_ST1".
        """
        if '_' not in reference:
            return False
        
        try:
            parts = reference.split('_')
            if len(parts) != 4:
                return False
            
            stage_ref, work_ref, exec_ref, subtask_ref = parts
            
            # Extract numbers from IDs
            stage_match = stage.get('id', '').replace('S', '') == stage_ref.replace('S', '')
            work_match = work.get('id', '').endswith(work_ref) or work_ref in work.get('id', '')
            exec_match = exec_ref in exec_task.get('id', '') or exec_task.get('id', '').endswith(exec_ref)
            
            # For subtasks, check both position-based and ID-based matching
            subtask_sequence = subtask.get('sequence_order', -1)
            subtask_num = subtask_ref.replace('ST', '')
            
            # Try to match by sequence (ST1 = sequence 0, ST2 = sequence 1, etc.)
            try:
                expected_sequence = int(subtask_num) - 1
                sequence_match = subtask_sequence == expected_sequence
            except:
                sequence_match = False
            
            id_match = subtask_ref in subtask.get('id', '')
            
            return stage_match and work_match and exec_match and (sequence_match or id_match)
        except:
            return False
    
    def get_subtask_status(self, task_id: str, subtask_reference: str) -> Dict[str, Any]:
        """
        Get the current status and details of a specific subtask.
        
        Args:
            task_id: The task ID containing the subtask
            subtask_reference: Reference like "S1_W1_ET1_ST1" or subtask ID
            
        Returns:
            Dict with subtask status details or error
        """
        try:
            task_data = self.fetch_task_by_id(task_id)
            if not task_data:
                return {"success": False, "error": f"Task {task_id} not found"}
            
            task_json = json.loads(task_data['task_json'])
            subtask_info = self._find_subtask_info(task_json, subtask_reference)
            
            if not subtask_info["found"]:
                return {
                    "success": False, 
                    "error": f"Subtask {subtask_reference} not found in task {task_id}"
                }
            
            return {
                "success": True,
                "task_id": task_id,
                "subtask": subtask_info["subtask"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _find_subtask_info(self, task_json: Dict[str, Any], subtask_reference: str) -> Dict[str, Any]:
        """Find and return complete subtask information."""
        network_plan = task_json.get('network_plan', {})
        stages = network_plan.get('stages', [])
        
        for stage in stages:
            work_packages = stage.get('work_packages', [])
            for work in work_packages:
                executable_tasks = work.get('tasks', [])
                for exec_task in executable_tasks:
                    subtasks = exec_task.get('subtasks', [])
                    for subtask in subtasks:
                        subtask_id = subtask.get('id', '')
                        if (subtask_id == subtask_reference or 
                            subtask_reference in subtask_id or
                            self._matches_subtask_reference(stage, work, exec_task, subtask, subtask_reference)):
                            
                            return {
                                "found": True,
                                "subtask": subtask,
                                "stage_id": stage.get('id'),
                                "work_id": work.get('id'),
                                "exec_task_id": exec_task.get('id')
                            }
        
        return {"found": False}
