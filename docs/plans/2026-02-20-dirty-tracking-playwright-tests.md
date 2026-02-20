# Dirty Tracking Playwright Tests Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 5 Playwright tests to `TestTaskExpansion` covering the Save button dirty tracking behavior.

**Architecture:** All tests go in `tests/test_ui.py` inside `TestTaskExpansion`. Each test creates its own task for isolation. The feature is already implemented so tests should pass immediately — these are regression tests, not TDD. Each test verifies both the functional state (`:disabled` attribute) and visual state (`btn-secondary`/`btn-success` class) of the Save button.

**Tech Stack:** pytest, Playwright (sync API), `playwright.sync_api.expect` — same as existing tests. App uses Alpine.js; Alpine reactive updates are synchronous on DOM events so no extra waits are needed for button state changes after field edits.

---

### Task 1: Tests for initial disabled state and enabled-after-change

**Files:**
- Modify: `tests/test_ui.py` — `TestTaskExpansion` class (currently ends around line 207)

**Step 1: Add the two tests to `TestTaskExpansion`**

Append these two methods inside the `TestTaskExpansion` class, after `test_change_task_priority`:

```python
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
```

**Step 2: Run the two new tests to verify they pass**

```bash
cd /Users/bnaylor/src/sharpei && python -m pytest tests/test_ui.py::TestTaskExpansion::test_save_button_disabled_on_expand tests/test_ui.py::TestTaskExpansion::test_save_button_enabled_after_change -v
```

Expected: both PASS.

**Step 3: Commit**

```bash
git add tests/test_ui.py
git commit -m "test: save button disabled on expand, enabled after change"
```

---

### Task 2: Tests for post-save, collapse/reexpand, and revert behaviors

**Files:**
- Modify: `tests/test_ui.py` — `TestTaskExpansion` class (after the tests added in Task 1)

**Step 1: Add three more tests to `TestTaskExpansion`**

Append these three methods inside `TestTaskExpansion`, after the Task 1 tests:

```python
    def test_save_button_disabled_after_save(self, ui_page):
        """Test that Save button goes back to disabled after a successful save."""
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Dirty tracking task C")
        input_field.press("Enter")
        ui_page.wait_for_selector(".task-title:has-text('Dirty tracking task C')")

        ui_page.locator(".task-title:has-text('Dirty tracking task C')").click()
        ui_page.wait_for_selector(".task-details")

        textarea = ui_page.locator(".task-details textarea")
        textarea.fill("Description to save")

        save_btn = ui_page.locator(".task-details button:has-text('Save')")
        save_btn.click()
        ui_page.wait_for_timeout(500)

        expect(save_btn).to_be_disabled()
        expect(save_btn).to_have_class(re.compile(r"btn-secondary"))

    def test_save_button_disabled_after_collapse_reexpand(self, ui_page):
        """Test that Save button is disabled after collapsing and re-expanding an unsaved task."""
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Dirty tracking task D")
        input_field.press("Enter")
        ui_page.wait_for_selector(".task-title:has-text('Dirty tracking task D')")

        # Expand
        ui_page.locator(".task-title:has-text('Dirty tracking task D')").click()
        ui_page.wait_for_selector(".task-details")

        # Make a change (but don't save)
        textarea = ui_page.locator(".task-details textarea")
        textarea.fill("Unsaved change")

        # Collapse
        ui_page.locator(".task-title:has-text('Dirty tracking task D')").click()
        ui_page.wait_for_selector(".task-details", state="hidden")

        # Re-expand
        ui_page.locator(".task-title:has-text('Dirty tracking task D')").click()
        ui_page.wait_for_selector(".task-details")

        save_btn = ui_page.locator(".task-details button:has-text('Save')")
        expect(save_btn).to_be_disabled()
        expect(save_btn).to_have_class(re.compile(r"btn-secondary"))

    def test_save_button_disabled_after_reverting_change(self, ui_page):
        """Test that Save button goes back to disabled when a change is reverted to the original value."""
        input_field = ui_page.locator("input[placeholder='Add a task...']")
        input_field.fill("Dirty tracking task E")
        input_field.press("Enter")
        ui_page.wait_for_selector(".task-title:has-text('Dirty tracking task E')")

        ui_page.locator(".task-title:has-text('Dirty tracking task E')").click()
        ui_page.wait_for_selector(".task-details")

        textarea = ui_page.locator(".task-details textarea")

        # Change the description
        textarea.fill("Temporary change")
        save_btn = ui_page.locator(".task-details button:has-text('Save')")
        expect(save_btn).to_be_enabled()

        # Revert to original (empty string — new tasks have no description)
        textarea.fill("")
        expect(save_btn).to_be_disabled()
        expect(save_btn).to_have_class(re.compile(r"btn-secondary"))
```

**Step 2: Run the three new tests**

```bash
cd /Users/bnaylor/src/sharpei && python -m pytest tests/test_ui.py::TestTaskExpansion::test_save_button_disabled_after_save tests/test_ui.py::TestTaskExpansion::test_save_button_disabled_after_collapse_reexpand tests/test_ui.py::TestTaskExpansion::test_save_button_disabled_after_reverting_change -v
```

Expected: all three PASS.

**Step 3: Run the full test suite to confirm no regressions**

```bash
cd /Users/bnaylor/src/sharpei && python -m pytest tests/ -v
```

Expected: all tests pass (87 existing + 5 new = 92 total).

**Step 4: Commit**

```bash
git add tests/test_ui.py
git commit -m "test: save button disabled after save, collapse/reexpand, and revert"
```
