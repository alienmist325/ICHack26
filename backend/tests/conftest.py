"""Pytest configuration and fixtures for backend tests."""

import os
import pytest
from backend.app.database import init_db, reset_test_db


# Module-level flag to track if we're in integration tests
_integration_tests_completed = False


@pytest.fixture(scope="session", autouse=True)
def enable_test_mode():
    """Enable test mode for the entire test session."""
    os.environ["TEST_MODE"] = "true"
    yield
    # Cleanup after all tests
    os.environ.pop("TEST_MODE", None)


@pytest.fixture(scope="session", autouse=True)
def setup_session_db():
    """Initialize database for the session."""
    # Initialize database once at session start
    init_db()
    yield
    # Cleanup after all tests
    reset_test_db()


@pytest.fixture(autouse=True)
def setup_test_db(request):
    """
    Initialize database for each test.

    For test_integration.py: Database is shared across all tests in that module
    For other tests: Fresh database for each test
    """
    is_integration_test = "test_integration.py" in request.node.nodeid

    if not is_integration_test:
        # For non-integration tests, reset and initialize a fresh database
        reset_test_db()
        init_db()

    yield
