# Task Dependencies & Blockers

Sharpei allows you to create dependencies between tasks. If Task B depends on Task A, Task B will be marked as **Blocked** until Task A is completed.

## Finding Task IDs

To link tasks, you need to know their unique **ID**. 

-   Every task has an ID displayed with a `#` prefix in its row (e.g., `#123`), located next to the trash icon.
-   These IDs are automatically assigned by the database and never change.

## Setting a Dependency

1.  Find the **ID** of the task that is blocking you (the "Blocker").
2.  Expand the task that is currently blocked.
3.  In the **Blocker IDs** field, type the ID of the blocking task.
4.  Click **Save**.

### Multiple Blockers
You can list multiple blockers by separating their IDs with commas (e.g., `101, 102, 105`).

## Visual Indicators

### Blocked Badge
When a task has one or more incomplete dependencies, a red **Blocked** badge appears next to its title in the list view.

### Compact Details
If you have "Show Details" enabled, a warning message will appear in the compact view: `⚠ This task is blocked.`

## Behavior

-   **Automatic Refresh**: As soon as you mark a blocker task as completed, all tasks depending on it will automatically have their "Blocked" status re-evaluated.
-   **Recursive Blocking**: If Task C depends on Task B, and Task B is blocked by Task A, Task C will remain blocked until *both* are resolved.
