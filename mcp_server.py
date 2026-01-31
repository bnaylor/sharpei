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
from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import sessionmaker

from app.models import Base, Category, Task

# Database setup - use the same database as the main app
# Use absolute path to ensure it works regardless of working directory
import os
_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sharpei.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{_db_path}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create MCP server
# Use WARNING log level to prevent debug output from corrupting stdio protocol
mcp = FastMCP("Sharpei TODO", log_level="WARNING")


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Caller is responsible for closing


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
        categories = db.query(Category).all()
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
        category = Category(name=name)
        db.add(category)
        db.commit()
        db.refresh(category)
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
        query = db.query(Task)

        if search:
            search_filter = or_(
                Task.title.ilike(f"%{search}%"),
                Task.description.ilike(f"%{search}%"),
                Task.hashtags.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        else:
            # Only top-level tasks if not searching
            query = query.filter(Task.parent_id == None)

        if not include_archived:
            query = query.filter(Task.archived == False)

        if category_id is not None:
            query = query.filter(Task.category_id == category_id)

        if priority is not None:
            query = query.filter(Task.priority == priority)

        tasks = query.order_by(Task.priority.asc(), Task.position.asc(), Task.id.desc()).all()

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
        task = db.query(Task).filter(Task.id == task_id).first()
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

        # Calculate position
        max_pos = db.query(func.max(Task.position)).filter(
            Task.priority == priority,
            Task.parent_id == parent_id
        ).scalar()
        position = (max_pos or 0) + 1

        task = Task(
            title=title,
            description=description,
            due_date=parsed_due_date,
            priority=priority,
            position=position,
            hashtags=hashtags,
            category_id=category_id,
            parent_id=parent_id,
            completed=False,
            archived=False
        )
        db.add(task)
        db.commit()
        db.refresh(task)
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
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return json.dumps({"error": f"Task with ID {task_id} not found"})

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if due_date is not None:
            if due_date == "":
                task.due_date = None
            else:
                try:
                    task.due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                except ValueError:
                    task.due_date = datetime.strptime(due_date, "%Y-%m-%d")
        if priority is not None:
            task.priority = priority
        if hashtags is not None:
            task.hashtags = hashtags
        if category_id is not None:
            task.category_id = None if category_id == -1 else category_id
        if completed is not None:
            task.completed = completed
            # If uncompleting, also unarchive
            if not completed:
                task.archived = False
        if archived is not None:
            task.archived = archived

        db.commit()
        db.refresh(task)
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
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return json.dumps({"error": f"Task with ID {task_id} not found"})

        title = task.title
        db.delete(task)
        db.commit()
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
        query = db.query(Task).filter(
            Task.completed == True,
            Task.archived == False
        )
        if category_id is not None:
            query = query.filter(Task.category_id == category_id)

        count = query.update({"archived": True})
        db.commit()
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
        parent = db.query(Task).filter(Task.id == parent_id).first()
        if not parent:
            return json.dumps({"error": f"Parent task with ID {parent_id} not found"})

        return create_task(
            title=title,
            description=description,
            priority=parent.priority,
            category_id=parent.category_id,
            parent_id=parent_id
        )
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run()
