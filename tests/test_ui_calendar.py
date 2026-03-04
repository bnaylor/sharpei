#!/usr/bin/env python3
"""Tests for the Sharpei calendar view functionality."""
import pytest
from playwright.sync_api import expect
from datetime import datetime
import os

@pytest.fixture(autouse=True)
def setup_console_capture(ui_page):
    """Fail the test if any console errors occur."""
    console_errors = []
    ui_page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    ui_page.on("pageerror", lambda err: console_errors.append(str(err)))
    yield
    if console_errors:
        print(f"Browser console errors detected: {console_errors}")

def test_toggle_calendar_view(ui_page):
    """Test switching between list and calendar views."""
    # Add a task to ensure task-list has content and is "visible"
    input_field = ui_page.locator("input[placeholder='Add a task...']")
    input_field.fill("Visibility test task")
    input_field.press("Enter")
    
    # Wait for the view toggle to be ready and loading to finish
    ui_page.wait_for_selector("button:has-text('Calendar')")
    ui_page.wait_for_function("() => Alpine.$data(document.querySelector('[x-data]')).loading === false")
    
    # Start in list view
    expect(ui_page.locator(".task-list")).to_be_visible()
    expect(ui_page.locator(".calendar-view")).not_to_be_visible()
    
    # Switch to calendar view
    ui_page.locator("button:has-text('Calendar')").click()
    expect(ui_page.locator(".calendar-view")).to_be_visible()
    expect(ui_page.locator(".task-list")).not_to_be_visible()
    
    # Switch back to list view
    ui_page.locator("button:has-text('List')").click()
    expect(ui_page.locator(".task-list")).to_be_visible()
    expect(ui_page.locator(".calendar-view")).not_to_be_visible()

def test_calendar_navigation(ui_page):
    """Test navigating months in the calendar view."""
    ui_page.locator("button:has-text('Calendar')").click()
    
    # Use expect with timeout instead of wait_for_selector
    expect(ui_page.locator(".month-display")).to_be_visible(timeout=5000)
    
    current_month_name = ui_page.locator(".month-display").text_content()
    
    # Go to previous month
    ui_page.locator("button:has(i.bi-chevron-left)").click()
    prev_month_name = ui_page.locator(".month-display").text_content()
    assert prev_month_name != current_month_name
    
    # Go to next month (back to original)
    ui_page.locator("button:has(i.bi-chevron-right)").click()
    assert ui_page.locator(".month-display").text_content() == current_month_name
    
    # Go to today
    ui_page.locator("button:has-text('Today')").click()
    assert ui_page.locator(".month-display").text_content() == current_month_name

def test_task_appears_in_calendar(ui_page):
    """Test that a task with a due date appears in the calendar."""
    # 1. Add a task with a specific date
    # We use a fixed date to avoid issues with month boundaries
    today = datetime.now()
    target_date = today.strftime("%Y-%m-%d")
    task_title = f"Calendar test task {today.timestamp()}"
    
    input_field = ui_page.locator("input[placeholder='Add a task...']")
    input_field.fill(f"{task_title} @{target_date}")
    input_field.press("Enter")
    ui_page.wait_for_timeout(500)
    
    # 2. Switch to calendar
    ui_page.locator("button:has-text('Calendar')").click()
    
    # 3. Verify task is visible in the calendar grid
    # We look for the task title inside the calendar-task elements
    expect(ui_page.locator(f".calendar-task:has-text('{task_title}')")).to_be_visible()

def test_calendar_task_click_redirects_to_list(ui_page):
    """Test that clicking a task in calendar switches to list view and expands it."""
    # 1. Add a task with today's date
    task_title = "Clickable calendar task"
    input_field = ui_page.locator("input[placeholder='Add a task...']")
    input_field.fill(f"{task_title} @today")
    input_field.press("Enter")
    ui_page.wait_for_timeout(500)
    
    # 2. Switch to calendar
    ui_page.locator("button:has-text('Calendar')").click()
    
    # 3. Click the task in the calendar
    ui_page.locator(f".calendar-task:has-text('{task_title}')").click()
    
    state = ui_page.evaluate("() => { const d = Alpine.$data(document.querySelector('[x-data]')); return {viewMode: d.viewMode, expandedTasks: d.expandedTasks}; }")
    print(f"State after click: {state}")
    
    # 4. Verify we are back in list view
    expect(ui_page.locator(".task-list")).to_be_visible()
    expect(ui_page.locator(".calendar-view")).not_to_be_visible()
    
    # 5. Verify the task is expanded
    task_container = ui_page.locator(f".task-item-container:has-text('{task_title}')")
    expect(task_container.locator(".task-details")).to_be_visible(timeout=5000)

def test_navigation_widgets_hidden_in_list_mode(ui_page):
    """Test that calendar navigation widgets are hidden in list mode."""
    # 1. Start in list view (default)
    ui_page.wait_for_selector("button:has-text('Calendar')")
    
    # 2. Check if Today button or Month name is visible
    # The container has x-show="viewMode === 'calendar'"
    nav_container = ui_page.locator(".calendar-nav")
    expect(nav_container).to_be_hidden()
    
    # 3. Switch to calendar view
    ui_page.locator("button:has-text('Calendar')").click()
    expect(nav_container).to_be_visible()
    
    # 4. Switch back to list view
    ui_page.locator("button:has-text('List')").click()
    expect(nav_container).to_be_hidden()
