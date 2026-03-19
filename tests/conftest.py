"""Pytest configuration and shared fixtures.

Configures a session-scoped database connection before any tests run.
All tests are read-only (SELECT only) against the production database.
"""

from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load .env before autodealer imports so DatabaseConfig picks up env vars
load_dotenv(Path(__file__).parent.parent / ".env")

from autodealer.connection import configure_database, get_engine  # noqa: E402


def pytest_configure(config: pytest.Config) -> None:
    """Connect to the database once before the test session starts."""
    configure_database(
        host="192.168.88.64",
        port=3050,
        database=r"C:\Program Files (x86)\AutoDealer\AutoDealer\Database\Autodealer061221.fdb",
        user="SYSDBA",
        password="masterkey",
        charset="UTF8",
    )


@pytest.fixture(scope="session", autouse=True)
def db_engine():
    """Session-scoped engine fixture. Disposes cleanly after all tests."""
    engine = get_engine()
    yield engine
    engine.dispose()
