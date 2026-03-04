# Search & Smart Filters

Sharpei supports an advanced search syntax that allows you to filter tasks by status, priority, due dates, and more. You can also save these searches as **Smart Categories**.

## Search Syntax

Enter these tokens into the main search bar to filter your tasks. Tokens can be combined with regular text search.

### Status Filters (`is:`)

| Token | Meaning |
|-------|---------|
| `is:overdue` | Tasks where the due date has passed and are not completed |
| `is:completed` | Tasks that are marked as done |
| `is:pending` | Tasks that are NOT marked as done |
| `is:archived` | Tasks that have been archived |

### Priority Filters (`priority:` or `p:`)

| Token | Meaning |
|-------|---------|
| `priority:high` | High priority (P0) tasks |
| `priority:normal` | Normal priority (P1) tasks |
| `priority:low` | Low priority (P2) tasks |
| `p:0`, `p:1`, `p:2` | Shorthand for High, Normal, and Low |

### Property Filters (`has:`)

| Token | Meaning |
|-------|---------|
| `has:due` | Tasks that have any due date assigned |
| `has:tags` | Tasks that have one or more hashtags |
| `has:desc` | Tasks that have a description |

### Category Filter (`category:`)

Filter by category name directly:
`category:work`

## Combined Examples

- `is:overdue priority:high` - High priority tasks that are past due.
- `report has:tags` - Any task containing "report" that also has tags.
- `is:completed category:personal` - All completed tasks in the Personal category.

---

## Smart Categories

Smart Categories are persistent filters that appear in your sidebar. Instead of containing a static list of tasks, they execute a search query every time you click them.

### Creating a Smart Category

In the "New category" input field in the sidebar, use the following syntax:
`Category Name [query]`

**Examples:**
- `Overdue [is:overdue]`
- `Hotlist [priority:high is:pending]`
- `Needs Docs [has:tags !is:completed]`

### Visual Indicators

Smart Categories are marked with a **lightning bolt icon** (⚡) in the sidebar to distinguish them from regular categories.

### Behavior

When you click a Smart Category:
1. The search query is automatically applied.
2. The task list refreshes to show the matching results.
3. Unlike regular categories, adding a new task while a Smart Category is selected will **not** automatically assign it to that category (it will use the default category instead).
