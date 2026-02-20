# Design: Playwright Tests for Save Button Dirty Tracking

**Date:** 2026-02-20
**Follow-up to:** `docs/plans/2026-02-20-save-button-dirty-tracking-design.md`

## Goal

Add Playwright tests to `TestTaskExpansion` in `tests/test_ui.py` covering the 5 key behaviors of the dirty tracking feature.

## Test Cases

### 1. `test_save_button_disabled_on_expand`
Create a task, expand it. Assert the Save button is disabled and has class `btn-secondary`.

### 2. `test_save_button_enabled_after_change`
Create a task, expand it, fill the description textarea. Assert the Save button is enabled and has class `btn-success`.

### 3. `test_save_button_disabled_after_save`
Create a task, expand it, change the description, click Save, wait for page reload. Assert the Save button is disabled again.

### 4. `test_save_button_disabled_after_collapse_reexpand`
Create a task, expand it, change the description, collapse without saving, re-expand. Assert the Save button is disabled.

### 5. `test_save_button_disabled_after_reverting_change`
Create a task, expand it, type something in the description, then clear it back to empty. Assert the Save button is disabled.

## Assertion Pattern

```python
save_btn = ui_page.locator(".task-details button:has-text('Save')")
expect(save_btn).to_be_disabled()
expect(save_btn).to_have_class(re.compile(r"btn-secondary"))
```

Both the functional state (`:disabled`) and visual state (`btn-secondary`/`btn-success`) are verified.

## Placement

All 5 tests go in `TestTaskExpansion` in `tests/test_ui.py`. Each test creates its own task for isolation, consistent with the existing test pattern.
