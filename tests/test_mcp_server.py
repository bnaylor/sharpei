#!/usr/bin/env python3
"""Tests for the Sharpei MCP server."""
import json

import pytest


class TestCategories:
    """Test category-related MCP tools."""

    def test_list_categories_empty(self, mcp_server):
        """Test listing categories when none exist."""
        result = json.loads(mcp_server.list_categories())
        assert result == []

    def test_create_category(self, mcp_server):
        """Test creating a category."""
        result = json.loads(mcp_server.create_category("Work"))

        assert result["name"] == "Work"
        assert "id" in result
        assert isinstance(result["id"], int)

    def test_list_categories_with_data(self, mcp_server):
        """Test listing categories after creating some."""
        mcp_server.create_category("Work")
        mcp_server.create_category("Personal")

        result = json.loads(mcp_server.list_categories())

        assert len(result) == 2
        names = [c["name"] for c in result]
        assert "Work" in names
        assert "Personal" in names


class TestTasks:
    """Test task-related MCP tools."""

    def test_list_tasks_empty(self, mcp_server):
        """Test listing tasks when none exist."""
        result = json.loads(mcp_server.list_tasks())
        assert result == []

    def test_create_task_minimal(self, mcp_server):
        """Test creating a task with just a title."""
        result = json.loads(mcp_server.create_task("Buy groceries"))

        assert result["title"] == "Buy groceries"
        assert result["completed"] is False
        assert result["archived"] is False
        assert result["priority"] == 1
        assert result["priority_label"] == "Normal"

    def test_create_task_full(self, mcp_server):
        """Test creating a task with all fields."""
        # Create a category first
        cat = json.loads(mcp_server.create_category("Work"))

        result = json.loads(mcp_server.create_task(
            title="Finish report",
            description="Complete the quarterly report with **charts**",
            due_date="2025-02-15",
            priority=0,
            hashtags="#urgent #q4",
            category_id=cat["id"]
        ))

        assert result["title"] == "Finish report"
        assert result["description"] == "Complete the quarterly report with **charts**"
        assert "2025-02-15" in result["due_date"]
        assert result["priority"] == 0
        assert result["priority_label"] == "High"
        assert result["hashtags"] == "#urgent #q4"
        assert result["category_id"] == cat["id"]

    def test_get_task(self, mcp_server):
        """Test getting a specific task."""
        created = json.loads(mcp_server.create_task("Test task"))

        result = json.loads(mcp_server.get_task(created["id"]))

        assert result["id"] == created["id"]
        assert result["title"] == "Test task"

    def test_get_task_not_found(self, mcp_server):
        """Test getting a non-existent task."""
        result = json.loads(mcp_server.get_task(99999))

        assert "error" in result

    def test_update_task(self, mcp_server):
        """Test updating a task."""
        created = json.loads(mcp_server.create_task("Original title"))

        result = json.loads(mcp_server.update_task(
            task_id=created["id"],
            title="Updated title",
            priority=2
        ))

        assert result["title"] == "Updated title"
        assert result["priority"] == 2
        assert result["priority_label"] == "Low"

    def test_complete_task(self, mcp_server):
        """Test completing a task."""
        created = json.loads(mcp_server.create_task("Complete me"))
        assert created["completed"] is False

        result = json.loads(mcp_server.complete_task(created["id"]))

        assert result["completed"] is True

    def test_uncomplete_task_unarchives(self, mcp_server):
        """Test that uncompleting a task also unarchives it."""
        created = json.loads(mcp_server.create_task("Archive test"))

        # Complete and archive
        mcp_server.complete_task(created["id"])
        mcp_server.update_task(created["id"], archived=True)

        # Verify archived
        task = json.loads(mcp_server.get_task(created["id"]))
        assert task["archived"] is True

        # Uncomplete
        result = json.loads(mcp_server.complete_task(created["id"], completed=False))

        assert result["completed"] is False
        assert result["archived"] is False

    def test_delete_task(self, mcp_server):
        """Test deleting a task."""
        created = json.loads(mcp_server.create_task("Delete me"))

        result = json.loads(mcp_server.delete_task(created["id"]))

        assert "message" in result
        assert "Deleted" in result["message"]

        # Verify it's gone
        get_result = json.loads(mcp_server.get_task(created["id"]))
        assert "error" in get_result

    def test_delete_task_not_found(self, mcp_server):
        """Test deleting a non-existent task."""
        result = json.loads(mcp_server.delete_task(99999))

        assert "error" in result


class TestSubtasks:
    """Test subtask functionality."""

    def test_add_subtask(self, mcp_server):
        """Test adding a subtask."""
        parent = json.loads(mcp_server.create_task("Parent task", priority=0))

        result = json.loads(mcp_server.add_subtask(
            parent_id=parent["id"],
            title="Child task"
        ))

        assert result["title"] == "Child task"
        assert result["parent_id"] == parent["id"]
        # Subtask inherits parent's priority
        assert result["priority"] == 0

    def test_subtasks_in_parent(self, mcp_server):
        """Test that subtasks appear in parent task."""
        parent = json.loads(mcp_server.create_task("Parent"))
        mcp_server.add_subtask(parent["id"], "Sub 1")
        mcp_server.add_subtask(parent["id"], "Sub 2")

        result = json.loads(mcp_server.get_task(parent["id"]))

        assert len(result["subtasks"]) == 2
        subtask_titles = [s["title"] for s in result["subtasks"]]
        assert "Sub 1" in subtask_titles
        assert "Sub 2" in subtask_titles

    def test_add_subtask_invalid_parent(self, mcp_server):
        """Test adding subtask to non-existent parent."""
        result = json.loads(mcp_server.add_subtask(99999, "Orphan"))

        assert "error" in result


class TestFiltering:
    """Test task filtering and search."""

    def test_filter_by_category(self, mcp_server):
        """Test filtering tasks by category."""
        cat1 = json.loads(mcp_server.create_category("Work"))
        cat2 = json.loads(mcp_server.create_category("Personal"))

        mcp_server.create_task("Work task", category_id=cat1["id"])
        mcp_server.create_task("Personal task", category_id=cat2["id"])

        result = json.loads(mcp_server.list_tasks(category_id=cat1["id"]))

        assert len(result) == 1
        assert result[0]["title"] == "Work task"

    def test_search_tasks(self, mcp_server):
        """Test searching tasks."""
        mcp_server.create_task("Buy milk")
        mcp_server.create_task("Buy eggs")
        mcp_server.create_task("Clean house")

        result = json.loads(mcp_server.list_tasks(search="buy"))

        assert len(result) == 2
        titles = [t["title"] for t in result]
        assert "Buy milk" in titles
        assert "Buy eggs" in titles

    def test_search_in_description(self, mcp_server):
        """Test that search includes description."""
        mcp_server.create_task("Generic title", description="Find the secret keyword here")

        result = json.loads(mcp_server.list_tasks(search="secret"))

        assert len(result) == 1

    def test_search_in_hashtags(self, mcp_server):
        """Test that search includes hashtags."""
        mcp_server.create_task("Tagged task", hashtags="#important #urgent")

        result = json.loads(mcp_server.list_tasks(search="important"))

        assert len(result) == 1

    def test_archived_tasks_hidden_by_default(self, mcp_server):
        """Test that archived tasks are hidden by default."""
        task = json.loads(mcp_server.create_task("Archive me"))
        mcp_server.complete_task(task["id"])
        mcp_server.update_task(task["id"], archived=True)

        result = json.loads(mcp_server.list_tasks())

        assert len(result) == 0

    def test_include_archived(self, mcp_server):
        """Test including archived tasks."""
        task = json.loads(mcp_server.create_task("Archive me"))
        mcp_server.complete_task(task["id"])
        mcp_server.update_task(task["id"], archived=True)

        result = json.loads(mcp_server.list_tasks(include_archived=True))

        assert len(result) == 1


class TestArchiving:
    """Test archive functionality."""

    def test_archive_completed(self, mcp_server):
        """Test archiving all completed tasks."""
        # Create and complete some tasks
        task1 = json.loads(mcp_server.create_task("Task 1"))
        task2 = json.loads(mcp_server.create_task("Task 2"))
        task3 = json.loads(mcp_server.create_task("Task 3"))

        mcp_server.complete_task(task1["id"])
        mcp_server.complete_task(task2["id"])
        # task3 remains incomplete

        result = json.loads(mcp_server.archive_completed())

        assert "2" in result["message"]  # 2 tasks archived

        # Check that completed tasks are archived
        t1 = json.loads(mcp_server.get_task(task1["id"]))
        t2 = json.loads(mcp_server.get_task(task2["id"]))
        t3 = json.loads(mcp_server.get_task(task3["id"]))

        assert t1["archived"] is True
        assert t2["archived"] is True
        assert t3["archived"] is False

    def test_archive_completed_by_category(self, mcp_server):
        """Test archiving completed tasks in a specific category."""
        cat = json.loads(mcp_server.create_category("Work"))

        task1 = json.loads(mcp_server.create_task("Work task", category_id=cat["id"]))
        task2 = json.loads(mcp_server.create_task("No category"))

        mcp_server.complete_task(task1["id"])
        mcp_server.complete_task(task2["id"])

        result = json.loads(mcp_server.archive_completed(category_id=cat["id"]))

        assert "1" in result["message"]

        t1 = json.loads(mcp_server.get_task(task1["id"]))
        t2 = json.loads(mcp_server.get_task(task2["id"]))

        assert t1["archived"] is True
        assert t2["archived"] is False


class TestPriority:
    """Test priority handling."""

    def test_task_ordering_by_priority(self, mcp_server):
        """Test that tasks are ordered by priority."""
        mcp_server.create_task("Low", priority=2)
        mcp_server.create_task("High", priority=0)
        mcp_server.create_task("Normal", priority=1)

        result = json.loads(mcp_server.list_tasks())

        assert result[0]["title"] == "High"
        assert result[1]["title"] == "Normal"
        assert result[2]["title"] == "Low"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
