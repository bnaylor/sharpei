#!/usr/bin/env python3
"""MCP Server for Sharpei TODO application.

This server exposes Sharpei's task management functionality to AI assistants
via the Model Context Protocol (MCP).

Run with: python mcp_server.py
Or configure in your AI assistant's MCP settings.
"""
# Configure logging FIRST to ensure nothing pollutes stdout (used by MCP stdio protocol)
import logging
import sys
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

import json
from datetime import datetime
from typing import Optional

from mcp.server.fastmcp import FastMCP

from app.models import Task, Category
from app.database import SessionLocal
from app import crud, schemas

# Create MCP server
# Use WARNING log level to prevent debug output from corrupting stdio protocol
mcp = FastMCP("Sharpei TODO", log_level="WARNING")


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Caller is responsible for closing, or we could use context manager if we refactor more


def task_to_dict(task: Task) -> dict:
    """Convert a Task object to a dictionary."""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "priority": task.priority,
        "priority_label": {0: "High", 1: "Normal", 2: "Low"}.get(task.priority, "Normal"),
        "hashtags": task.hashtags,
        "completed": task.completed,
        "archived": task.archived,
        "category_id": task.category_id,
        "parent_id": task.parent_id,
        "subtasks": [task_to_dict(sub) for sub in task.subtasks] if task.subtasks else []
    }


def category_to_dict(category: Category) -> dict:
    """Convert a Category object to a dictionary."""
    return {
        "id": category.id,
        "name": category.name
    }


@mcp.tool()
def list_categories() -> str:
    """List all task categories.

    Returns a list of categories that can be used to organize tasks.
    """
    db = get_db()
    try:
        categories = crud.get_categories(db)
        return json.dumps([category_to_dict(c) for c in categories], indent=2)
    finally:
        db.close()


@mcp.tool()
def create_category(name: str) -> str:
    """Create a new task category.

    Args:
        name: The name for the new category

    Returns:
        The created category with its ID
    """
    db = get_db()
    try:
        category = crud.create_category(db, schemas.CategoryCreate(name=name))
        return json.dumps(category_to_dict(category), indent=2)
    finally:
        db.close()


@mcp.tool()
def list_tasks(
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    include_archived: bool = False,
    include_subtasks: bool = True,
    priority: Optional[int] = None
) -> str:
    """List tasks with optional filtering.

    Args:
        category_id: Filter by category ID (optional)
        search: Search term to filter by title, description, or hashtags (optional)
        include_archived: Whether to include archived tasks (default: False)
        include_subtasks: Whether to include subtask details (default: True)
        priority: Filter by priority (0=High, 1=Normal, 2=Low) (optional)

    Returns:
        A list of tasks matching the criteria
    """
    db = get_db()
    try:
        # Note: crud.get_tasks handles search, category_id, priority, and archived filtering
        # The logic in crud.get_tasks matches the previous logic here:
        # - if search is provided, it searches everything (including subtasks logic implicitly via flattened result if designed so, but wait...)
        # In original mcp_server.py: "Only top-level tasks if not searching".
        # In crud.get_tasks: Same logic.
        
        tasks = crud.get_tasks(
            db, 
            category_id=category_id, 
            search=search, 
            show_archived=include_archived, 
            priority=priority
        )

        result = []
        for task in tasks:
            task_dict = task_to_dict(task)
            if not include_subtasks:
                task_dict["subtasks"] = f"[{len(task.subtasks)} subtasks]" if task.subtasks else []
            result.append(task_dict)

        return json.dumps(result, indent=2)
    finally:
        db.close()


@mcp.tool()
def get_task(task_id: int) -> str:
    """Get a specific task by ID.

    Args:
        task_id: The ID of the task to retrieve

    Returns:
        The task details including subtasks
    """
    db = get_db()
    try:
        task = crud.get_task(db, task_id)
        if not task:
            return json.dumps({"error": f"Task with ID {task_id} not found"})
        return json.dumps(task_to_dict(task), indent=2)
    finally:
        db.close()


@mcp.tool()
def create_task(
    title: str,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: int = 1,
    hashtags: Optional[str] = None,
    category_id: Optional[int] = None,
    parent_id: Optional[int] = None
) -> str:
    """Create a new task.

    Args:
        title: The task title (required)
        description: Task description in markdown format (optional)
        due_date: Due date in ISO format YYYY-MM-DD (optional)
        priority: Priority level - 0=High, 1=Normal, 2=Low (default: 1)
        hashtags: Space or comma separated hashtags (optional)
        category_id: Category ID to assign the task to (optional)
        parent_id: Parent task ID if this is a subtask (optional)

    Returns:
        The created task with its ID
    """
    db = get_db()
    try:
        # Parse due date if provided
        parsed_due_date = None
        if due_date:
            try:
                parsed_due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            except ValueError:
                # Try parsing as date only
                parsed_due_date = datetime.strptime(due_date, "%Y-%m-%d")

        task_create = schemas.TaskCreate(
            title=title,
            description=description,
            due_date=parsed_due_date,
            priority=priority,
            hashtags=hashtags,
            category_id=category_id,
            parent_id=parent_id
        )

        task = crud.create_task(db, task_create)
        return json.dumps(task_to_dict(task), indent=2)
    finally:
        db.close()


@mcp.tool()
def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[int] = None,
    hashtags: Optional[str] = None,
    category_id: Optional[int] = None,
    completed: Optional[bool] = None,
    archived: Optional[bool] = None
) -> str:
    """Update an existing task.

    Only provided fields will be updated. Pass null/None to clear a field.

    Args:
        task_id: The ID of the task to update (required)
        title: New title (optional)
        description: New description (optional)
        due_date: New due date in ISO format YYYY-MM-DD, or empty string to clear (optional)
        priority: New priority 0=High, 1=Normal, 2=Low (optional)
        hashtags: New hashtags (optional)
        category_id: New category ID, or -1 to remove from category (optional)
        completed: Mark as completed or not (optional)
        archived: Mark as archived or not (optional)

    Returns:
        The updated task
    """
    db = get_db()
    try:
        # Construct update dict
        update_data = {}
        if title is not None:
            update_data['title'] = title
        if description is not None:
            update_data['description'] = description
        if due_date is not None:
            if due_date == "":
                update_data['due_date'] = None
            else:
                try:
                    update_data['due_date'] = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                except ValueError:
                    update_data['due_date'] = datetime.strptime(due_date, "%Y-%m-%d")
        if priority is not None:
            update_data['priority'] = priority
        if hashtags is not None:
            update_data['hashtags'] = hashtags
        if category_id is not None:
            update_data['category_id'] = None if category_id == -1 else category_id
        if completed is not None:
            update_data['completed'] = completed
            # If uncompleting, also unarchive (logic from original mcp_server)
            if not completed:
                update_data['archived'] = False
        if archived is not None:
            update_data['archived'] = archived

        if not update_data:
             # No updates
             task = crud.get_task(db, task_id)
             if not task:
                return json.dumps({"error": f"Task with ID {task_id} not found"})
             return json.dumps(task_to_dict(task), indent=2)

        # Use the flexible dict support in crud.update_task
        task = crud.update_task(db, task_id, update_data)
        if not task:
            return json.dumps({"error": f"Task with ID {task_id} not found"})
            
        return json.dumps(task_to_dict(task), indent=2)
    finally:
        db.close()


@mcp.tool()
def complete_task(task_id: int, completed: bool = True) -> str:
    """Mark a task as completed or not completed.

    This is a convenience method for toggling task completion status.
    If uncompleting a task, it will also be unarchived.

    Args:
        task_id: The ID of the task
        completed: True to mark complete, False to mark incomplete (default: True)

    Returns:
        The updated task
    """
    return update_task(task_id, completed=completed)


@mcp.tool()
def delete_task(task_id: int) -> str:
    """Delete a task and all its subtasks.

    Args:
        task_id: The ID of the task to delete

    Returns:
        Confirmation message
    """
    db = get_db()
    try:
        # get task first to get title for message
        task = crud.get_task(db, task_id)
        if not task:
            return json.dumps({"error": f"Task with ID {task_id} not found"})
        
        title = task.title
        crud.delete_task(db, task_id)
        return json.dumps({"message": f"Deleted task: {title}"})
    finally:
        db.close()


@mcp.tool()
def archive_completed(category_id: Optional[int] = None) -> str:
    """Archive all completed tasks.

    Moves completed tasks to archived status so they don't appear in the main list.

    Args:
        category_id: Only archive completed tasks in this category (optional)

    Returns:
        Number of tasks archived
    """
    db = get_db()
    try:
        count = crud.archive_completed_tasks(db, category_id=category_id)
        return json.dumps({"message": f"Archived {count} completed tasks"})
    finally:
        db.close()


@mcp.tool()
def add_subtask(parent_id: int, title: str, description: Optional[str] = None) -> str:
    """Add a subtask to an existing task.

    Subtasks inherit the priority and category of their parent task.

    Args:
        parent_id: The ID of the parent task
        title: The subtask title
        description: Optional description for the subtask

    Returns:
        The created subtask
    """
    db = get_db()
    try:
        parent = crud.get_task(db, parent_id)
        if not parent:
            return json.dumps({"error": f"Parent task with ID {parent_id} not found"})

        task = crud.create_task(db, schemas.TaskCreate(
            title=title,
            description=description,
            priority=parent.priority,
            category_id=parent.category_id,
            parent_id=parent_id
        ))
        return json.dumps(task_to_dict(task), indent=2)
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run()
