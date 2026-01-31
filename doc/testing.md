# Testing Sharpei

Sharpei has a comprehensive test suite covering the MCP server, REST API, and UI. All tests use temporary databases to avoid affecting your data.

## Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with verbose output (default via pytest.ini)
pytest -v
```

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_mcp_server.py   # MCP server tool tests
├── test_api.py          # FastAPI endpoint tests
└── test_ui.py           # Playwright UI tests
```

## Test Categories

### MCP Server Tests (`test_mcp_server.py`)
**25 tests** covering all MCP tools:

| Category | Tests | Description |
|----------|-------|-------------|
| Categories | 3 | List, create, list with data |
| Tasks | 9 | CRUD operations, completion, archiving |
| Subtasks | 3 | Add subtask, inheritance, invalid parent |
| Filtering | 6 | By category, search, archived status |
| Archiving | 2 | Archive all, archive by category |
| Priority | 1 | Task ordering |

### API Tests (`test_api.py`)
**28 tests** covering all REST endpoints:

| Category | Tests | Description |
|----------|-------|-------------|
| Root | 1 | HTML page load |
| Categories | 5 | CRUD, cascade delete behavior |
| Tasks | 9 | CRUD, 404 handling, cascade delete |
| Filtering | 5 | Category, search, case-insensitive, archived |
| Reordering | 1 | Drag-and-drop position updates |
| Archive | 2 | Archive completed, by category |
| Subtasks | 3 | Create, in response, hidden at top level |
| Position | 2 | Auto-assignment, per-priority |

### UI Tests (`test_ui.py`)
**22 tests** covering browser interactions:

| Category | Tests | Description |
|----------|-------|-------------|
| Page Load | 3 | Title, banner, sidebar |
| Categories | 3 | Create, select, default selection |
| Tasks | 5 | Create, complete, uncomplete, delete |
| Expansion | 3 | Expand, edit description, change priority |
| Subtasks | 1 | Add subtask |
| Search | 2 | Search, clear search |
| Archiving | 2 | Archive completed, show archived |
| Show Details | 1 | Toggle details view |
| Hashtags | 2 | Add hashtag, filter by hashtag |

## Running Specific Tests

```bash
# Run only MCP tests
pytest tests/test_mcp_server.py

# Run only API tests
pytest tests/test_api.py

# Run only UI tests
pytest tests/test_ui.py

# Run a specific test class
pytest tests/test_api.py::TestTaskEndpoints

# Run a specific test
pytest tests/test_api.py::TestTaskEndpoints::test_create_task_minimal

# Run tests matching a pattern
pytest -k "search"
pytest -k "category"
```

## Test Options

```bash
# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Run failed tests from last run
pytest --lf

# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Generate coverage report (requires pytest-cov)
pytest --cov=app --cov-report=html
```

## UI Test Options

```bash
# Run UI tests with browser visible (headed mode)
pytest tests/test_ui.py --headed

# Run in specific browser
pytest tests/test_ui.py --browser firefox
pytest tests/test_ui.py --browser webkit

# Slow down for debugging (milliseconds)
pytest tests/test_ui.py --slowmo 500

# Keep browser open on failure
pytest tests/test_ui.py --headed --slowmo 100 -x
```

## Fixtures

Shared fixtures in `conftest.py`:

| Fixture | Scope | Description |
|---------|-------|-------------|
| `test_db` | function | Temporary SQLite database |
| `mcp_server` | function | MCP server with test database |
| `api_client` | function | FastAPI TestClient |
| `live_server` | function | Running server for UI tests |
| `ui_page` | function | Playwright page navigated to app |

## Writing New Tests

### API Test Example

```python
def test_my_endpoint(self, api_client):
    """Test description."""
    # Create test data
    response = api_client.post("/api/tasks", json={"title": "Test"})
    assert response.status_code == 200

    # Verify behavior
    data = response.json()
    assert data["title"] == "Test"
```

### UI Test Example

```python
def test_my_feature(self, ui_page):
    """Test description."""
    # Interact with UI
    ui_page.locator("input[placeholder='Add a task...']").fill("Test")
    ui_page.locator("input[placeholder='Add a task...']").press("Enter")

    # Wait for changes
    ui_page.wait_for_selector(".task-title:has-text('Test')")

    # Verify
    expect(ui_page.locator(".task-list")).to_contain_text("Test")
```

## Prerequisites

Install test dependencies:

```bash
pip install pytest pytest-playwright playwright
playwright install chromium
```

## Continuous Integration

Example GitHub Actions workflow:

```yaml
- name: Run tests
  run: |
    source venv/bin/activate
    playwright install chromium
    pytest --tb=short
```

## Test Database

Tests use temporary SQLite databases created in the system temp directory. Each test gets a fresh database that is automatically deleted after the test completes. This ensures:

- Tests are isolated from each other
- No interference with your actual data
- Tests can run in parallel safely
