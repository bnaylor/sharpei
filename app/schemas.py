from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: int = 0
    hashtags: Optional[str] = None
    completed: bool = False
    category_id: Optional[int] = None
    parent_id: Optional[int] = None

class TaskCreate(TaskBase):
    pass

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
