# Save Button Dirty Tracking Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Disable the Save button in the task edit form until a field value has actually changed from what it was when the task was expanded.

**Architecture:** On expand, snapshot the 5 editable field values keyed by task ID. A reactive `isDirty(task)` method compares current values against the snapshot. The Save button's disabled state and color class are bound to `isDirty(task)`. Snapshot is refreshed after a successful save, and deleted on collapse.

**Tech Stack:** Alpine.js 3.14.3 (reactive frontend), Bootstrap 5.3.0 (btn-secondary / btn-success classes)

---

### Task 1: Add `taskSnapshots` state and helper methods to `app.js`

**Files:**
- Modify: `static/app.js:2-14` (data object) and after `toggleExpand` around line 431

**Step 1: Add `taskSnapshots: {}` to the Alpine data object**

In `static/app.js`, the `sharpei()` return object starts at line 2. Add `taskSnapshots: {}` after `showDetails: false,` on line 14:

```js
        showDetails: false,
        taskSnapshots: {},
```

**Step 2: Add `_snapshotFields` and `isDirty` methods**

Add these two methods immediately after the closing brace of `toggleExpand` (currently ends around line 431). Insert after the `},` that closes `toggleExpand`:

```js
        _snapshotFields(task) {
            return {
                description: task.description,
                due_date_str: task.due_date_str,
                priority: task.priority,
                category_id: task.category_id,
                hashtags: task.hashtags,
            };
        },

        isDirty(task) {
            const snap = this.taskSnapshots[task.id];
            if (!snap) return false;
            return snap.description !== task.description
                || snap.due_date_str !== task.due_date_str
                || snap.priority !== task.priority
                || snap.category_id !== task.category_id
                || snap.hashtags !== task.hashtags;
        },
```

**Step 3: Verify the file is syntactically valid**

Open the browser dev tools console after loading the app and confirm no JS errors. (No automated JS tests exist in this project.)

**Step 4: Commit**

```bash
git add static/app.js
git commit -m "feat: add taskSnapshots state and isDirty helper"
```

---

### Task 2: Update `toggleExpand` to capture and clear snapshots

**Files:**
- Modify: `static/app.js:425-431`

**Step 1: Replace `toggleExpand` with snapshot-aware version**

Current code (lines 425-431):
```js
        toggleExpand(task) {
            if (this.expandedTasks.includes(task.id)) {
                this.expandedTasks = this.expandedTasks.filter(id => id !== task.id);
            } else {
                this.expandedTasks.push(task.id);
            }
        },
```

Replace with:
```js
        toggleExpand(task) {
            if (this.expandedTasks.includes(task.id)) {
                this.expandedTasks = this.expandedTasks.filter(id => id !== task.id);
                delete this.taskSnapshots[task.id];
            } else {
                this.expandedTasks.push(task.id);
                this.taskSnapshots[task.id] = this._snapshotFields(task);
            }
        },
```

**Step 2: Manual verification**

Start the dev server (`uvicorn app.main:app --reload` from the project root). Open the app. Expand a task — the Save button should appear grayed out (Bootstrap `btn-secondary`). Collapse and re-expand — still grayed out. No JS console errors.

**Step 3: Commit**

```bash
git add static/app.js
git commit -m "feat: snapshot task fields on expand, clear on collapse"
```

---

### Task 3: Refresh snapshot after successful save

**Files:**
- Modify: `static/app.js:363-387`

**Step 1: Update the `.then` handler in `saveTask`**

Current success handler (lines 382-385):
```js
            .then(res => {
                if (!res.ok) throw new Error('Failed to save task');
                this.fetchTasks();
            })
```

Replace with:
```js
            .then(res => {
                if (!res.ok) throw new Error('Failed to save task');
                if (this.taskSnapshots[task.id]) {
                    this.taskSnapshots[task.id] = this._snapshotFields(task);
                }
                this.fetchTasks();
            })
```

This re-arms the snapshot after saving so the button goes back to disabled. The `if` guard ensures this only runs when the task is currently expanded — it has no effect when `saveTask` is called from `toggleTask` or drag-reorder.

**Step 2: Manual verification**

Expand a task. Change a field — Save button should activate (green). Click Save. After the page refreshes, the Save button should be grayed out again. No JS console errors.

**Step 3: Commit**

```bash
git add static/app.js
git commit -m "feat: refresh snapshot after successful save"
```

---

### Task 4: Bind Save button state to `isDirty` in `index.html`

**Files:**
- Modify: `templates/index.html:188`

**Step 1: Replace the Save button**

Current line 188:
```html
                                                    <button class="btn btn-sm btn-success" @click="saveTask(task)">Save</button>
```

Replace with:
```html
                                                    <button class="btn btn-sm" :class="isDirty(task) ? 'btn-success' : 'btn-secondary'" :disabled="!isDirty(task)" @click="saveTask(task)">Save</button>
```

**Step 2: Manual verification — full flow**

1. Load the app. Expand any task → Save button is gray and unclickable.
2. Change the description → Save button turns green and is clickable.
3. Change the description back to original text → Save button turns gray again.
4. Change priority → Save button turns green.
5. Click Save → page refreshes, Save button is gray again.
6. Collapse the task and re-expand → Save button is gray.

**Step 3: Commit**

```bash
git add templates/index.html
git commit -m "feat: disable Save button until task fields are dirty

Closes #3"
```

---

### Task 5: Final verification

**Step 1: Run the backend tests to confirm no regressions**

```bash
cd /Users/bnaylor/src/sharpei && python -m pytest tests/ -v
```

Expected: all tests pass (these are API tests; our changes are frontend-only).

**Step 2: Smoke test edge cases manually**

- Expand two tasks simultaneously — each Save button tracks its own dirty state independently.
- Toggle a task's completion checkbox (calls `saveTask` internally) — no snapshot side effects.
- Drag a task to a new priority group (also calls `saveTask`) — no snapshot side effects.
