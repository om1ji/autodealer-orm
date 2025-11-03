# tests/test_connection.py
from autodealer import connect

def test_connection_import():
    assert callable(connect)
