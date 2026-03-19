"""Write-test configuration — connects to StOm1.fdb (test database)."""

import pytest
from autodealer.connection import configure_database, get_engine, set_session_user


def pytest_configure(config: pytest.Config) -> None:
    configure_database(
        host="192.168.88.64",
        port=3050,
        database=r"C:\Program Files (x86)\AutoDealer\AutoDealer\Database\StOm1.fdb",
        user="SYSDBA",
        password="masterkey",
        charset="UTF8",
    )
    # AutoDealer triggers (e.g. ORGANIZATION_AU) read CURRENT_USER_ID from the
    # Firebird USER_SESSION context. Set it to the system user so write
    # operations don't fail FK/NOT-NULL validation inside triggers.
    set_session_user(1)


@pytest.fixture(scope="session", autouse=True)
def db_engine():
    engine = get_engine()
    yield engine
    engine.dispose()
