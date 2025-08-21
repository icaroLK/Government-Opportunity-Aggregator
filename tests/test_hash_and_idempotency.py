from scrapers.formatter import generate_hash

def test_generate_hash_stable():
    a = generate_hash("ABC|Title")
    b = generate_hash("ABC|Title")
    assert a == b

def test_generate_hash_changes_on_title():
    a = generate_hash("ABC|Title")
    b = generate_hash("ABC|Other")
    assert a != b
