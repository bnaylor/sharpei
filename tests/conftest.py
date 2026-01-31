"""Shared test fixtures for Sharpei tests."""
import os
import sys
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Base


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
