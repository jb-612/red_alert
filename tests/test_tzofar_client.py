from backend.ingestion.tzofar_client import _parse_response, strip_bom


def test_strip_bom_removes_bom():
    bom_text = "\ufeffhello"
    assert strip_bom(bom_text) == "hello"


def test_strip_bom_no_bom_unchanged():
    text = "hello"
    assert strip_bom(text) == "hello"


def test_strip_bom_empty_string():
    assert strip_bom("") == ""


def test_parse_response_extracts_alerts():
    json_text = """[
        {
            "date": "2024-01-15T10:30:00",
            "name": "תל אביב - מרכז",
            "category": 1,
            "title": "ירי רקטות וטילים"
        }
    ]"""
    alerts = _parse_response(json_text)
    assert len(alerts) == 1
    assert alerts[0]["location_name"] == "תל אביב - מרכז"
    assert alerts[0]["category"] == 1
    assert alerts[0]["source"] == "tzofar"


def test_parse_response_skips_invalid_dates():
    json_text = """[
        {
            "date": "not-a-date",
            "name": "test",
            "category": 1
        }
    ]"""
    alerts = _parse_response(json_text)
    assert len(alerts) == 0


def test_parse_response_handles_empty_list():
    alerts = _parse_response("[]")
    assert alerts == []


def test_parse_response_preserves_hebrew():
    json_text = """[
        {
            "date": "2024-01-15T10:30:00",
            "name": "ירושלים",
            "category": 1,
            "title": "ירי רקטות וטילים"
        }
    ]"""
    alerts = _parse_response(json_text)
    assert alerts[0]["location_name"] == "ירושלים"
