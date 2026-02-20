#!/usr/bin/env python3
"""UI tests for Sharpei using Playwright."""
import re
from datetime import datetime, timedelta

import pytest
from playwright.sync_api import expect


class TestPageLoad:
    """Test basic page loading."""

    def test_page_loads(self, ui_page):
        """Test that the page loads successfully."""
        expect(ui_page).to_have_title("Sharpei - TODO")

    def test_banner_visible(self, ui_page):
        """Test that the app banner is visible."""
        banner = ui_page.locator(".app-banner")
        expect(banner).to_be_visible()
        expect(banner.locator(".app-title")).to_have_text("Sharpei")

    def test_sidebar_visible(self, ui_page):
        """Test that the sidebar is visible."""
        sidebar = ui_page.locator("#sidebar")
        expect(sidebar).to_be_visible()
        expect(sidebar.locator("text=All Tasks")).to_be_visible()


class TestCategoryManagement:
    """Test category creation and selection."""

    def test_create_category(self, ui_page):
        """Test creating a new category."""
        # Find the category input and add button
        input_field = ui_page.locator("#sidebar input[placeholder='New category']")
        add_button = ui_page.locator("#sidebar button:has(i.bi-plus)")

        # Create a category
        input_field.fill("Work")
        add_button.click()

        # Wait for category to appear in sidebar
        ui_page.wait_for_selector("text=Work")
        expect(ui_page.locator("#sidebar")).to_contain_text("Work")

    def test_select_category(self, ui_page):
        """Test selecting a category."""
        # Create a category first
        input_field = ui_page.locator("#sidebar input[placeholder='New category']")
        input_field.fill("Personal")
        input_field.press("Enter")
        ui_page.wait_for_selector("text=Personal")

        # Click on the category
        ui_page.locator("#sidebar a:has-text('Personal')").click()

        # Check the header changed
        expect(ui_page.locator("h1.h2")).to_have_text("Personal")

    def test_all_tasks_selected_by_default(self, ui_page):
        """Test that 'All Tasks' is selected by default."""
        all_tasks_link = ui_page.locator("#sidebar a:has-text('All Tasks')")
        expect(all_tasks_link).to_have_class(re.compile(r"active"))


class TestTaskManagement:
    """Test task creation and management."""

    def test_create_task(self, ui_page):
        """Test creating a new task."""
        # Find the task input
        input_field = ui_page.locator("input[placeholder='Add a task...']")

        # Create a task
        input_field.fill("Buy groceries")
        input_field.press("Enter")

        # Wait for task to appear
        ui_page.wait_for_selector("text=Buy groceries")
        expect(ui_page.locator(".task-list")).to_contain_text("Buy groceries")

    def test_create_task_with_button(self, ui_page):
        """Test creating a task using the Add button."""
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        add_button = ui_page.locator("button:has-text('Add Task')")

        input_field.fill("Call mom")
        add_button.click()

        ui_page.wait_for_selector("text=Call mom")
        expect(ui_page.locator(".task-list")).to_contain_text("Call mom")

    def test_complete_task(self, ui_page):
        """Test completing a task."""
        # Create a task
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Complete me")
        input_field.press("Enter")
        ui_page.wait_for_selector("text=Complete me")

        # Find the checkbox and click it
        checkbox = ui_page.locator(".task-item:has-text('Complete me') input[type='checkbox']")
        checkbox.click()

        # Verify the task is crossed out
        task_title = ui_page.locator(".task-item:has-text('Complete me') .task-title")
        expect(task_title).to_have_class(re.compile(r"text-decoration-line-through"))

    def test_uncomplete_task(self, ui_page):
        """Test uncompleting a task."""
        # Create and complete a task
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Toggle me")
        input_field.press("Enter")
        ui_page.wait_for_selector("text=Toggle me")

        checkbox = ui_page.locator(".task-item:has-text('Toggle me') input[type='checkbox']")
        checkbox.click()  # Complete
        ui_page.wait_for_timeout(300)
        checkbox.click()  # Uncomplete

        # Verify the task is not crossed out
        task_title = ui_page.locator(".task-item:has-text('Toggle me') .task-title")
        expect(task_title).not_to_have_class(re.compile(r"text-decoration-line-through"))

    def test_delete_task(self, ui_page):
        """Test deleting a task."""
        # Create a task
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Delete me")
        input_field.press("Enter")
        ui_page.wait_for_selector("text=Delete me")

        # Click delete button (need to handle confirmation dialog)
        ui_page.on("dialog", lambda dialog: dialog.accept())
        delete_button = ui_page.locator(".task-item:has-text('Delete me') button:has(i.bi-trash)")
        delete_button.click()

        # Verify task is gone
        ui_page.wait_for_timeout(500)
        expect(ui_page.locator(".task-list")).not_to_contain_text("Delete me")


class TestTaskExpansion:
    """Test task expansion and details."""

    def test_expand_task(self, ui_page):
        """Test expanding a task to see details."""
        # Create a task
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Expandable task")
        input_field.press("Enter")
        ui_page.wait_for_selector("text=Expandable task")

        # Click on the task title to expand
        ui_page.locator(".task-title:has-text('Expandable task')").click()

        # Verify details panel is visible
        details = ui_page.locator(".task-details")
        expect(details).to_be_visible()

    def test_edit_task_description(self, ui_page):
        """Test editing a task description."""
        # Create a task
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Task with description")
        input_field.press("Enter")
        ui_page.wait_for_selector("text=Task with description")

        # Expand the task
        ui_page.locator(".task-title:has-text('Task with description')").click()
        ui_page.wait_for_selector(".task-details")

        # Fill in description
        textarea = ui_page.locator(".task-details textarea")
        textarea.fill("This is my **markdown** description")

        # Save
        ui_page.locator(".task-details button:has-text('Save')").click()
        ui_page.wait_for_timeout(500)

        # Re-expand and verify
        ui_page.locator(".task-title:has-text('Task with description')").click()
        expect(textarea).to_have_value("This is my **markdown** description")

    def test_change_task_priority(self, ui_page):
        """Test changing task priority."""
        # Create a task
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Priority task")
        input_field.press("Enter")
        ui_page.wait_for_selector("text=Priority task")

        # Expand and change priority
        ui_page.locator(".task-title:has-text('Priority task')").click()
        ui_page.wait_for_selector(".task-details")

        priority_select = ui_page.locator(".task-details select").first
        priority_select.select_option("0")  # High priority

        ui_page.locator(".task-details button:has-text('Save')").click()
        ui_page.wait_for_timeout(500)

        # Verify task moved to high priority section
        high_priority_section = ui_page.locator("#list-p0")
        expect(high_priority_section).to_contain_text("Priority task")

    def test_save_button_disabled_on_expand(self, ui_page):
        """Test that Save button is disabled when a task is first expanded."""
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Dirty tracking task A")
        input_field.press("Enter")
        ui_page.wait_for_selector(".task-title:has-text('Dirty tracking task A')")

        ui_page.locator(".task-title:has-text('Dirty tracking task A')").click()
        ui_page.wait_for_selector(".task-details")

        save_btn = ui_page.locator(".task-details button:has-text('Save')")
        expect(save_btn).to_be_disabled()
        expect(save_btn).to_have_class(re.compile(r"btn-secondary"))

    def test_save_button_enabled_after_change(self, ui_page):
        """Test that Save button enables after a field is changed."""
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Dirty tracking task B")
        input_field.press("Enter")
        ui_page.wait_for_selector(".task-title:has-text('Dirty tracking task B')")

        ui_page.locator(".task-title:has-text('Dirty tracking task B')").click()
        ui_page.wait_for_selector(".task-details")

        textarea = ui_page.locator(".task-details textarea")
        textarea.fill("Some new description")

        save_btn = ui_page.locator(".task-details button:has-text('Save')")
        expect(save_btn).to_be_enabled()
        expect(save_btn).to_have_class(re.compile(r"btn-success"))


class TestSubtasks:
    """Test subtask functionality."""

    def test_add_subtask(self, ui_page):
        """Test adding a subtask."""
        # Create a parent task
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Parent task")
        input_field.press("Enter")
        ui_page.wait_for_selector(".task-title:has-text('Parent task')")

        # Expand the task
        ui_page.locator(".task-title:has-text('Parent task')").click()
        ui_page.wait_for_selector(".task-details")

        # Add a subtask
        subtask_input = ui_page.locator(".task-details input[placeholder='Add subtask...']")
        subtask_input.fill("Child task")
        subtask_input.press("Enter")

        # Wait for subtask to appear in the subtasks section
        ui_page.wait_for_timeout(500)
        subtask_item = ui_page.locator(".task-details .d-flex:has-text('Child task')")
        expect(subtask_item).to_be_visible()


class TestSearch:
    """Test search functionality."""

    def test_search_tasks(self, ui_page):
        """Test searching for tasks."""
        # Create some tasks
        input_field = ui_page.locator("input[placeholder='Add a task...']")

        input_field.fill("Buy apples")
        input_field.press("Enter")
        ui_page.wait_for_selector(".task-title:has-text('Buy apples')")

        input_field.fill("Buy oranges")
        input_field.press("Enter")
        ui_page.wait_for_selector(".task-title:has-text('Buy oranges')")

        input_field.fill("Clean kitchen")
        input_field.press("Enter")
        ui_page.wait_for_selector(".task-title:has-text('Clean kitchen')")

        # Search for "buy"
        search_input = ui_page.locator("input[placeholder='Search...']")
        search_input.fill("buy")
        ui_page.locator("button:has(i.bi-search)").click()

        ui_page.wait_for_timeout(500)

        # Verify only buy tasks are shown
        expect(ui_page.locator(".task-list")).to_contain_text("Buy apples")
        expect(ui_page.locator(".task-list")).to_contain_text("Buy oranges")
        expect(ui_page.locator(".task-list")).not_to_contain_text("Clean kitchen")

    def test_clear_search(self, ui_page):
        """Test clearing search."""
        # Create tasks
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Searchable task")
        input_field.press("Enter")
        ui_page.wait_for_selector(".task-title:has-text('Searchable task')")

        input_field.fill("Other task")
        input_field.press("Enter")
        ui_page.wait_for_selector(".task-title:has-text('Other task')")

        # Search
        search_input = ui_page.locator("input[placeholder='Search...']")
        search_input.fill("Searchable")
        ui_page.locator("button:has(i.bi-search)").click()
        ui_page.wait_for_timeout(500)

        # Verify only one task shown
        expect(ui_page.locator(".task-list")).to_contain_text("Searchable task")
        expect(ui_page.locator(".task-list")).not_to_contain_text("Other task")

        # Clear search
        ui_page.locator("button:has(i.bi-x-lg)").click()
        ui_page.wait_for_timeout(500)

        # Both tasks should be visible
        expect(ui_page.locator(".task-list")).to_contain_text("Searchable task")
        expect(ui_page.locator(".task-list")).to_contain_text("Other task")


class TestArchiving:
    """Test archiving functionality."""

    def test_archive_completed_tasks(self, ui_page):
        """Test archiving completed tasks."""
        # Create and complete a task
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Archive me")
        input_field.press("Enter")
        ui_page.wait_for_selector("text=Archive me")

        checkbox = ui_page.locator(".task-item:has-text('Archive me') input[type='checkbox']")
        checkbox.click()
        ui_page.wait_for_timeout(300)

        # Click Clean Up button
        ui_page.locator("button:has-text('Clean Up')").click()
        ui_page.wait_for_timeout(500)

        # Task should be hidden
        expect(ui_page.locator(".task-list")).not_to_contain_text("Archive me")

    def test_show_archived_tasks(self, ui_page):
        """Test showing archived tasks."""
        # Create, complete, and archive a task
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Hidden task")
        input_field.press("Enter")
        ui_page.wait_for_selector("text=Hidden task")

        checkbox = ui_page.locator(".task-item:has-text('Hidden task') input[type='checkbox']")
        checkbox.click()
        ui_page.wait_for_timeout(300)

        ui_page.locator("button:has-text('Clean Up')").click()
        ui_page.wait_for_timeout(500)

        # Toggle show archived
        ui_page.locator("button:has-text('Show Archived')").click()
        ui_page.wait_for_timeout(500)

        # Task should be visible again
        expect(ui_page.locator(".task-list")).to_contain_text("Hidden task")


class TestShowDetails:
    """Test show details toggle."""

    def test_toggle_show_details(self, ui_page):
        """Test the show details toggle."""
        # Create a task with description
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Detailed task")
        input_field.press("Enter")
        ui_page.wait_for_selector("text=Detailed task")

        # Expand and add description
        ui_page.locator(".task-title:has-text('Detailed task')").click()
        ui_page.wait_for_selector(".task-details")

        textarea = ui_page.locator(".task-details textarea")
        textarea.fill("Some details here")
        ui_page.locator(".task-details button:has-text('Save')").click()
        ui_page.wait_for_timeout(500)

        # Collapse task
        ui_page.locator(".task-title:has-text('Detailed task')").click()
        ui_page.wait_for_timeout(300)

        # Click show details
        ui_page.locator("button:has-text('Show Details')").click()
        ui_page.wait_for_timeout(500)

        # Compact details should be visible
        expect(ui_page.locator(".task-compact-details")).to_be_visible()


class TestHashtags:
    """Test hashtag functionality."""

    def test_add_hashtag(self, ui_page):
        """Test adding hashtags to a task."""
        # Create a task
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Tagged task")
        input_field.press("Enter")
        ui_page.wait_for_selector("text=Tagged task")

        # Expand and add hashtag
        ui_page.locator(".task-title:has-text('Tagged task')").click()
        ui_page.wait_for_selector(".task-details")

        hashtag_input = ui_page.locator(".task-details input[placeholder='#tags']")
        hashtag_input.fill("#work #urgent")
        ui_page.locator(".task-details button:has-text('Save')").click()
        ui_page.wait_for_timeout(500)

        # Verify tags appear as badges
        expect(ui_page.locator(".task-item:has-text('Tagged task')")).to_contain_text("#work")
        expect(ui_page.locator(".task-item:has-text('Tagged task')")).to_contain_text("#urgent")

    def test_filter_by_hashtag(self, ui_page):
        """Test filtering by clicking a hashtag."""
        # Create tasks with different tags
        input_field = ui_page.locator("input[placeholder='Add a task...']")

        input_field.fill("Work task")
        input_field.press("Enter")
        ui_page.wait_for_selector("text=Work task")

        # Add hashtag to first task
        ui_page.locator(".task-title:has-text('Work task')").click()
        ui_page.wait_for_selector(".task-details")
        hashtag_input = ui_page.locator(".task-details input[placeholder='#tags']")
        hashtag_input.fill("#work")
        ui_page.locator(".task-details button:has-text('Save')").click()
        ui_page.wait_for_timeout(500)

        # Create another task without tag
        input_field.fill("Personal task")
        input_field.press("Enter")
        ui_page.wait_for_selector("text=Personal task")

        # Click on the #work tag
        ui_page.locator(".badge:has-text('#work')").click()
        ui_page.wait_for_timeout(500)

        # Only work task should be visible
        expect(ui_page.locator(".task-list")).to_contain_text("Work task")
        expect(ui_page.locator(".task-list")).not_to_contain_text("Personal task")


class TestQuickAdd:
    """Test quick-add syntax parsing."""

    def test_quick_add_with_priority_high(self, ui_page):
        """Test quick-add with high priority."""
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Urgent task !high")
        input_field.press("Enter")

        ui_page.wait_for_selector(".task-title:has-text('Urgent task')")

        # Verify task is in high priority section
        high_priority_section = ui_page.locator("#list-p0")
        expect(high_priority_section).to_contain_text("Urgent task")

    def test_quick_add_with_priority_low(self, ui_page):
        """Test quick-add with low priority."""
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Someday task !low")
        input_field.press("Enter")

        ui_page.wait_for_selector(".task-title:has-text('Someday task')")

        # Verify task is in low priority section
        low_priority_section = ui_page.locator("#list-p2")
        expect(low_priority_section).to_contain_text("Someday task")

    def test_quick_add_with_hashtags(self, ui_page):
        """Test quick-add with hashtags."""
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Tagged task #work #urgent")
        input_field.press("Enter")

        ui_page.wait_for_selector(".task-title:has-text('Tagged task')")
        ui_page.wait_for_timeout(300)

        # Verify tags appear
        task_item = ui_page.locator(".task-item:has-text('Tagged task')")
        expect(task_item).to_contain_text("#work")
        expect(task_item).to_contain_text("#urgent")

    def test_quick_add_with_due_date_tomorrow(self, ui_page):
        """Test quick-add with @tomorrow."""
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Due soon @tomorrow")
        input_field.press("Enter")

        ui_page.wait_for_selector(".task-title:has-text('Due soon')")
        ui_page.wait_for_timeout(300)

        # Verify due date shows "Tomorrow"
        task_item = ui_page.locator(".task-item:has-text('Due soon')")
        expect(task_item).to_contain_text("Tomorrow")

    def test_quick_add_with_due_date_today(self, ui_page):
        """Test quick-add with @today."""
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Do now @today")
        input_field.press("Enter")

        ui_page.wait_for_selector(".task-title:has-text('Do now')")
        ui_page.wait_for_timeout(300)

        # Verify due date shows "Today"
        task_item = ui_page.locator(".task-item:has-text('Do now')")
        expect(task_item).to_contain_text("Today")

    def test_quick_add_with_category(self, ui_page):
        """Test quick-add with category override."""
        # Create a category first
        cat_input = ui_page.locator("#sidebar input[placeholder='New category']")
        cat_input.fill("Work")
        cat_input.press("Enter")
        ui_page.wait_for_selector("#sidebar a:has-text('Work')")

        # Add task with category override (while "All Tasks" is selected)
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Work stuff >Work")
        input_field.press("Enter")

        ui_page.wait_for_selector(".task-title:has-text('Work stuff')")

        # Switch to Work category and verify task is there
        ui_page.locator("#sidebar a:has-text('Work')").click()
        ui_page.wait_for_timeout(500)

        expect(ui_page.locator(".task-list")).to_contain_text("Work stuff")

    def test_quick_add_combined(self, ui_page):
        """Test quick-add with multiple elements."""
        # Create category
        cat_input = ui_page.locator("#sidebar input[placeholder='New category']")
        cat_input.fill("Projects")
        cat_input.press("Enter")
        ui_page.wait_for_selector("#sidebar a:has-text('Projects')")

        # Add task with everything
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Big project !high #important #q1 @tomorrow >Projects")
        input_field.press("Enter")

        ui_page.wait_for_selector(".task-title:has-text('Big project')")
        ui_page.wait_for_timeout(300)

        # Verify it's in high priority
        high_priority_section = ui_page.locator("#list-p0")
        expect(high_priority_section).to_contain_text("Big project")

        # Verify tags
        task_item = ui_page.locator(".task-item:has-text('Big project')")
        expect(task_item).to_contain_text("#important")
        expect(task_item).to_contain_text("#q1")

        # Verify due date
        expect(task_item).to_contain_text("Tomorrow")

    def test_quick_add_title_only(self, ui_page):
        """Test that plain text still works."""
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Simple task with no special syntax")
        input_field.press("Enter")

        ui_page.wait_for_selector(".task-title:has-text('Simple task with no special syntax')")

        # Should be in Normal priority
        normal_section = ui_page.locator("#list-p1")
        expect(normal_section).to_contain_text("Simple task with no special syntax")


class TestBugFixes:
    """Tests for specific bug fixes."""

    def test_completed_task_not_marked_overdue(self, ui_page):
        """Test that a completed task doesn't show 'Overdue'."""
        # Create a task with a past due date
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill(f"Overdue task @{yesterday}")
        input_field.press("Enter")

        ui_page.wait_for_selector(".task-title:has-text('Overdue task')")
        ui_page.wait_for_timeout(300)

        # Verify it shows "Overdue"
        task_item = ui_page.locator(".task-item:has-text('Overdue task')")
        expect(task_item.locator(".due-date")).to_contain_text("Overdue")
        expect(task_item.locator(".due-date")).to_have_class(re.compile(r"overdue"))

        # Complete the task
        checkbox = task_item.locator("input[type='checkbox']")
        checkbox.click()
        ui_page.wait_for_timeout(300)

        # Verify it NO LONGER shows "Overdue" but shows the date or something else
        # and doesn't have the "overdue" class
        expect(task_item.locator(".due-date")).not_to_contain_text("Overdue")
        expect(task_item.locator(".due-date")).not_to_have_class(re.compile(r"overdue"))

    def test_doc_link_exists(self, ui_page):
        """Test that the documentation link is present in the banner."""
        doc_link = ui_page.locator(".app-banner a:has-text('Documentation')")
        expect(doc_link).to_be_visible()
        expect(doc_link).to_have_attribute("href", "https://github.com/bnaylor/sharpei")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
