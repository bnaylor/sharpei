from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ReorderPayload(BaseModel):
    task_ids: List[int]

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: int = 1
    position: Optional[int] = None
    hashtags: Optional[str] = None
    completed: bool = False
    archived: bool = False
    category_id: Optional[int] = None
    parent_id: Optional[int] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = None
    position: Optional[int] = None
    hashtags: Optional[str] = None
    completed: Optional[bool] = None
    archived: Optional[bool] = None
    category_id: Optional[int] = None
    parent_id: Optional[int] = None

class Task(TaskBase):
    id: int
    
    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    tasks: List[Task] = []

    class Config:
        from_attributes = True

# For nested display
class TaskWithSubtasks(Task):
    subtasks: List['TaskWithSubtasks'] = []

TaskWithSubtasks.model_rebuild()
