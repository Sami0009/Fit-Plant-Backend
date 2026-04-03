from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from ..dependencies import get_db
from ..crud.task import get_tasks, create_task, update_task, delete_task, complete_task
from ..schemas.task import Task, TaskCreate, TaskUpdate, TaskWithWorker, PaginatedTasks
from ..auth.auth import get_current_admin, get_current_user
from ..models.user import User
from ..models.task import Task as TaskModel
from typing import Optional
import os
import shutil
import datetime
from datetime import timedelta

router = APIRouter()

@router.get("/tasks/", response_model=PaginatedTasks)
def read_tasks(page: int = 1, limit: int = 10, search: str = None, status: str = None, worker_id: int = None, severity: str = None, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be greater than 0")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    tasks, total = get_tasks(db, page=page, limit=limit, search=search, status=status, worker_id=worker_id, severity=severity, user=current_user)
    total_pages = (total + limit - 1) // limit  # Ceiling division
    return PaginatedTasks(
        tasks=tasks,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )

@router.get("/tasks/{task_id}", response_model=TaskWithWorker)
def read_single_task(task_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    task = db.query(TaskModel).options(joinedload(TaskModel.assigned_user)).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check permissions: workers can only see their own tasks, admins can see all
    if current_user.role == "worker" and task.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return TaskWithWorker(
        id=task.id,
        title=task.title,
        description=task.description,
        crop_type=task.crop_type,
        due_date=task.due_date,
        assigned_to=task.assigned_to,
        status=task.status,
        severity=task.severity,
        created_by=task.created_by,
        created_at=task.created_at,
        updated_at=task.updated_at,
        worker_name=task.assigned_user.full_name if task.assigned_user else "",
        worker_image_path=task.assigned_user.image_path if task.assigned_user else None,
        image_path=task.image_path
    )

@router.post("/tasks/", response_model=Task)
def create_new_task(task: TaskCreate, db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    # Default due_date to 10 days from now when omitted
    if task.due_date is None:
        task = TaskCreate(**{**task.dict(), "due_date": datetime.datetime.utcnow() + timedelta(days=10)})

    # Check if assigned_to is a worker
    assigned_user = db.query(User).filter(User.id == task.assigned_to, User.role == "worker").first()
    if not assigned_user:
        raise HTTPException(status_code=400, detail="Assigned user must be a worker")
    db_task = create_task(db=db, task=task, created_by=current_user.id)
    return db_task

@router.put("/tasks/{task_id}", response_model=Task)
def update_existing_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    if task_update.assigned_to:
        assigned_user = db.query(User).filter(User.id == task_update.assigned_to, User.role == "worker").first()
        if not assigned_user:
            raise HTTPException(status_code=400, detail="Assigned user must be a worker")
    db_task = update_task(db, task_id=task_id, task_update=task_update)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@router.put("/tasks/{task_id}/complete", response_model=Task)
def complete_task_endpoint(task_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "worker":
        raise HTTPException(status_code=403, detail="Only workers can complete tasks")
    
    # Check if task is assigned to current user and pending
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Task not assigned to you")
    if task.status != "pending":
        raise HTTPException(status_code=400, detail="Task is not pending")
    
    # Save the uploaded file
    upload_dir = f"uploads/worker_{current_user.id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_extension = os.path.splitext(file.filename)[1]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"task_{task_id}_worker_{current_user.id}_{timestamp}{file_extension}"
    file_path = f"{upload_dir}/{file_name}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Complete the task
    db_task = complete_task(db, task_id=task_id, image_path=file_path, worker_id=current_user.id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found or already completed")
    # Add image_name to response
    db_task.image_name = file_name
    return db_task

@router.get("/tasks/{task_id}/image")
def get_task_image(task_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check permissions: workers can only see their own tasks, admins can see all
    if current_user.role == "worker" and task.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not task.image_path or not os.path.exists(task.image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(task.image_path)

@router.delete("/tasks/{task_id}")
def delete_existing_task(task_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    db_task = delete_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}
