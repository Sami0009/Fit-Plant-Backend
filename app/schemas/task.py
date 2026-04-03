from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional
import enum

class TaskStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

class TaskSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    crop_type: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to: int
    status: TaskStatus = TaskStatus.pending
    severity: Optional[TaskSeverity] = TaskSeverity.low

    @validator("description", "crop_type", pre=True, always=False)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

    @validator("due_date", pre=True, always=False)
    def parse_due_date(cls, v):
        if v == "" or v is None:
            return None
        return v

    @validator("severity", pre=True, always=False)
    def parse_severity(cls, v):
        if v == "" or v is None:
            return TaskSeverity.low
        return v

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    crop_type: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None
    status: Optional[TaskStatus] = None
    severity: Optional[TaskSeverity] = None
    image_path: Optional[str] = None

class Task(TaskBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    image_path: Optional[str] = None
    image_name: Optional[str] = None

    class Config:
        from_attributes = True

class TaskWithWorker(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    crop_type: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to: int
    status: TaskStatus
    severity: Optional[TaskSeverity] = None
    created_by: int
    created_at: datetime
    updated_at: datetime
    worker_name: str
    worker_image_path: Optional[str] = None
    image_path: Optional[str] = None

    class Config:
        from_attributes = True

class PaginatedTasks(BaseModel):
    tasks: list[TaskWithWorker]
    total: int
    page: int
    limit: int
    total_pages: int

    class Config:
        from_attributes = True
