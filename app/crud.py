from sqlalchemy.orm import Session
from sqlalchemy import or_, func, desc
from typing import List, Optional, Union
from datetime import datetime, timedelta
from . import models, schemas

# Categories
def get_categories(db: Session):
    return db.query(models.Category).all()

def get_category(db: Session, category_id: int):
    return db.query(models.Category).filter(models.Category.id == category_id).first()

def create_category(db: Session, category: schemas.CategoryCreate):
    db_category = models.Category(name=category.name, query=category.query)
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

def clear_all_data(db: Session):
    """Delete all tasks and categories."""
    db.query(models.Task).delete()
    db.query(models.Category).delete()
    db.commit()

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

    # If category_id is provided, check if it's a smart category
    if category_id is not None:
        db_category = get_category(db, category_id)
        if db_category and db_category.query:
            # It's a smart category! Merge its query with the search param
            if search:
                search = f"{db_category.query} {search}"
            else:
                search = db_category.query
            # Don't filter by category_id since the smart query handles it
            category_id = None

    if search:
        # Split search into tokens
        tokens = search.split()
        filters = []
        remaining_search = []
        
        for token in tokens:
            if token.lower().startswith('is:'):
                val = token[3:].lower()
                if val == 'overdue':
                    filters.append(models.Task.due_date < datetime.now())
                    filters.append(models.Task.completed == False)
                elif val == 'completed':
                    filters.append(models.Task.completed == True)
                elif val == 'pending':
                    filters.append(models.Task.completed == False)
                elif val == 'archived':
                    show_archived = True
                    filters.append(models.Task.archived == True)
            elif token.lower().startswith('priority:') or token.lower().startswith('p:'):
                parts = token.split(':')
                if len(parts) > 1:
                    val = parts[1].lower()
                    p_map = {'high': 0, 'h': 0, 'normal': 1, 'n': 1, 'low': 2, 'l': 2}
                    if val in p_map:
                        filters.append(models.Task.priority == p_map[val])
                    elif val.isdigit():
                        filters.append(models.Task.priority == int(val))
            elif token.lower().startswith('has:'):
                val = token[4:].lower()
                if val == 'due':
                    filters.append(models.Task.due_date != None)
                elif val == 'tags':
                    filters.append(models.Task.hashtags != None)
                    filters.append(models.Task.hashtags != '')
                elif val in ('description', 'desc'):
                    filters.append(models.Task.description != None)
                    filters.append(models.Task.description != '')
            elif token.lower().startswith('category:'):
                parts = token.split(':')
                if len(parts) > 1:
                    cat_name = parts[1]
                    query = query.join(models.Category, isouter=True).filter(models.Category.name.ilike(f"%{cat_name}%"))
            else:
                remaining_search.append(token)

        if filters:
            query = query.filter(*filters)

        if remaining_search:
            text_search = " ".join(remaining_search)
            search_filter = or_(
                models.Task.title.ilike(f"%{text_search}%"),
                models.Task.description.ilike(f"%{text_search}%"),
                models.Task.hashtags.ilike(f"%{text_search}%")
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

    # Handle recurring tasks
    if db_task.completed and db_task.recurrence and db_task.due_date:
        # Move due date forward
        new_due_date = db_task.due_date
        
        r = db_task.recurrence.lower()
        if r == 'daily':
            new_due_date += timedelta(days=1)
        elif r == 'weekly':
            new_due_date += timedelta(weeks=1)
        elif r == 'monthly':
            # Simplified monthly: just add 30 days
            new_due_date += timedelta(days=30)
        elif r.endswith('d'):
            try:
                days = int(r[:-1])
                new_due_date += timedelta(days=days)
            except ValueError:
                pass
        elif r.endswith('w'):
            try:
                weeks = int(r[:-1])
                new_due_date += timedelta(weeks=weeks)
            except ValueError:
                pass
        
        # If we successfully calculated a new date, reset completed status and update due date
        if new_due_date != db_task.due_date:
            db_task.completed = False
            db_task.due_date = new_due_date

    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int):
    db_task = get_task(db, task_id)
    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task

def bulk_update_tasks(db: Session, task_ids: List[int], updates: dict):
    """Update multiple tasks at once."""
    if not task_ids:
        return 0
    
    # Filter out updates that don't exist on the model
    clean_updates = {k: v for k, v in updates.items() if hasattr(models.Task, k)}
    if not clean_updates:
        return 0

    count = db.query(models.Task).filter(models.Task.id.in_(task_ids)).update(clean_updates, synchronize_session=False)
    db.commit()
    return count

def bulk_delete_tasks(db: Session, task_ids: List[int]):
    """Delete multiple tasks at once."""
    if not task_ids:
        return 0
    
    count = db.query(models.Task).filter(models.Task.id.in_(task_ids)).delete(synchronize_session=False)
    db.commit()
    return count

def archive_completed_tasks(db: Session, category_id: Optional[int] = None):
    query = db.query(models.Task).filter(
        models.Task.completed == True,
        models.Task.archived == False
    )
    if category_id is not None:
        query = query.filter(models.Task.category_id == category_id)

    count = query.update({"archived": True})
    db.commit()
    return count

def reorder_tasks(db: Session, task_ids: List[int]):
    for index, task_id in enumerate(task_ids):
        db.query(models.Task).filter(models.Task.id == task_id).update({"position": index})
    db.commit()
