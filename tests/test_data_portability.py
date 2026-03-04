#!/usr/bin/env python3
"""Tests for Sharpei data portability (export/import/backup)."""
import json
import os
import pytest
from datetime import datetime, timedelta
from app.main import BACKUP_DIR, perform_backup

def test_export_data(api_client):
    """Test exporting data as JSON."""
    # 1. Create some data
    cat = api_client.post("/api/categories", json={"name": "ExportCat"}).json()
    api_client.post("/api/tasks", json={
        "title": "Task to export",
        "category_id": cat["id"],
        "priority": 0
    })

    # 2. Export
    response = api_client.get("/api/data/export")
    assert response.status_code == 200
    data = response.json()

    # 3. Verify structure
    assert "categories" in data
    assert "tasks" in data
    assert any(c["name"] == "ExportCat" for c in data["categories"])
    assert any(t["title"] == "Task to export" for t in data["tasks"])

def test_import_data(api_client):
    """Test importing data from JSON."""
    # 1. Prepare export data
    export_data = {
        "categories": [{"id": 99, "name": "ImportedCat", "query": None}],
        "tasks": [
            {
                "title": "Imported Task",
                "old_id": 101,
                "category_id": 99,
                "priority": 1,
                "completed": False,
                "archived": False,
                "parent_id": None
            },
            {
                "title": "Imported Subtask",
                "old_id": 102,
                "category_id": 99,
                "priority": 1,
                "completed": False,
                "archived": False,
                "parent_id": 101
            }
        ]
    }

    # 2. Import
    import_json = json.dumps(export_data)
    response = api_client.post(
        "/api/data/import",
        files={"file": ("export.json", import_json, "application/json")}
    )
    assert response.status_code == 200

    # 3. Verify data in DB
    tasks = api_client.get("/api/tasks").json()
    assert len(tasks) == 1 # Only top-level
    assert tasks[0]["title"] == "Imported Task"
    assert len(tasks[0]["subtasks"]) == 1
    assert tasks[0]["subtasks"][0]["title"] == "Imported Subtask"
    
    categories = api_client.get("/api/categories").json()
    assert any(c["name"] == "ImportedCat" for c in categories)

def test_automated_backup_logic(api_client):
    """Test that the backup function creates a file."""
    # Ensure backup dir exists
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    # Trigger a backup manually using the app's internal function
    perform_backup()
    
    # Check if a backup file exists
    backups = [f for f in os.listdir(BACKUP_DIR) if f.startswith("sharpei_backup_")]
    assert len(backups) > 0
