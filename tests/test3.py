def test_string_concat():
    assert "Hello, " + "World!" == "Hello, World!"  

def test_string_length():
    assert len("OpenAI") == 6  

def test_string_failure():
    assert len("OpenAI") == 7  
