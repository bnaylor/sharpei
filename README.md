# Sharpei

A focused, local-first TODO application inspired by [MyTinyTodo](https://www.mytinytodo.net/).

Sharpei runs entirely on your machine with no cloud dependencies, stores data in SQLite for easy AI/agent access, and provides a clean, responsive UI for managing tasks, and an MCP server for direct AI agent manipulation.

![Sharpei screenshot](assets/sharpei_screenshot.png?raw=true)

## Features

- **Local-first** - Runs on localhost, no internet required
- **SQLite storage** - Simple, portable database that AI tools can read
- **Calendar View** - Interactive monthly grid to visualize deadlines
- **Bulk Actions** - Multi-select tasks for group updates (move, priority, delete)
- **Task Recurrence** - Automatically repeating tasks (daily, weekly, custom)
- **Smart Categories** - Save search queries as persistent sidebar items
- **Advanced Search** - Filter by status (`is:overdue`), priority, and more
- **PWA Support** - Install as a standalone desktop app with offline caching
- **Data Portability** - JSON export/import and automated daily backups
- **Markdown notes** - Capture details about your tasks in markdown syntax
- **Subtasks** - Break down tasks into smaller items
- **Hashtags** - Tag tasks for easy filtering
- **Quick-add syntax** - Rapidly create tasks with `!priority #tags @dates *recur >Category`
- **MCP server** - AI assistant integration via Model Context Protocol
- **Dark Mode** - Full support for light and dark themes

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
Submit timesheet *weekly @friday >Work
Water plants *3d @tomorrow
```

| Element | Syntax | Examples |
|---------|--------|----------|
| Priority | `!high` `!low` | `!high`, `!h`, `!low`, `!l` |
| Hashtags | `#tag` | `#work #urgent` |
| Due date | `@date` | `@today`, `@monday`, `@+3d`, `@2025-02-15` |
| Recurrence | `*pattern` | `*daily`, `*weekly`, `*monthly`, `*3d`, `*2w` |
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

See [doc/mcp.md](doc/mcp.md) for full documentation.

## Testing

```bash
# Run all tests (125 total)
pytest
```

## Documentation

- [Quick-Add Syntax](doc/quick-add.md)
- [Search & Smart Filters](doc/search.md)
- [Calendar View](doc/calendar.md)
- [Bulk Actions](doc/bulk-actions.md)
- [Task Dependencies](doc/dependencies.md)
- [Data Portability & Backups](doc/data-portability.md)
- [MCP Server](doc/mcp.md)
- [Testing](doc/testing.md)

## Credits

Built with assistance from [Gemini 3](https://deepmind.google/technologies/gemini/) and [Claude Opus 4.5](https://www.anthropic.com/claude).

## License

Apache 2.0 License - see [LICENSE](LICENSE) for details.
