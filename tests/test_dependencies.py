#!/usr/bin/env python3
"""Tests for Sharpei task dependencies (blockers)."""
import pytest
from playwright.sync_api import expect

def test_task_blocking_indicator(ui_page):
    """Test that a task shows as blocked if it has an incomplete dependency."""
    # 1. Add two tasks
    input_field = ui_page.locator("input[placeholder='Add a task...']")
    input_field.fill("Blocker task")
    input_field.press("Enter")
    ui_page.wait_for_selector(".task-item:has-text('Blocker task')")
    
    input_field.fill("Blocked task")
    input_field.press("Enter")
    ui_page.wait_for_selector(".task-item:has-text('Blocked task')")
    
    # 2. Get ID of blocker task from DOM
    blocker_id = ui_page.locator(".task-item-container:has-text('Blocker task')").get_attribute("data-id")
    
    # 3. Expand "Blocked task" and add blocker ID
    blocked_item = ui_page.locator(".task-item:has-text('Blocked task')")
    blocked_item.locator(".task-title").click()
    
    details = ui_page.locator(".task-details:visible")
    blocker_input = details.locator("input[placeholder='Blocker IDs']")
    blocker_input.fill(blocker_id)
    details.locator("button:has-text('Save')").click()
    ui_page.wait_for_timeout(500)
    
    # 4. Verify "Blocked" badge appears
    expect(blocked_item.locator(".badge:has-text('Blocked')")).to_be_visible()
    
    # 5. Complete blocker task
    ui_page.locator(".task-item:has-text('Blocker task')").locator("input.toggle-completion").click()
    ui_page.wait_for_timeout(500)
    
    # 6. Verify "Blocked" badge disappears
    expect(blocked_item.locator(".badge:has-text('Blocked')")).to_be_hidden()

def test_compact_view_blocking_indicator(ui_page):
    """Test that blocked status shows in compact view."""
    # 1. Add tasks and setup dependency
    input_field = ui_page.locator("input[placeholder='Add a task...']")
    input_field.fill("Task A")
    input_field.press("Enter")
    ui_page.wait_for_selector(".task-item:has-text('Task A')")
    
    input_field.fill("Task B")
    input_field.press("Enter")
    ui_page.wait_for_selector(".task-item:has-text('Task B')")
    
    id_a = ui_page.locator(".task-item-container:has-text('Task A')").get_attribute("data-id")
    
    # Set Task B blocked by Task A
    ui_page.locator(".task-item:has-text('Task B')").locator(".task-title").click()
    details = ui_page.locator(".task-details:visible")
    details.locator("input[placeholder='Blocker IDs']").fill(id_a)
    details.locator("button:has-text('Save')").click()
    ui_page.wait_for_timeout(500)
    
    # Collapse
    ui_page.locator(".task-item:has-text('Task B')").locator(".task-title").click()
    
    # 2. Enable "Show Details"
    ui_page.locator("button:has-text('Show Details')").click()
    ui_page.wait_for_timeout(500)
    
    # 3. Verify blocked message in compact details for Task B
    task_b_container = ui_page.locator(".task-item-container:has-text('Task B')")
    expect(task_b_container.locator(".task-compact-details:has-text('This task is blocked')")).to_be_visible()
    
    # Also verify Task A is NOT blocked
    task_a_container = ui_page.locator(".task-item-container:has-text('Task A')")
    expect(task_a_container.locator(".task-compact-details:has-text('This task is blocked')")).to_be_hidden()
