#!/usr/bin/env python3
"""Robust UI smoke and stress tests for Sharpei."""
import pytest
from playwright.sync_api import expect
import logging

class TestUISmoke:
    """Smoke tests to ensure the UI isn't fundamentally broken."""

    @pytest.fixture(autouse=True)
    def setup_console_capture(self, ui_page):
        """Fail the test if any console errors occur."""
        self.console_errors = []
        ui_page.on("console", lambda msg: self.console_errors.append(msg.text) if msg.type == "error" else None)
        ui_page.on("pageerror", lambda err: self.console_errors.append(str(err)))
        yield
        if self.console_errors:
            pytest.fail(f"Browser console errors detected: {self.console_errors}")

    def test_ui_renders_various_task_types(self, ui_page):
        """Stress test: Add many types of tasks and ensure they all render."""
        tasks_to_add = [
            "Normal task",
            "High priority !high",
            "Low priority !low",
            "Task with tags #work #urgent",
            "Task with date @today",
            "Task with recurrence *daily",
            "Task with everything !high @tomorrow #boss *weekly",
            "Task with weird characters !@#$%^&*()",
            "Subtask parent",
        ]

        input_field = ui_page.locator("input[placeholder='Add a task...']")
        
        for task_text in tasks_to_add:
            input_field.fill(task_text)
            input_field.press("Enter")
            ui_page.wait_for_timeout(200)

        # Verify all tasks are rendered
        for task_text in tasks_to_add:
            display_text = task_text.split('!')[0].split('@')[0].split('#')[0].split('*')[0].strip()
            expect(ui_page.locator(f".task-item:has-text('{display_text}')")).to_be_visible()

    def test_expand_and_save_functionality(self, ui_page):
        """Ensure that expanding and saving a task still works."""
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Expand test task")
        input_field.press("Enter")
        
        task_item = ui_page.locator(".task-item:has-text('Expand test task')")
        ui_page.wait_for_selector(".task-item:has-text('Expand test task')")
        
        # Click to expand
        task_item.locator(".task-title").click()
        
        # Verify details are visible
        details_panel = ui_page.locator(".task-details")
        expect(details_panel).to_be_visible()
        
        # Modify description
        textarea = details_panel.locator("textarea")
        textarea.fill("New description")
        
        # Save button should be enabled
        save_btn = details_panel.locator("button:has-text('Save')")
        expect(save_btn).to_be_enabled()
        
        # Click save
        save_btn.click()
        ui_page.wait_for_timeout(500)
        
        # Save button should be disabled again
        expect(save_btn).not_to_be_enabled()

    def test_category_switching_smoke(self, ui_page):
        """Ensure switching categories doesn't crash the UI."""
        # Add a category
        cat_input = ui_page.locator("input[placeholder='New category']")
        cat_input.fill("SmokeTestCat")
        cat_input.press("Enter")
        
        ui_page.wait_for_selector("a.nav-link:has-text('SmokeTestCat')")
        
        # Switch to it
        ui_page.locator("a.nav-link:has-text('SmokeTestCat')").click()
        expect(ui_page.locator("h1.h2")).to_contain_text("SmokeTestCat")
        
        # Switch back
        ui_page.locator("a.nav-link:has-text('All Tasks')").click()
        expect(ui_page.locator("h1.h2")).to_contain_text("All Tasks")

    def test_smart_category_smoke(self, ui_page):
        """Ensure smart categories filter tasks and show the lightning icon."""
        # 1. Add a high priority task
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Crucial task !high")
        input_field.press("Enter")
        ui_page.wait_for_timeout(500)

        # 2. Add a normal task
        input_field.fill("Meh task")
        input_field.press("Enter")
        ui_page.wait_for_timeout(500)

        # 3. Create a smart category
        cat_input = ui_page.locator("input[placeholder='New category']")
        cat_input.fill("High Only [priority:high]")
        cat_input.press("Enter")
        ui_page.wait_for_timeout(500)

        # 4. Verify lightning icon is visible
        cat_link = ui_page.locator("a.nav-link:has-text('High Only')")
        expect(cat_link.locator("i.bi-lightning-fill")).to_be_visible()

        # 5. Click the smart category
        cat_link.click()
        ui_page.wait_for_timeout(500)

        # 6. Verify only the high priority task is visible
        expect(ui_page.locator(".task-item:has-text('Crucial task')")).to_be_visible()
        expect(ui_page.locator(".task-item:has-text('Meh task')")).to_be_hidden()

    def test_subtask_rendering_smoke(self, ui_page):
        """Ensure subtasks render correctly and don't break the list."""
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Parent task")
        input_field.press("Enter")
        ui_page.wait_for_timeout(500)
        
        task_item = ui_page.locator(".task-item:has-text('Parent task')")
        task_item.locator(".task-title").click() # Expand
        
        subtask_input = ui_page.locator("input[placeholder='Add subtask...']")
        subtask_input.fill("Subtask 1")
        subtask_input.press("Enter")
        ui_page.wait_for_timeout(500)
        
        # Check subtask in expanded view
        expect(ui_page.locator(".task-details .small:has-text('Subtask 1')")).to_be_visible()
        
        # Collapse it so compact view can show up
        task_item.locator(".task-title").click()
        ui_page.wait_for_timeout(300)
        
        # Turn on "Show Details"
        ui_page.locator("button:has-text('Show Details')").click()
        ui_page.wait_for_timeout(500)
        
        # The compact view should now show the subtask
        expect(ui_page.locator(".task-compact-details .small:has-text('Subtask 1')")).to_be_visible()

    def test_recurrence_stress_smoke(self, ui_page):
        """Rapidly complete recurring tasks to check for state corruption."""
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Rapid recurrence @today *daily")
        input_field.press("Enter")
        ui_page.wait_for_timeout(500)
        
        task_item = ui_page.locator(".task-item:has-text('Rapid recurrence')")
        
        for _ in range(5):
            checkbox = task_item.locator("input.toggle-completion")
            checkbox.click()
            # Wait for the re-render where it's uncompleted again
            ui_page.wait_for_selector(".task-item:has-text('Rapid recurrence') input.toggle-completion:not(:checked)")
            ui_page.wait_for_timeout(100)
        
        # UI should still be alive
        expect(ui_page.locator("h1.h2")).to_be_visible()
