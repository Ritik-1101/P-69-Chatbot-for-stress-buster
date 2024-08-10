# tests/test_string_operations.py

def test_string_concat():
    assert "Hello, " + "World!" == "Hello, World!"  # This test should pass

def test_string_length():
    assert len("OpenAI") == 6  # This test should pass

def test_string_failure():
    assert len("OpenAI") == 7  # This will cause the test to fail
