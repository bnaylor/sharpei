#!/usr/bin/env python3
"""Tests for the Sharpei FastAPI endpoints."""
import pytest


class TestRootEndpoint:
    """Test the root endpoint."""

    def test_root_returns_html(self, api_client):
        """Test that root returns the HTML template."""
        response = api_client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Sharpei" in response.text


class TestCategoryEndpoints:
    """Test category API endpoints."""

    def test_list_categories_empty(self, api_client):
        """Test listing categories when none exist."""
        response = api_client.get("/api/categories")

        assert response.status_code == 200
        assert response.json() == []

    def test_create_category(self, api_client):
        """Test creating a category."""
        response = api_client.post(
            "/api/categories",
            json={"name": "Work"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Work"
        assert "id" in data

    def test_list_categories_with_data(self, api_client):
        """Test listing categories after creating some."""
        api_client.post("/api/categories", json={"name": "Work"})
        api_client.post("/api/categories", json={"name": "Personal"})

        response = api_client.get("/api/categories")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = [c["name"] for c in data]
        assert "Work" in names
        assert "Personal" in names

    def test_delete_category(self, api_client):
        """Test deleting a category."""
        # Create category
        create_resp = api_client.post("/api/categories", json={"name": "ToDelete"})
        cat_id = create_resp.json()["id"]

        # Delete it
        response = api_client.delete(f"/api/categories/{cat_id}")

        assert response.status_code == 200

        # Verify it's gone
        list_resp = api_client.get("/api/categories")
        assert len(list_resp.json()) == 0

    def test_delete_category_moves_tasks(self, api_client):
        """Test that deleting a category moves tasks to no category."""
        # Create category and task
        cat = api_client.post("/api/categories", json={"name": "Work"}).json()
        task = api_client.post("/api/tasks", json={
            "title": "Work task",
            "category_id": cat["id"]
        }).json()

        # Delete category
        api_client.delete(f"/api/categories/{cat['id']}")

        # Check task now has no category
        tasks = api_client.get("/api/tasks").json()
        assert len(tasks) == 1
        assert tasks[0]["category_id"] is None


class TestTaskEndpoints:
    """Test task API endpoints."""

    def test_list_tasks_empty(self, api_client):
        """Test listing tasks when none exist."""
        response = api_client.get("/api/tasks")

        assert response.status_code == 200
        assert response.json() == []

    def test_create_task_minimal(self, api_client):
        """Test creating a task with just a title."""
        response = api_client.post(
            "/api/tasks",
            json={"title": "Buy groceries"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Buy groceries"
        assert data["completed"] is False
        assert data["priority"] == 1

    def test_create_task_full(self, api_client):
        """Test creating a task with all fields."""
        cat = api_client.post("/api/categories", json={"name": "Work"}).json()

        response = api_client.post("/api/tasks", json={
            "title": "Finish report",
            "description": "Complete the quarterly report",
            "due_date": "2025-02-15T12:00:00",
            "priority": 0,
            "hashtags": "#urgent #q4",
            "category_id": cat["id"]
        })

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Finish report"
        assert data["description"] == "Complete the quarterly report"
        assert data["priority"] == 0
        assert data["hashtags"] == "#urgent #q4"
        assert data["category_id"] == cat["id"]

    def test_get_task(self, api_client):
        """Test getting tasks includes the created task."""
        create_resp = api_client.post("/api/tasks", json={"title": "Test task"})
        task_id = create_resp.json()["id"]

        response = api_client.get("/api/tasks")

        assert response.status_code == 200
        tasks = response.json()
        assert any(t["id"] == task_id for t in tasks)

    def test_update_task(self, api_client):
        """Test updating a task."""
        create_resp = api_client.post("/api/tasks", json={"title": "Original"})
        task_id = create_resp.json()["id"]

        response = api_client.put(f"/api/tasks/{task_id}", json={
            "title": "Updated",
            "priority": 2,
            "completed": False
        })

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["priority"] == 2

    def test_update_task_not_found(self, api_client):
        """Test updating a non-existent task."""
        response = api_client.put("/api/tasks/99999", json={
            "title": "Ghost",
            "completed": False
        })

        assert response.status_code == 404

    def test_delete_task(self, api_client):
        """Test deleting a task."""
        create_resp = api_client.post("/api/tasks", json={"title": "Delete me"})
        task_id = create_resp.json()["id"]

        response = api_client.delete(f"/api/tasks/{task_id}")

        assert response.status_code == 200

        # Verify it's gone
        tasks = api_client.get("/api/tasks").json()
        assert not any(t["id"] == task_id for t in tasks)

    def test_delete_task_not_found(self, api_client):
        """Test deleting a non-existent task."""
        response = api_client.delete("/api/tasks/99999")

        assert response.status_code == 404

    def test_delete_task_cascades_subtasks(self, api_client):
        """Test that deleting a task also deletes its subtasks."""
        # Create parent and subtask
        parent = api_client.post("/api/tasks", json={"title": "Parent"}).json()
        subtask = api_client.post("/api/tasks", json={
            "title": "Child",
            "parent_id": parent["id"]
        }).json()

        # Delete parent
        api_client.delete(f"/api/tasks/{parent['id']}")

        # Verify subtask is also gone (search to find all tasks)
        tasks = api_client.get("/api/tasks", params={"q": "Child"}).json()
        assert len(tasks) == 0


class TestTaskFiltering:
    """Test task filtering and search."""

    def test_filter_by_category(self, api_client):
        """Test filtering tasks by category."""
        cat1 = api_client.post("/api/categories", json={"name": "Work"}).json()
        cat2 = api_client.post("/api/categories", json={"name": "Personal"}).json()

        api_client.post("/api/tasks", json={"title": "Work task", "category_id": cat1["id"]})
        api_client.post("/api/tasks", json={"title": "Personal task", "category_id": cat2["id"]})

        response = api_client.get("/api/tasks", params={"category_id": cat1["id"]})

        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Work task"

    def test_search_tasks(self, api_client):
        """Test searching tasks."""
        api_client.post("/api/tasks", json={"title": "Buy milk"})
        api_client.post("/api/tasks", json={"title": "Buy eggs"})
        api_client.post("/api/tasks", json={"title": "Clean house"})

        response = api_client.get("/api/tasks", params={"q": "buy"})

        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2

    def test_search_case_insensitive(self, api_client):
        """Test that search is case insensitive."""
        api_client.post("/api/tasks", json={"title": "UPPERCASE TASK"})

        response = api_client.get("/api/tasks", params={"q": "uppercase"})

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_archived_hidden_by_default(self, api_client):
        """Test that archived tasks are hidden by default."""
        task = api_client.post("/api/tasks", json={"title": "Archive me"}).json()
        api_client.put(f"/api/tasks/{task['id']}", json={
            "title": "Archive me",
            "completed": True,
            "archived": True
        })

        response = api_client.get("/api/tasks")

        assert len(response.json()) == 0

    def test_show_archived(self, api_client):
        """Test including archived tasks."""
        task = api_client.post("/api/tasks", json={"title": "Archive me"}).json()
        api_client.put(f"/api/tasks/{task['id']}", json={
            "title": "Archive me",
            "completed": True,
            "archived": True
        })

        response = api_client.get("/api/tasks", params={"show_archived": True})

        assert len(response.json()) == 1


class TestTaskReordering:
    """Test task reordering endpoint."""

    def test_reorder_tasks(self, api_client):
        """Test reordering tasks."""
        t1 = api_client.post("/api/tasks", json={"title": "Task 1"}).json()
        t2 = api_client.post("/api/tasks", json={"title": "Task 2"}).json()
        t3 = api_client.post("/api/tasks", json={"title": "Task 3"}).json()

        # Reorder: 3, 1, 2
        response = api_client.post("/api/tasks/reorder", json={
            "task_ids": [t3["id"], t1["id"], t2["id"]]
        })

        assert response.status_code == 200

        # Verify order
        tasks = api_client.get("/api/tasks").json()
        titles = [t["title"] for t in tasks]
        assert titles == ["Task 3", "Task 1", "Task 2"]


class TestArchiveCompleted:
    """Test archive completed endpoint."""

    def test_archive_completed(self, api_client):
        """Test archiving all completed tasks."""
        t1 = api_client.post("/api/tasks", json={"title": "Task 1"}).json()
        t2 = api_client.post("/api/tasks", json={"title": "Task 2"}).json()

        # Complete one task
        api_client.put(f"/api/tasks/{t1['id']}", json={
            "title": "Task 1",
            "completed": True
        })

        # Archive completed
        response = api_client.post("/api/tasks/archive-completed")

        assert response.status_code == 200
        assert "1" in response.json()["message"]

        # Verify only incomplete task visible
        tasks = api_client.get("/api/tasks").json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Task 2"

    def test_archive_completed_by_category(self, api_client):
        """Test archiving completed tasks in specific category."""
        cat = api_client.post("/api/categories", json={"name": "Work"}).json()

        t1 = api_client.post("/api/tasks", json={
            "title": "Work task",
            "category_id": cat["id"]
        }).json()
        t2 = api_client.post("/api/tasks", json={"title": "No category"}).json()

        # Complete both
        for t in [t1, t2]:
            api_client.put(f"/api/tasks/{t['id']}", json={
                "title": t["title"],
                "completed": True
            })

        # Archive only in category
        response = api_client.post(
            "/api/tasks/archive-completed",
            params={"category_id": cat["id"]}
        )

        assert "1" in response.json()["message"]

        # Verify uncategorized task still visible
        tasks = api_client.get("/api/tasks").json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "No category"


class TestSubtasks:
    """Test subtask functionality via API."""

    def test_create_subtask(self, api_client):
        """Test creating a subtask."""
        parent = api_client.post("/api/tasks", json={"title": "Parent"}).json()

        response = api_client.post("/api/tasks", json={
            "title": "Subtask",
            "parent_id": parent["id"]
        })

        assert response.status_code == 200
        data = response.json()
        assert data["parent_id"] == parent["id"]

    def test_subtasks_in_response(self, api_client):
        """Test that subtasks are included in task response."""
        parent = api_client.post("/api/tasks", json={"title": "Parent"}).json()
        api_client.post("/api/tasks", json={
            "title": "Sub 1",
            "parent_id": parent["id"]
        })
        api_client.post("/api/tasks", json={
            "title": "Sub 2",
            "parent_id": parent["id"]
        })

        response = api_client.get("/api/tasks")
        tasks = response.json()

        # Find parent task
        parent_task = next(t for t in tasks if t["id"] == parent["id"])
        assert len(parent_task["subtasks"]) == 2

    def test_subtasks_hidden_at_top_level(self, api_client):
        """Test that subtasks don't appear as top-level tasks."""
        parent = api_client.post("/api/tasks", json={"title": "Parent"}).json()
        api_client.post("/api/tasks", json={
            "title": "Subtask",
            "parent_id": parent["id"]
        })

        response = api_client.get("/api/tasks")
        tasks = response.json()

        # Only parent should be at top level
        top_level = [t for t in tasks if t["parent_id"] is None]
        assert len(top_level) == 1
        assert top_level[0]["title"] == "Parent"


class TestPositionAutoAssignment:
    """Test automatic position assignment."""

    def test_new_task_gets_position(self, api_client):
        """Test that new tasks get auto-assigned positions."""
        t1 = api_client.post("/api/tasks", json={"title": "Task 1"}).json()
        t2 = api_client.post("/api/tasks", json={"title": "Task 2"}).json()
        t3 = api_client.post("/api/tasks", json={"title": "Task 3"}).json()

        # Each should have incrementing positions
        assert t1["position"] == 1
        assert t2["position"] == 2
        assert t3["position"] == 3

    def test_position_per_priority(self, api_client):
        """Test that positions are assigned per priority level."""
        t1 = api_client.post("/api/tasks", json={"title": "Normal 1", "priority": 1}).json()
        t2 = api_client.post("/api/tasks", json={"title": "High 1", "priority": 0}).json()
        t3 = api_client.post("/api/tasks", json={"title": "Normal 2", "priority": 1}).json()

        # High priority task should have position 1 (first in its group)
        assert t2["position"] == 1
        # Normal tasks should be 1 and 2
        assert t1["position"] == 1
        assert t3["position"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
