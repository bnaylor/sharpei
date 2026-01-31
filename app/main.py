from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List

from . import models, schemas, database
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sharpei")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Categories
@app.get("/api/categories", response_model=List[schemas.Category])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

@app.post("/api/categories", response_model=schemas.Category)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    db_category = models.Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# Tasks
@app.get("/api/tasks", response_model=List[schemas.TaskWithSubtasks])
def get_tasks(category_id: int = None, q: str = None, show_archived: bool = False, db: Session = Depends(get_db)):
    query = db.query(models.Task)

    if q:
        search_filter = or_(
            models.Task.title.ilike(f"%{q}%"),
            models.Task.description.ilike(f"%{q}%"),
            models.Task.hashtags.ilike(f"%{q}%")
        )
        query = query.filter(search_filter)
    else:
        # Only show top-level tasks if not searching
        query = query.filter(models.Task.parent_id == None)

    # Filter archived tasks unless explicitly requested
    if not show_archived:
        query = query.filter(models.Task.archived == False)

    if category_id:
        query = query.filter(models.Task.category_id == category_id)

    return query.order_by(models.Task.priority.asc(), models.Task.position.asc(), models.Task.id.desc()).all()

@app.post("/api/tasks/archive-completed")
def archive_completed_tasks(category_id: int = None, db: Session = Depends(get_db)):
    """Archive all completed tasks (optionally filtered by category)."""
    query = db.query(models.Task).filter(
        models.Task.completed == True,
        models.Task.archived == False
    )
    if category_id:
        query = query.filter(models.Task.category_id == category_id)

    count = query.update({"archived": True})
    db.commit()
    return {"message": f"Archived {count} completed tasks"}

@app.post("/api/tasks/reorder")
def reorder_tasks(payload: schemas.ReorderPayload, db: Session = Depends(get_db)):
    for index, task_id in enumerate(payload.task_ids):
        db.query(models.Task).filter(models.Task.id == task_id).update({"position": index})
    db.commit()
    return {"message": "Reordered successfully"}

@app.post("/api/tasks", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
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

@app.put("/api/tasks/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, task: schemas.TaskCreate, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    for var, value in task.dict(exclude_unset=True).items():
        # Preserve existing position if not explicitly set
        if var == 'position' and value is None:
            continue
        setattr(db_task, var, value)

    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted"}

# Category deletion
@app.delete("/api/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    # Set tasks in this category to no category
    db.query(models.Task).filter(models.Task.category_id == category_id).update({"category_id": None})
    db.delete(db_category)
    db.commit()
    return {"message": "Category deleted"}
