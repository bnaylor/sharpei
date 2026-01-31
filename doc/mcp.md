# Sharpei MCP Server

Sharpei includes a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that allows AI assistants to interact with your tasks programmatically. This enables AI tools like Claude to read, create, update, and manage your TODO items directly.

## Setup

### Prerequisites

Ensure the MCP package is installed:

```bash
source venv/bin/activate
pip install mcp
```

### Configuration

Add the following to your MCP client's configuration file:

**For Claude Code** (`~/.claude/claude_code_config.json`):

```json
{
  "mcpServers": {
    "sharpei": {
      "command": "python",
      "args": ["/path/to/sharpei/mcp_server.py"],
      "cwd": "/path/to/sharpei"
    }
  }
}
```

**For Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "sharpei": {
      "command": "/path/to/sharpei/venv/bin/python",
      "args": ["/path/to/sharpei/mcp_server.py"],
      "cwd": "/path/to/sharpei"
    }
  }
}
```

Replace `/path/to/sharpei` with the actual path to your Sharpei installation.

## Available Tools

### Category Management

#### `list_categories()`
List all task categories.

**Returns:** Array of categories with `id` and `name`.

#### `create_category(name)`
Create a new category.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Category name |

**Returns:** The created category with its ID.

---

### Task Management

#### `list_tasks(category_id, search, include_archived, include_subtasks)`
List tasks with optional filtering.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `category_id` | int | No | null | Filter by category |
| `search` | string | No | null | Search in title, description, and hashtags |
| `include_archived` | bool | No | false | Include archived tasks |
| `include_subtasks` | bool | No | true | Include subtask details |

**Returns:** Array of tasks ordered by priority, then position.

#### `get_task(task_id)`
Get a specific task with full details including subtasks.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | int | Yes | Task ID |

**Returns:** Task object with all fields and nested subtasks.

#### `create_task(title, description, due_date, priority, hashtags, category_id, parent_id)`
Create a new task.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `title` | string | Yes | - | Task title |
| `description` | string | No | null | Markdown description |
| `due_date` | string | No | null | ISO format: `YYYY-MM-DD` |
| `priority` | int | No | 1 | 0=High, 1=Normal, 2=Low |
| `hashtags` | string | No | null | Space/comma separated tags |
| `category_id` | int | No | null | Category to assign |
| `parent_id` | int | No | null | Parent task (for subtasks) |

**Returns:** The created task with its ID.

#### `update_task(task_id, ...)`
Update an existing task. Only provided fields are updated.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | int | Yes | Task ID to update |
| `title` | string | No | New title |
| `description` | string | No | New description |
| `due_date` | string | No | New due date (empty string to clear) |
| `priority` | int | No | New priority |
| `hashtags` | string | No | New hashtags |
| `category_id` | int | No | New category (-1 to remove) |
| `completed` | bool | No | Completion status |
| `archived` | bool | No | Archive status |

**Returns:** The updated task.

#### `delete_task(task_id)`
Delete a task and all its subtasks.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | int | Yes | Task ID to delete |

**Returns:** Confirmation message.

---

### Task Actions

#### `complete_task(task_id, completed)`
Mark a task as completed or not completed. Uncompleting a task automatically unarchives it.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `task_id` | int | Yes | - | Task ID |
| `completed` | bool | No | true | Completion status |

**Returns:** The updated task.

#### `archive_completed(category_id)`
Archive all completed tasks, removing them from the default task list.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category_id` | int | No | Only archive in this category |

**Returns:** Number of tasks archived.

#### `add_subtask(parent_id, title, description)`
Add a subtask to an existing task. Subtasks inherit the parent's priority and category.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `parent_id` | int | Yes | Parent task ID |
| `title` | string | Yes | Subtask title |
| `description` | string | No | Subtask description |

**Returns:** The created subtask.

---

## Task Object Structure

```json
{
  "id": 1,
  "title": "Example task",
  "description": "Markdown description",
  "due_date": "2025-02-15T12:00:00",
  "priority": 1,
  "priority_label": "Normal",
  "hashtags": "#work #urgent",
  "completed": false,
  "archived": false,
  "category_id": 1,
  "parent_id": null,
  "subtasks": []
}
```

## Priority Levels

| Value | Label | UI Color |
|-------|-------|----------|
| 0 | High | Red |
| 1 | Normal | Green |
| 2 | Low | Blue |

## Example Usage

Here are some example prompts you can use with an AI assistant once the MCP server is configured:

- "Show me all my high-priority tasks"
- "Create a task to review the quarterly report, due Friday, high priority"
- "Mark the grocery shopping task as complete"
- "Add a subtask 'Buy milk' to my shopping list task"
- "Archive all my completed tasks"
- "Search for tasks tagged with #work"
- "What tasks are overdue?"

## Testing

Run the test suite to verify the MCP server functionality:

```bash
source venv/bin/activate
python -m pytest tests/test_mcp_server.py -v
```
