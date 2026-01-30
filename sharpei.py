#!/usr/bin/env python3
import uvicorn
import webbrowser
import threading
import time
import os

def open_browser():
    # Wait a second for the server to start
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    # Start browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run FastAPI server
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
