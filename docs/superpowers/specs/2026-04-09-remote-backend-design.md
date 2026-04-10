# Remote Backend Design Spec

This spec outlines the addition of an optional remote execution mode for Sharpei, enabling secure, encrypted communication between a remote frontend and a backend hosted on a different system.

## Goals

*   **Remote Connectivity:** Allow the backend to listen on non-localhost interfaces (e.g., `0.0.0.0`).
*   **Encrypted Communication:** Support HTTPS/SSL natively via CLI arguments.
*   **API Security:** Implement optional API Key authentication for data protection.
*   **Flexible Frontend:** Enable the PWA to connect to a remote API URL with a persistent API Key.
*   **Backward Compatibility:** Maintain the current local-first, zero-config experience as the default.

## Architecture

The system will transition from a hardcoded `localhost:8000` setup to a configurable environment.

### 1. Backend CLI (`sharpei.py`)
Enhance `sharpei.py` to accept the following arguments using `argparse`:
*   `--host`: Host interface (default: `127.0.0.1`).
*   `--port`: Port number (default: `8000`).
*   `--no-browser`: Flag to skip auto-opening the browser.
*   `--ssl-cert`: Path to SSL certificate file (optional).
*   `--ssl-key`: Path to SSL private key file (optional).
*   `--api-key`: Secret key required for all API requests (optional).

If `--api-key` is provided, it will be set as an environment variable (`SHARPEI_API_KEY`) for the FastAPI process to consume.

### 2. API Key Middleware (`app/main.py`)
A FastAPI middleware will be added to check for the `X-API-Key` header on all `/api/*` requests.
*   If `SHARPEI_API_KEY` is not set, the middleware is transparent (no auth required).
*   If `SHARPEI_API_KEY` is set, it validates that the `X-API-Key` header matches.
*   Failed requests return `401 Unauthorized`.

### 3. Frontend Settings (`static/app.js` & `templates/index.html`)
The "Settings" modal will be expanded to include:
*   **Remote API URL:** A field to enter the full base URL (e.g., `https://my-server.com:8000`). If empty, it defaults to the current origin.
*   **API Key:** A password field to enter the key.
*   **Storage:** Both will be persisted in `localStorage`.

All `fetch()` calls in `app.js` will be updated to use the configured API base URL and include the `X-API-Key` header if a key is stored.

## Data Flow

1.  **Local Mode (Default):**
    *   `sharpei.py` starts on `127.0.0.1:8000`.
    *   Browser opens `http://127.0.0.1:8000`.
    *   UI fetches `/api/...` (relative path).
    *   No API key required.

2.  **Remote Mode:**
    *   Backend starts on `0.0.0.0:8000` with `--api-key MY_SECRET --ssl-cert ...`.
    *   User opens PWA, goes to Settings, enters `https://SERVER_IP:8000` and `MY_SECRET`.
    *   UI fetches `https://SERVER_IP:8000/api/...` with `X-API-Key: MY_SECRET`.

## Testing Strategy

*   **Unit Tests:** Update tests to handle both authenticated and unauthenticated scenarios.
*   **Integration Tests:** Verify that CLI arguments correctly propagate to the `uvicorn` and FastAPI layers.
*   **UI Tests:** Verify that settings are correctly saved and applied to `fetch` calls.
*   **Manual Verification:** Run the backend with `--api-key` and verify that unauthorized requests fail.
