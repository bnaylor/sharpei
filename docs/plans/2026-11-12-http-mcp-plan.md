# Sharpei Streamable HTTP MCP Implementation Plan

> **For Hermes:** Use subagent-driven-development or direct TDD execution task-by-task.

**Goal:** Expose Sharpei's 12 MCP tools natively at `/mcp` over Streamable HTTP inside FastAPI with `Bearer` and `X-API-Key` authentication.

**Architecture:** `mcp_server.py` defines the canonical 12-tool `FastMCP` server (`json_response=True, stateless_http=True`). `app/main.py` manages a fresh `StreamableHTTPSessionManager` per FastAPI lifespan, wires `/mcp` and `/mcp/` directly without trailing-slash redirects, and enforces `SHARPEI_API_KEY` across `/api` and `/mcp` via a pure-ASGI middleware.

**Tech Stack:** Python 3.12, FastAPI / Starlette, SQLAlchemy, `mcp` (`FastMCP`, `StreamableHTTPSessionManager`), `pytest`.

---

### Task 1: Add `set_task_description`, `set_task_blockers`, and Streamable HTTP config to `mcp_server.py`

**Objective:** Bring `mcp_server.py` to 12-tool parity and configure `FastMCP` for stateless Streamable HTTP and test DB isolation.

**Files:**
- Modify: `mcp_server.py`
- Modify: `tests/conftest.py`
- Test: `tests/test_mcp_server.py`

**Steps:**
1. Add failing tests in `tests/test_mcp_server.py` for `set_task_description` and `set_task_blockers`.
2. Run `pytest tests/test_mcp_server.py -v` and confirm failure (`AttributeError`).
3. Update `mcp_server.py`:
   - Configure `FastMCP` with `json_response=True, stateless_http=True, transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False)`.
   - Use dynamic `app.database.SessionLocal` lookup when `mcp_server.SessionLocal` is not overridden, and patch `mcp_server.SessionLocal` in `conftest.py`'s `api_client` / `live_server` fixtures if needed.
   - Implement `set_task_description(task_id: int, description: str)` and `set_task_blockers(task_id: int, blocked_by_ids: List[int])`.
4. Run `pytest tests/test_mcp_server.py -v` and confirm pass.

---

### Task 2: Mount `/mcp` on FastAPI, upgrade `APIKeyMiddleware` to pure ASGI, and fix `GET /api/tasks` priority filter

**Objective:** Serve Streamable HTTP MCP at `/mcp` (and `/mcp/`) with `Bearer` + `X-API-Key` auth and `priority` query support on `/api/tasks`.

**Files:**
- Modify: `app/main.py`
- Create: `tests/test_mcp_http.py`

**Steps:**
1. Write `tests/test_mcp_http.py` covering:
   - `POST /mcp` `initialize`, `tools/list` (12 tools), and `tools/call` (`create_task`, `set_task_description`, `set_task_blockers`, `list_tasks`) with `Host: sharpei.scromp.net`.
   - `SHARPEI_API_KEY` enforcement on `/mcp` and `/api/tasks`: missing → `401`, wrong key → `401`, `X-API-Key` → `200`, `Authorization: Bearer <key>` → `200`.
   - `GET /api/tasks?priority=0` filtering.
2. Run `pytest tests/test_mcp_http.py -v` and confirm failure (`404` on `/mcp`).
3. Update `app/main.py`:
   - Implement `MCPStreamableASGIApp` + FastAPI `lifespan` managing `StreamableHTTPSessionManager`.
   - Register `Route("/mcp", endpoint=mcp_asgi)` and `Route("/mcp/", endpoint=mcp_asgi)`.
   - Replace `BaseHTTPMiddleware` with pure-ASGI `APIKeyMiddleware` checking `X-API-Key` and `Authorization: Bearer <token>` via `hmac.compare_digest` on `/api` and `/mcp`.
   - Add `priority: Optional[int] = None` to `GET /api/tasks` and pass `priority=priority` to `crud.get_tasks`.
4. Run full test suite (`pytest -m "not ui"` / `pytest tests/test_api.py tests/test_mcp_server.py tests/test_mcp_http.py -v`) and confirm pass.

---

### Task 3: Update `Dockerfile` and Documentation (`doc/mcp.md`, `README.md`)

**Objective:** Ensure container builds include `mcp_server.py` and document native HTTP MCP config stanzas.

**Files:**
- Modify: `Dockerfile`
- Modify: `doc/mcp.md`
- Modify: `README.md`

**Steps:**
1. Add `COPY mcp_server.py .` to `Dockerfile`.
2. Update `doc/mcp.md` and `README.md` with Streamable HTTP (`/mcp`) configuration examples for Claude Code, Antigravity, and stdio local mode, plus the 2 added tools (`set_task_description`, `set_task_blockers`).
3. Run full non-Playwright test suite and verify clean git diff.
