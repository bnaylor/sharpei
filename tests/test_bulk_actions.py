#!/usr/bin/env python3
"""Tests for Sharpei bulk actions."""
import pytest
from playwright.sync_api import expect

def test_multi_select_and_bulk_delete(ui_page):
    """Test selecting multiple tasks and deleting them."""
    # 1. Add some tasks
    input_field = ui_page.locator("input[placeholder='Add a task...']")
    for i in range(3):
        input_field.fill(f"Bulk task {i}")
        input_field.press("Enter")
        ui_page.wait_for_timeout(200)

    # 2. Enable Bulk Mode
    ui_page.locator("button:has-text('Bulk Edit')").click()

    # 3. Select two tasks
    ui_page.locator(".task-item:has-text('Bulk task 0')").locator("input.select-task").click()
    ui_page.locator(".task-item:has-text('Bulk task 1')").locator("input.select-task").click()

    # 4. Bulk Action Bar should be visible
    bulk_bar = ui_page.locator(".bulk-action-bar")
    expect(bulk_bar).to_be_visible()
    expect(bulk_bar).to_contain_text("2 selected")

    # 5. Bulk Delete
    ui_page.on("dialog", lambda dialog: dialog.accept()) # Confirm delete
    bulk_bar.locator("button:has-text('Delete')").click()
    ui_page.wait_for_timeout(500)

    # 6. Verify tasks are gone
    expect(ui_page.locator(".task-item:has-text('Bulk task 0')")).to_be_hidden()
    expect(ui_page.locator(".task-item:has-text('Bulk task 1')")).to_be_hidden()
    expect(ui_page.locator(".task-item:has-text('Bulk task 2')")).to_be_visible()
    expect(bulk_bar).to_be_hidden()

def test_select_all_toggle(ui_page):
    """Test the select all button in the toolbar."""
    # 1. Add some tasks
    input_field = ui_page.locator("input[placeholder='Add a task...']")
    for i in range(3):
        input_field.fill(f"Select all task {i}")
        input_field.press("Enter")
        ui_page.wait_for_timeout(200)

    # 2. Enable Bulk Mode
    ui_page.locator("button:has-text('Bulk Edit')").click()

    # 3. Click Select All
    ui_page.locator("button[title='Select all visible']").click()
    
    # 4. Verify all selected
    bulk_bar = ui_page.locator(".bulk-action-bar")
    expect(bulk_bar).to_contain_text("3 selected")
    
    # 5. Click Deselect All
    ui_page.locator("button[title='Deselect all']").click()
    expect(bulk_bar).to_be_hidden()

def test_bulk_priority_change(ui_page):
    """Test bulk changing priority of tasks."""
    # 1. Add two normal priority tasks
    input_field = ui_page.locator("input[placeholder='Add a task...']")
    input_field.fill("Priority task 1")
    input_field.press("Enter")
    ui_page.wait_for_selector(".task-item:has-text('Priority task 1')")
    
    input_field.fill("Priority task 2")
    input_field.press("Enter")
    ui_page.wait_for_selector(".task-item:has-text('Priority task 2')")
    
    # 2. Enable Bulk Mode
    ui_page.locator("button:has-text('Bulk Edit')").click()

    # 3. Select them
    ui_page.locator(".task-item:has-text('Priority task 1')").locator("input.select-task").click()
    ui_page.locator(".task-item:has-text('Priority task 2')").locator("input.select-task").click()

    # 4. Change to High Priority
    bulk_bar = ui_page.locator(".bulk-action-bar")
    bulk_bar.locator("button:has-text('Priority')").click()
    
    # Target the specific dropdown item inside the bulk bar
    high_option = bulk_bar.locator(".dropdown-item:has-text('High')")
    expect(high_option).to_be_visible()
    high_option.click()
    ui_page.wait_for_timeout(500)

    # 5. Verify they are in High Priority group
    high_group = ui_page.locator(".priority-group:has-text('High Priority')")
    expect(high_group.locator(".task-item:has-text('Priority task 1')")).to_be_visible()
    expect(high_group.locator(".task-item:has-text('Priority task 2')")).to_be_visible()

def test_shift_click_range_selection(ui_page):
    """Test Shift+Click to select a range of tasks."""
    # 1. Add 5 tasks
    input_field = ui_page.locator("input[placeholder='Add a task...']")
    for i in range(5):
        input_field.fill(f"Range task {i}")
        input_field.press("Enter")
        ui_page.wait_for_timeout(100)

    # 2. Enable Bulk Mode
    ui_page.locator("button:has-text('Bulk Edit')").click()

    # 3. Click first task
    ui_page.locator(".task-item:has-text('Range task 0')").locator("input.select-task").click()
    
    # 4. Shift+Click fifth task
    ui_page.locator(".task-item:has-text('Range task 4')").locator("input.select-task").click(modifiers=["Shift"])
    
    # 5. Verify all 5 are selected
    bulk_bar = ui_page.locator(".bulk-action-bar")
    expect(bulk_bar).to_contain_text("5 selected")
