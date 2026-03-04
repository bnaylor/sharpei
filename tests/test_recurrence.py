#!/usr/bin/env python3
"""Tests for task recurrence functionality in Sharpei."""
import pytest
from playwright.sync_api import expect
from datetime import datetime, timedelta

def test_daily_recurrence(ui_page):
    """Test that a daily recurring task moves its due date forward by 1 day."""
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    tomorrow_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")

    # 1. Create a daily task due today
    input_field = ui_page.locator("input[placeholder='Add a task...']")
    input_field.fill(f"Daily task @today *daily")
    input_field.press("Enter")
    
    ui_page.wait_for_selector(".task-item:has-text('Daily task')")
    task_item = ui_page.locator(".task-item:has-text('Daily task')")
    
    # Verify it shows "Today" and the repeat icon
    expect(task_item.locator(".due-date")).to_contain_text("Today")
    expect(task_item.locator(".bi-repeat")).to_be_visible()
    
    # 2. Complete the task
    checkbox = task_item.locator("input.toggle-completion")
    checkbox.click()
    
    # Wait for the UI to refresh (the backend should reset completion and move date)
    ui_page.wait_for_timeout(1000)
    
    # 3. Verify it's now due tomorrow and NOT completed
    expect(task_item.locator(".due-date")).to_contain_text("Tomorrow")
    expect(checkbox).not_to_be_checked()
    expect(task_item.locator(".task-title")).not_to_have_class("text-decoration-line-through")

def test_custom_days_recurrence(ui_page):
    """Test that a task with custom day recurrence (e.g., *3d) moves correctly."""
    today = datetime.now()
    # 3 days from now
    three_days_later = today + timedelta(days=3)
    # 6 days from now
    six_days_later = today + timedelta(days=6)
    
    input_field = ui_page.locator("input[placeholder='Add a task...']")
    input_field.fill(f"Three day task @today *3d")
    input_field.press("Enter")
    
    ui_page.wait_for_selector(".task-item:has-text('Three day task')")
    task_item = ui_page.locator(".task-item:has-text('Three day task')")
    
    # Complete it
    task_item.locator("input.toggle-completion").click()
    ui_page.wait_for_timeout(1000)
    
    # Should now be due in 3 days (displaying the date)
    expect(task_item.locator(".due-date")).to_contain_text(three_days_later.strftime("%-m/%-d/%Y"))
    
    # Complete it again
    task_item.locator("input.toggle-completion").click()
    ui_page.wait_for_timeout(1000)
    
    # Should now be due in 6 days
    expect(task_item.locator(".due-date")).to_contain_text(six_days_later.strftime("%-m/%-d/%Y"))
