# Remote Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable an optional remote backend mode with secure, encrypted communication (HTTPS) and API key authentication.

**Architecture:** 
1. Enhance the `sharpei.py` CLI to support host/port/SSL/API Key arguments.
2. Implement a FastAPI middleware to handle optional `X-API-Key` authentication.
3. Update the PWA settings to allow configuring a remote API URL and API key.
4. Refactor frontend `fetch` calls to use a centralized requester that adds auth headers and the correct base URL.

**Tech Stack:** 
* Python/FastAPI (Backend)
* Uvicorn (ASGI Server)
* Alpine.js (Frontend)
* localStorage (Settings Persistence)

---

### Task 1: Backend CLI Enhancements

**Files:**
- Modify: `sharpei.py`

- [ ] **Step 1: Replace simple `if __name__ == "__main__":` with `argparse` logic**

```python
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Sharpei TODO")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--no-browser", action="store_true", help="Skip opening browser")
    parser.add_argument("--ssl-cert", help="Path to SSL certificate")
    parser.add_argument("--ssl-key", help="Path to SSL key")
    parser.add_argument("--api-key", help="Secret key for API access")
    args = parser.parse_args()

    if args.api_key:
        os.environ["SHARPEI_API_KEY"] = args.api_key

    if not args.no_browser:
        threading.Thread(target=open_browser, args=(args.host, args.port, args.ssl_cert), daemon=True).start()

    uvicorn_kwargs = {
        "app": "app.main:app",
        "host": args.host,
        "port": args.port,
        "reload": True if args.host == "127.0.0.1" else False, # Only reload on localhost
        "ssl_certfile": args.ssl_cert,
        "ssl_keyfile": args.ssl_key
    }
    uvicorn.run(**uvicorn_kwargs)
```

- [ ] **Step 2: Update `open_browser` to handle host/port/HTTPS**

```python
def open_browser(host, port, is_https):
    protocol = "https" if is_https else "http"
    # Wait a second for the server to start
    time.sleep(1.5)
    webbrowser.open(f"{protocol}://{host}:{port}")
```

- [ ] **Step 3: Verify CLI help works**

Run: `python sharpei.py --help`
Expected: Shows all new arguments.

- [ ] **Step 4: Commit**

```bash
git add sharpei.py
git commit -m "feat: add CLI arguments for remote hosting and security"
```

---

### Task 2: API Key Middleware

**Files:**
- Modify: `app/main.py`

- [ ] **Step 1: Add `X-API-Key` validation middleware**

```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        api_key = os.getenv("SHARPEI_API_KEY")
        # Only enforce on /api requests if an API Key is set in env
        if api_key and request.url.path.startswith("/api"):
            header_key = request.headers.get("X-API-Key")
            if header_key != api_key:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Unauthorized: Invalid or missing API Key"}
                )
        return await call_next(request)

app.add_middleware(APIKeyMiddleware)
```

- [ ] **Step 2: Verify local mode still works without a key**

Run: `python sharpei.py --no-browser`
Run in another terminal: `curl -i http://127.0.0.1:8000/api/categories`
Expected: `200 OK`

- [ ] **Step 3: Verify authenticated mode rejects unauthorized requests**

Run: `SHARPEI_API_KEY=secret python sharpei.py --no-browser`
Run in another terminal: `curl -i http://127.0.0.1:8000/api/categories`
Expected: `401 Unauthorized`

- [ ] **Step 4: Verify authenticated mode accepts authorized requests**

Run in another terminal: `curl -i -H "X-API-Key: secret" http://127.0.0.1:8000/api/categories`
Expected: `200 OK`

- [ ] **Step 5: Commit**

```bash
git add app/main.py
git commit -m "feat: implement API Key middleware"
```

---

### Task 3: Frontend Settings UI

**Files:**
- Modify: `templates/index.html`

- [ ] **Step 1: Add Remote API and Key fields to settings modal**

Search for settings modal container and add the following fields:

```html
<div class="mb-4">
    <label class="block text-sm font-medium mb-1">Remote API URL (optional)</label>
    <input type="text" x-model="remoteApiUrl" placeholder="https://your-server:8000" 
           class="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600">
    <p class="text-xs text-gray-500 mt-1">Leave empty to use current host.</p>
</div>
<div class="mb-4">
    <label class="block text-sm font-medium mb-1">API Key (optional)</label>
    <input type="password" x-model="apiKey" placeholder="Your secret key" 
           class="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600">
</div>
```

- [ ] **Step 2: Commit**

```bash
git add templates/index.html
git commit -m "ui: add remote connection fields to settings"
```

---

### Task 4: Frontend State and Persistence

**Files:**
- Modify: `static/app.js`

- [ ] **Step 1: Add new settings to `sharpei()` state**

```javascript
remoteApiUrl: localStorage.getItem('remoteApiUrl') || '',
apiKey: localStorage.getItem('apiKey') || '',
```

- [ ] **Step 2: Add logic to save settings when they change**

We can add a watcher or just update `toggleDarkMode` style methods if there's no central save. Since we use `x-model`, let's add an explicit save in the settings close logic or separate save method.

```javascript
saveSettings() {
    localStorage.setItem('remoteApiUrl', this.remoteApiUrl);
    localStorage.setItem('apiKey', this.apiKey);
    localStorage.setItem('darkMode', this.darkMode);
    this.closeSettings();
    this.checkConnection(); // Refresh data from potentially new server
},
```

- [ ] **Step 3: Update `templates/index.html` to use `saveSettings()`**

Update the "Close" or "Save" button in the settings modal to call `saveSettings()`.

- [ ] **Step 4: Commit**

```bash
git add static/app.js templates/index.html
git commit -m "feat: persist remote backend settings in localStorage"
```

---

### Task 5: Centralized Request Helper

**Files:**
- Modify: `static/app.js`

- [ ] **Step 1: Create `request(path, options = {})` helper**

```javascript
async request(path, options = {}) {
    // Ensure path starts with /
    if (!path.startsWith('/')) path = '/' + path;
    
    const baseUrl = this.remoteApiUrl ? this.remoteApiUrl.replace(/\/$/, '') : '';
    const url = baseUrl + path;
    
    const headers = options.headers || {};
    if (this.apiKey) {
        headers['X-API-Key'] = this.apiKey;
    }
    
    const finalOptions = {
        ...options,
        headers: headers
    };
    
    const response = await fetch(url, finalOptions);
    if (response.status === 401) {
        this.showError('Authentication failed. Check your API Key.');
        this.serverError = true;
    }
    return response;
},
```

- [ ] **Step 2: Refactor `checkConnection` to use the helper**

```javascript
checkConnection() {
    return this.request('/api/categories')
        .then(res => {
            this.serverError = !res.ok;
        })
        .catch(err => {
            this.serverError = true;
        });
},
```

- [ ] **Step 3: Refactor all other `fetch` calls**

This includes `exportData`, `importData`, and all `crud` operations (which I'll need to locate in `app.js`).

- [ ] **Step 4: Verify full application functionality**

1. Run backend locally without a key.
2. Open app, ensure it still works.
3. Run backend with a key.
4. App should show error/red indicator.
5. Enter key in settings, app should recover.

- [ ] **Step 5: Commit**

```bash
git add static/app.js
git commit -m "refactor: use centralized request helper for API/Auth"
```

---

### Task 6: Documentation and Final Polish

**Files:**
- Modify: `README.md`
- Modify: `doc/testing.md` (if it exists)

- [ ] **Step 1: Add "Remote Hosting" section to README**

Describe how to run with `--host`, `--api-key`, and SSL.

- [ ] **Step 2: Final smoke test across modes**

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document remote hosting mode"
```
