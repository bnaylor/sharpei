"""Integration tests for Streamable HTTP MCP endpoint (/mcp) and auth middleware."""
import json

import pytest
from starlette.testclient import TestClient


MCP_HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
}

EXPECTED_TOOLS = {
    "list_categories",
    "create_category",
    "list_tasks",
    "get_task",
    "create_task",
    "update_task",
    "set_task_description",
    "set_task_blockers",
    "complete_task",
    "delete_task",
    "archive_completed",
    "add_subtask",
}


def _rpc(method: str, params: dict | None = None, req_id: int = 1) -> dict:
    payload = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        payload["params"] = params
    return payload


class TestMCPStreamableHTTP:
    """End-to-end tests for /mcp Streamable HTTP JSON-RPC."""

    def test_initialize_and_list_all_12_tools_with_external_host(self, test_db, monkeypatch):
        from app import database
        import mcp_server as mcp_module
        monkeypatch.delenv("SHARPEI_API_KEY", raising=False)
        monkeypatch.setattr(database, "engine", test_db["engine"])
        monkeypatch.setattr(database, "SessionLocal", test_db["SessionLocal"])
        monkeypatch.setattr(mcp_module, "SessionLocal", test_db["SessionLocal"])

        from app.main import app

        with TestClient(app, base_url="https://sharpei.scromp.net") as client:
            init_resp = client.post(
                "/mcp",
                headers=MCP_HEADERS,
                json=_rpc(
                    "initialize",
                    {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {"name": "pytest-client", "version": "1.0.0"},
                    },
                ),
            )
            assert init_resp.status_code == 200
            init_body = init_resp.json()
            assert init_body["result"]["serverInfo"]["name"] == "Sharpei TODO"

            tools_resp = client.post(
                "/mcp",
                headers=MCP_HEADERS,
                json=_rpc("tools/list", {}),
            )
            assert tools_resp.status_code == 200
            tools = {t["name"] for t in tools_resp.json()["result"]["tools"]}
            assert tools == EXPECTED_TOOLS

    def test_tool_call_round_trip_and_repeated_lifespans(self, api_client):
        # First client session via api_client fixture: create + describe + list
        create_resp = api_client.post(
            "/mcp",
            headers=MCP_HEADERS,
            json=_rpc(
                "tools/call",
                {
                    "name": "create_task",
                    "arguments": {
                        "title": "Ship native HTTP MCP",
                        "priority": 0,
                        "hashtags": "#sharpei #mcp",
                    },
                },
            ),
        )
        assert create_resp.status_code == 200
        content_text = create_resp.json()["result"]["content"][0]["text"]
        created = json.loads(content_text)
        assert created["title"] == "Ship native HTTP MCP"
        assert created["priority"] == 0

        desc_resp = api_client.post(
            "/mcp",
            headers=MCP_HEADERS,
            json=_rpc(
                "tools/call",
                {
                    "name": "set_task_description",
                    "arguments": {
                        "task_id": created["id"],
                        "description": "Mounted at /mcp",
                    },
                },
            ),
        )
        assert desc_resp.status_code == 200
        described = json.loads(desc_resp.json()["result"]["content"][0]["text"])
        assert described["description"] == "Mounted at /mcp"

        # Verify task also appears through REST /api/tasks?priority=0
        rest_high = api_client.get("/api/tasks", params={"priority": 0})
        assert rest_high.status_code == 200
        assert [t["title"] for t in rest_high.json()] == ["Ship native HTTP MCP"]

        rest_low = api_client.get("/api/tasks", params={"priority": 2})
        assert rest_low.status_code == 200
        assert rest_low.json() == []


class TestMCPAndAPIAuthentication:
    """Verify Bearer and X-API-Key authentication across /mcp and /api."""

    @pytest.fixture
    def authed_client(self, test_db, monkeypatch):
        from app import database
        import mcp_server as mcp_module
        monkeypatch.setenv("SHARPEI_API_KEY", "super-secret-test-key")
        monkeypatch.setattr(database, "engine", test_db["engine"])
        monkeypatch.setattr(database, "SessionLocal", test_db["SessionLocal"])
        monkeypatch.setattr(mcp_module, "SessionLocal", test_db["SessionLocal"])

        from app.main import app

        with TestClient(app, base_url="https://sharpei.scromp.net") as client:
            yield client

    def test_mcp_rejects_missing_and_invalid_credentials(self, authed_client):
        no_auth = authed_client.post("/mcp", headers=MCP_HEADERS, json=_rpc("tools/list", {}))
        assert no_auth.status_code == 401

        bad_bearer = authed_client.post(
            "/mcp",
            headers={**MCP_HEADERS, "Authorization": "Bearer wrong-key"},
            json=_rpc("tools/list", {}),
        )
        assert bad_bearer.status_code == 401

        bad_x_api = authed_client.post(
            "/mcp",
            headers={**MCP_HEADERS, "X-API-Key": "wrong-key"},
            json=_rpc("tools/list", {}),
        )
        assert bad_x_api.status_code == 401

    def test_mcp_accepts_bearer_and_x_api_key(self, authed_client):
        bearer_ok = authed_client.post(
            "/mcp",
            headers={**MCP_HEADERS, "Authorization": "Bearer super-secret-test-key"},
            json=_rpc("tools/list", {}),
        )
        assert bearer_ok.status_code == 200
        assert len(bearer_ok.json()["result"]["tools"]) == 12

        x_api_ok = authed_client.post(
            "/mcp",
            headers={**MCP_HEADERS, "X-API-Key": "super-secret-test-key"},
            json=_rpc("tools/list", {}),
        )
        assert x_api_ok.status_code == 200

    def test_rest_api_accepts_bearer_and_x_api_key_while_root_stays_public(self, authed_client):
        assert authed_client.get("/").status_code == 200
        assert authed_client.get("/api/tasks").status_code == 401
        assert (
            authed_client.get(
                "/api/tasks",
                headers={"Authorization": "Bearer super-secret-test-key"},
            ).status_code
            == 200
        )
        assert (
            authed_client.get(
                "/api/tasks",
                headers={"X-API-Key": "super-secret-test-key"},
            ).status_code
            == 200
        )
