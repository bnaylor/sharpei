from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
import shutil
import os
import glob
from datetime import datetime, timedelta
import json

from . import models, schemas, database, crud
from .database import engine, get_db, DB_PATH

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sharpei")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
templates = Jinja2Templates(directory="templates")

BACKUP_DIR = os.path.join(os.path.dirname(DB_PATH), "backups")
BACKUP_INTERVAL_HOURS = 24

def perform_backup():
    """Create a timestamped backup of the database and cleanup old ones."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"sharpei_backup_{timestamp}.db")
    
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, backup_path)
        
        # Cleanup: keep last 10 backups
        backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "sharpei_backup_*.db")))
        if len(backups) > 10:
            for b in backups[:-10]:
                try:
                    os.remove(b)
                except OSError:
                    pass

def check_and_trigger_backup(background_tasks: BackgroundTasks):
    """Check if a new backup is needed based on cadence."""
    if not os.path.exists(BACKUP_DIR):
        background_tasks.add_task(perform_backup)
        return

    backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "sharpei_backup_*.db")))
    if not backups:
        background_tasks.add_task(perform_backup)
        return

    # Check if latest backup is older than interval
    latest_backup = backups[-1]
    mtime = os.path.getmtime(latest_backup)
    last_backup_time = datetime.fromtimestamp(mtime)
    
    if datetime.now() - last_backup_time > timedelta(hours=BACKUP_INTERVAL_HOURS):
        background_tasks.add_task(perform_backup)

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/manifest.json")
def get_manifest():
    return FileResponse("static/manifest.json")

@app.get("/service-worker.js")
def get_service_worker():
    return FileResponse("static/service-worker.js")

# Data Portability
@app.get("/api/data/export")
def export_data(db: Session = Depends(get_db)):
    """Export all categories and tasks as JSON."""
    categories = crud.get_categories(db)
    # Get all tasks including archived and subtasks
    tasks = db.query(models.Task).all()
    
    data = {
        "exported_at": datetime.now().isoformat(),
        "categories": [
            {"id": c.id, "name": c.name, "query": c.query} for c in categories
        ],
        "tasks": [
            {
                "title": t.title,
                "description": t.description,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "priority": t.priority,
                "position": t.position,
                "hashtags": t.hashtags,
                "recurrence": t.recurrence,
                "completed": t.completed,
                "archived": t.archived,
                "category_id": t.category_id,
                "parent_id": t.parent_id,
                "old_id": t.id
            } for t in tasks
        ]
    }
    
    filename = f"sharpei_export_{datetime.now().strftime('%Y%m%d')}.json"
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/api/data/import")
async def import_data(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import data from JSON, clearing existing data."""
    try:
        contents = await file.read()
        data = json.loads(contents)
        
        # Simple validation
        if "tasks" not in data or "categories" not in data:
            raise HTTPException(status_code=400, detail="Invalid export format")
            
        # Clear existing
        crud.clear_all_data(db)
        
        # Map old category IDs to new ones
        cat_id_map = {}
        for cat_data in data["categories"]:
            old_id = cat_data.get("id")
            new_cat = crud.create_category(db, schemas.CategoryCreate(
                name=cat_data["name"],
                query=cat_data.get("query")
            ))
            if old_id is not None:
                cat_id_map[old_id] = new_cat.id
                
        # Map old task IDs to new ones (for subtasks)
        task_id_map = {}
        # First pass: create all tasks
        for task_data in data["tasks"]:
            # Prepare data
            old_id = task_data.pop("old_id", None)
            old_cat_id = task_data.pop("category_id", None)
            old_parent_id = task_data.pop("parent_id", None)
            
            # Map category
            task_data["category_id"] = cat_id_map.get(old_cat_id)
            # Temporarily nullify parent_id for second pass
            task_data["parent_id"] = None
            
            # Convert due_date string back to datetime
            if task_data.get("due_date"):
                task_data["due_date"] = datetime.fromisoformat(task_data["due_date"])
            
            # Create task using model directly to preserve all fields
            db_task = models.Task(**task_data)
            db.add(db_task)
            db.flush() # Get new ID
            
            if old_id is not None:
                task_id_map[old_id] = {
                    "new_id": db_task.id,
                    "old_parent_id": old_parent_id
                }
        
        # Second pass: restore parent/subtask relationships
        for old_id, mapping in task_id_map.items():
            if mapping["old_parent_id"] is not None:
                new_parent_id = task_id_map.get(mapping["old_parent_id"], {}).get("new_id")
                if new_parent_id:
                    db.query(models.Task).filter(models.Task.id == mapping["new_id"]).update(
                        {"parent_id": new_parent_id}
                    )
        
        db.commit()
        return {"message": "Data imported successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

# Categories
@app.get("/api/categories", response_model=List[schemas.Category])
def get_categories(db: Session = Depends(get_db)):
    return crud.get_categories(db)

@app.post("/api/categories", response_model=schemas.Category)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    return crud.create_category(db, category)

# Tasks
@app.get("/api/tasks", response_model=List[schemas.TaskWithSubtasks])
def get_tasks(
    background_tasks: BackgroundTasks,
    category_id: int = None, 
    q: str = None, 
    show_archived: bool = False, 
    db: Session = Depends(get_db)
):
    check_and_trigger_backup(background_tasks)
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
