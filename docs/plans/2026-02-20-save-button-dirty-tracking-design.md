# Design: Save Button Dirty Tracking

**Date:** 2026-02-20
**Issue:** #3 — UX: Disable 'Save' button for item edits until something changes

## Problem

The Save button in the task edit form is always active, making it easy to expand a task, make no changes, and collapse without saving — or conversely, to make changes and forget to save.

## Solution

Track a snapshot of each task's editable field values at expand time. Disable the Save button until at least one field differs from its snapshot value.

## Tracked Fields

- `description`
- `due_date_str`
- `priority`
- `category_id`
- `hashtags`

Title is not editable in the UI and is excluded.

## Implementation

### State (`static/app.js`)

Add `taskSnapshots: {}` to the Alpine data object — a plain object keyed by task ID.

### Snapshot Lifecycle

In `toggleExpand(task)`:
- On **expand**: capture the 5 tracked fields into `taskSnapshots[task.id]`
- On **collapse**: `delete taskSnapshots[task.id]`

### Dirty Check

Add `isDirty(task)` method:
- Returns `false` if no snapshot exists (safe default)
- Returns `true` if any tracked field differs from its snapshot value

### Save Button (`templates/index.html`)

```html
<button
  class="btn btn-sm"
  :class="isDirty(task) ? 'btn-success' : 'btn-secondary'"
  :disabled="!isDirty(task)"
  @click="saveTask(task)">Save</button>
```

- Grayed out (`btn-secondary`) when unmodified
- Active green (`btn-success`) when dirty

## Scope

- `static/app.js` — snapshot state, `isDirty` method, `toggleExpand` changes
- `templates/index.html` — Save button attributes

No backend changes required.
