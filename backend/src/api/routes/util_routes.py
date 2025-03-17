from fastapi import APIRouter, Depends, HTTPException
import json
from src.api.deps import get_db_service
from src.model.task import Task
from src.services.database_service import DatabaseService

router = APIRouter()

@router.delete("/tasks/{task_id}/clear-scope", response_model=dict)
async def clear_task_scope(
    task_id: str,
    db: DatabaseService = Depends(get_db_service)
):
    """Clear the scope of a specific task"""
    task_data = db.fetch_task_by_id(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    # Convert task_data to Task object
    task_dict = json.loads(task_data['task_json'])
    
    # Clear the scope
    task_dict['scope'] = None
    
    # Update the task in the database
    task = Task(**task_dict)
    db.updated_task(task)
    
    return {"message": f"Task scope for ID {task_id} has been successfully cleared"} 