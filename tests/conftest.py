"""Shared test fixtures for Sharpei tests."""
import os
import socket
import sys
import tempfile
import threading
import time

import pytest
import uvicorn
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Base


def get_free_port():
    """Get a free port from the OS."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture
def test_db():
    """Create a temporary test database.

    Yields a dict with database connection info that can be used
    to configure test clients and MCP server.
    """
    # Create a temporary database file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield {
        "path": db_path,
        "url": db_url,
        "engine": engine,
        "SessionLocal": SessionLocal
    }

    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def mcp_server(test_db, monkeypatch):
    """Set up MCP server with test database."""
    import mcp_server as mcp_module

    # Monkeypatch the database connection
    monkeypatch.setattr(mcp_module, 'engine', test_db['engine'])
    monkeypatch.setattr(mcp_module, 'SessionLocal', test_db['SessionLocal'])

    return mcp_module


@pytest.fixture
def api_client(test_db, monkeypatch):
    """Create a test client for the FastAPI app with test database."""
    from starlette.testclient import TestClient

    # Monkeypatch the database before importing the app
    from app import database
    monkeypatch.setattr(database, 'engine', test_db['engine'])
    monkeypatch.setattr(database, 'SessionLocal', test_db['SessionLocal'])

    # Now import and create the app
    from app.main import app

    with TestClient(app) as client:
        yield client


class ServerThread(threading.Thread):
    """Thread that runs the uvicorn server."""

    def __init__(self, app, host, port):
        super().__init__()
        self.config = uvicorn.Config(app, host=host, port=port, log_level="error")
        self.server = uvicorn.Server(self.config)
        self.daemon = True

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True
        self.join(timeout=2)


@pytest.fixture(scope="function")
def live_server(test_db, monkeypatch):
    """Start a live server for UI testing.

    Yields the base URL of the server.
    """
    # Monkeypatch the database before importing the app
    from app import database
    monkeypatch.setattr(database, 'engine', test_db['engine'])
    monkeypatch.setattr(database, 'SessionLocal', test_db['SessionLocal'])

    # Import app after patching
    from app.main import app

    host = "127.0.0.1"
    port = get_free_port()

    server_thread = ServerThread(app, host, port)
    server_thread.start()

    # Wait for server to be ready
    for _ in range(20):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                break
        except ConnectionRefusedError:
            time.sleep(0.1)

    yield f"http://{host}:{port}"

    server_thread.stop()


@pytest.fixture(scope="function")
def ui_page(live_server, page):
    """Provide a Playwright page that's navigated to the app."""
    page.goto(live_server)
    # Wait for Alpine.js to initialize
    page.wait_for_selector("[x-data]")
    return page
