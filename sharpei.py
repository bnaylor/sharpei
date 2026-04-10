#!/usr/bin/env python3
import uvicorn
import webbrowser
import threading
import time
import os
import argparse

def open_browser(host="127.0.0.1", port=8000, is_https=False):
    protocol = "https" if is_https else "http"
    # Wait a second for the server to start
    time.sleep(1.5)
    webbrowser.open(f"{protocol}://{host}:{port}")

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

    is_https = bool(args.ssl_cert)

    if not args.no_browser:
        # Start browser in a separate thread
        threading.Thread(target=open_browser, args=(args.host, args.port, is_https), daemon=True).start()
    
    # Run FastAPI server
    uvicorn_kwargs = {
        "app": "app.main:app",
        "host": args.host,
        "port": args.port,
        "reload": True if args.host == "127.0.0.1" else False,
        "ssl_certfile": args.ssl_cert,
        "ssl_keyfile": args.ssl_key
    }
    uvicorn.run(**uvicorn_kwargs)

if __name__ == "__main__":
    main()
