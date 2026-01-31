from sqlalchemy.orm import Session
from sqlalchemy import or_, func, desc
from typing import List, Optional, Union
from . import models, schemas

# Categories
def get_categories(db: Session):
    return db.query(models.Category).all()

def get_category(db: Session, category_id: int):
    return db.query(models.Category).filter(models.Category.id == category_id).first()

def create_category(db: Session, category: schemas.CategoryCreate):
    db_category = models.Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int):
    db_category = get_category(db, category_id)
    if db_category:
        # Set tasks in this category to no category
        db.query(models.Task).filter(models.Task.category_id == category_id).update({"category_id": None})
        db.delete(db_category)
        db.commit()
    return db_category

# Tasks
def get_task(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def get_tasks(
    db: Session,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    show_archived: bool = False,
    priority: Optional[int] = None
):
    query = db.query(models.Task)

    if search:
        search_filter = or_(
            models.Task.title.ilike(f"%{search}%"),
            models.Task.description.ilike(f"%{search}%"),
            models.Task.hashtags.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    else:
        # Only show top-level tasks if not searching
        query = query.filter(models.Task.parent_id == None)

    if not show_archived:
        query = query.filter(models.Task.archived == False)

    if category_id is not None:
        query = query.filter(models.Task.category_id == category_id)
        
    if priority is not None:
        query = query.filter(models.Task.priority == priority)

    return query.order_by(models.Task.priority.asc(), models.Task.position.asc(), models.Task.id.desc()).all()

def create_task(db: Session, task: schemas.TaskCreate):
    task_data = task.dict()
    # Auto-assign position to end of list for this priority level
    max_pos = db.query(func.max(models.Task.position)).filter(
        models.Task.priority == task_data.get('priority', 1),
        models.Task.parent_id == task_data.get('parent_id')
    ).scalar()
    task_data['position'] = (max_pos or 0) + 1

    db_task = models.Task(**task_data)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, task_id: int, task_update: Union[schemas.TaskCreate, schemas.TaskUpdate, dict]):
    db_task = get_task(db, task_id)
    if not db_task:
        return None

    if isinstance(task_update, dict):
        update_data = task_update
    else:
        update_data = task_update.dict(exclude_unset=True)
    
    for var, value in update_data.items():
        # Preserve existing position if not explicitly set
        if var == 'position' and value is None:
            continue
        # Skip if attribute doesn't exist on model
        if not hasattr(db_task, var):
            continue
        setattr(db_task, var, value)

    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int):
    db_task = get_task(db, task_id)
    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task

def archive_completed_tasks(db: Session, category_id: Optional[int] = None):
    query = db.query(models.Task).filter(
        models.Task.completed == True,
        models.Task.archived == False
    )
    if category_id:
        query = query.filter(models.Task.category_id == category_id)

    count = query.update({"archived": True})
    db.commit()
    return count

def reorder_tasks(db: Session, task_ids: List[int]):
    for index, task_id in enumerate(task_ids):
        db.query(models.Task).filter(models.Task.id == task_id).update({"position": index})
    db.commit()
