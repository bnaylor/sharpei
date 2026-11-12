# Sharpei Native Streamable HTTP MCP Endpoint Design

**Date:** 2026-11-12
**Status:** Approved

## Problem

Sharpei currently ships `mcp_server.py` as a local SQLite stdio server and relies on an untracked client-side proxy script (`mcp_server_remote.py`) to expose MCP tools against `https://sharpei.scromp.net`. Configuring new MCP clients (Claude Code, Antigravity, Hermes) requires copying `mcp_server_remote.py` and managing Python/`uv` dependencies on each client host. Additionally, `mcp_server.py` (10 tools) drifted behind `mcp_server_remote.py` (12 tools: `set_task_description`, `set_task_blockers`), and `GET /api/tasks` ignored the `priority` query parameter.

## Goals

1. Expose a first-class MCP Streamable HTTP (`2025-03-26`) endpoint at `https://sharpei.scromp.net/mcp` inside the existing FastAPI process and container.
2. Authenticate `/mcp` (and `/api`) with `SHARPEI_API_KEY`, accepting either `Authorization: Bearer <key>` or `X-API-Key: <key>`.
3. Achieve full 12-tool parity in `mcp_server.py` while keeping standalone stdio execution (`python mcp_server.py`) working.
4. Fix `GET /api/tasks` to accept `priority: Optional[int] = None` so REST and MCP filtering match.

## Architecture

### 1. Unified `mcp_server.py`
- Configure `FastMCP("Sharpei TODO", log_level="WARNING", json_response=True, stateless_http=True, transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))`.
  - `json_response=True, stateless_http=True` matches our proven `clomptrader` pattern: supports standard `initialize`, `tools/list`, and `tools/call` handshakes across pod restarts without sticky SSE state.
  - Disabling FastMCP's localhost DNS-rebinding host filter prevents `421 Misdirected Request` behind Traefik (`Host: sharpei.scromp.net`) and Starlette `TestClient` (`Host: testserver`).
- Add `set_task_description(task_id: int, description: str)` and `set_task_blockers(task_id: int, blocked_by_ids: List[int])` delegating to `update_task(...)` so `mcp_server.py` exposes all 12 tools.
- Resolve database sessions dynamically (`SessionLocal()` via module attribute fallback to `app.database.SessionLocal`) so both `mcp_server` and `api_client` pytest fixtures isolate onto temporary SQLite files cleanly.

### 2. FastAPI Lifespan & Route Wiring (`app/main.py`)
- Wrap `mcp` in a lightweight `MCPStreamableASGIApp` helper that instantiates a fresh `StreamableHTTPSessionManager` inside FastAPI's `lifespan` context manager (`StreamableHTTPSessionManager.run()` is single-use per instance; creating one per lifespan allows repeated `with TestClient(app):` blocks in tests).
- Register Starlette `Route("/mcp", endpoint=mcp_asgi)` and `Route("/mcp/", endpoint=mcp_asgi)` directly on `app.router.routes` to avoid `Mount("/mcp", ...)`'s `307 Temporary Redirect` on `POST /mcp`.

### 3. Pure-ASGI Authentication Middleware (`app/main.py`)
- Replace `BaseHTTPMiddleware` (which buffers streaming responses and conflicts with AnyIO task groups) with a pure-ASGI `APIKeyMiddleware`.
- Protect paths matching `/api` (`/api` or `/api/...`) and `/mcp` (`/mcp` or `/mcp/...`) whenever `SHARPEI_API_KEY` is non-empty.
- Extract credentials from `X-API-Key` or `Authorization: Bearer <token>` (case-insensitive scheme) and compare via `hmac.compare_digest`. Return `401` JSON `{"detail": "Unauthorized: Invalid or missing API Key"}` on mismatch.

### 4. Packaging & Documentation
- Copy `mcp_server.py` into `/app/` in `Dockerfile`.
- Document remote HTTP MCP configuration for Claude Code, Antigravity, and Hermes in `doc/mcp.md` and `README.md`.

## Testing Strategy

- **Unit tests (`tests/test_mcp_server.py`):** Add coverage for `set_task_description` (set and clear) and `set_task_blockers` (set and clear).
- **Integration tests (`tests/test_mcp_http.py`):**
  - Auth enforcement on `/mcp` and `/api` when `SHARPEI_API_KEY` is set: missing header → `401`, wrong token → `401`, valid `X-API-Key` → `200`, valid `Authorization: Bearer <key>` → `200`.
  - Unauthenticated access allowed when `SHARPEI_API_KEY` is unset (local dev parity).
  - Full MCP JSON-RPC flow over `POST /mcp` with `Host: sharpei.scromp.net`: `initialize`, `tools/list` (verifying all 12 tool names), and `tools/call` (`create_task` → `list_tasks` → `complete_task`).
  - `GET /api/tasks?priority=0` filter verification.
