from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List

from . import models, schemas, database, crud
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
    return crud.get_categories(db)

@app.post("/api/categories", response_model=schemas.Category)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    return crud.create_category(db, category)

# Tasks
@app.get("/api/tasks", response_model=List[schemas.TaskWithSubtasks])
def get_tasks(category_id: int = None, q: str = None, show_archived: bool = False, db: Session = Depends(get_db)):
    return crud.get_tasks(db, category_id=category_id, search=q, show_archived=show_archived)

@app.post("/api/tasks/archive-completed")
def archive_completed_tasks(category_id: int = None, db: Session = Depends(get_db)):
    """Archive all completed tasks (optionally filtered by category)."""
    count = crud.archive_completed_tasks(db, category_id=category_id)
    return {"message": f"Archived {count} completed tasks"}

@app.post("/api/tasks/reorder")
def reorder_tasks(payload: schemas.ReorderPayload, db: Session = Depends(get_db)):
    crud.reorder_tasks(db, payload.task_ids)
    return {"message": "Reordered successfully"}

@app.post("/api/tasks", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db, task)

@app.put("/api/tasks/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, task: schemas.TaskCreate, db: Session = Depends(get_db)):
    db_task = crud.update_task(db, task_id, task)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.delete_task(db, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}

# Category deletion
@app.delete("/api/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    db_category = crud.delete_category(db, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}
