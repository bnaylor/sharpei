# Sharpei

A focused, local-first TODO application inspired by [MyTinyTodo](https://www.mytinytodo.net/).

Sharpei runs entirely on your machine with no cloud dependencies, stores data in SQLite for easy AI/agent access, and provides a clean, responsive UI for managing tasks, and an MCP server for direct AI agent manipulation.

![Sharpei screenshot](assets/sharpei_screenshot.png?raw=true)

## Features

- **Local-first** - Runs on localhost, no internet required
- **SQLite storage** - Simple, portable database that AI tools can read
- **Categories** - Organize tasks into projects or areas
- **Priority levels** - High (red), Normal (green), Low (blue)
- **Markdown notes** - Capture details about your tasks in markdown syntax
- **Subtasks** - Break down tasks into smaller items
- **Hashtags** - Tag tasks for easy filtering
- **Due dates** - With smart display (Today, Tomorrow, Overdue)
- **Quick-add syntax** - Rapidly create tasks with `!priority #tags @dates >Category`
- **Drag-and-drop** - Reorder tasks within priority groups
- **Search** - Find tasks by title, description, or tags
- **Archive** - Clean up completed tasks without deleting
- **MCP server** - AI assistant integration via Model Context Protocol
- **Keyboard shortcuts** - Power-user friendly

## Quick Start

```bash
# Clone the repo
git clone https://github.com/bnaylor/sharpei.git
cd sharpei

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python sharpei.py
```

The app opens automatically at http://127.0.0.1:8000

## Quick-Add Syntax

Create tasks rapidly from the input field:

```
Call dentist @tomorrow !high #health
Finish report >Work #q4 @friday
Buy groceries @+2d !low
```

| Element | Syntax | Examples |
|---------|--------|----------|
| Priority | `!high` `!low` | `!high`, `!h`, `!low`, `!l` |
| Hashtags | `#tag` | `#work #urgent` |
| Due date | `@date` | `@today`, `@tomorrow`, `@monday`, `@+3d`, `@+2w`, `@2025-02-15` |
| Category | `>name` | `>Work`, `>Personal` |

See [doc/quick-add.md](doc/quick-add.md) for full documentation.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+A` | Archive completed tasks |
| `Ctrl+Shift+H` | Toggle archived tasks visibility |
| `Ctrl+Shift+D` | Toggle details view |

## MCP Server

Sharpei includes an MCP server for AI assistant integration:

```bash
python mcp_server.py
```

Configure in your AI tool (Claude Code, Claude Desktop, etc.):

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

See [doc/mcp.md](doc/mcp.md) for available tools and full documentation.

## Testing

```bash
# Run all tests (83 total)
pytest

# Run specific test suites
pytest tests/test_api.py      # API tests (28)
pytest tests/test_mcp_server.py  # MCP tests (25)
pytest tests/test_ui.py       # UI tests (30)
```

See [doc/testing.md](doc/testing.md) for testing documentation.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: Alpine.js, Bootstrap 5, Sortable.js
- **Testing**: pytest, Playwright

## Documentation

- [Quick-Add Syntax](doc/quick-add.md)
- [MCP Server](doc/mcp.md)
- [Testing](doc/testing.md)

## Credits

Built with assistance from [Gemini 3](https://deepmind.google/technologies/gemini/) and [Claude Opus 4.5](https://www.anthropic.com/claude).

## License

Apache 2.0 License - see [LICENSE](LICENSE) for details.
