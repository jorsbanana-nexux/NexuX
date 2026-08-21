"""Skip legacy local-first-v5 tests that depend on the removed monolithic
GenerateRequest/server module (superseded by backend/main.py)."""
collect_ignore = [
    "test_server.py",
    "tests/test_fronted_control_matrix.py",
]
