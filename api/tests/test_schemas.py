def test_kill_event_parses():
    from app.schemas.events import EventPayload
    from pydantic import TypeAdapter
    ta = TypeAdapter(EventPayload)
    event = ta.validate_python({
        "type": "kill",
        "match_id": "00000000-0000-0000-0000-000000000001",
        "round_number": 1,
        "killer_steam_id": 76561198000000001,
        "victim_steam_id": 76561198000000002,
        "weapon": "ak47",
        "headshot": True,
    })
    assert event.type == "kill"
    assert event.headshot is True


def test_invalid_event_type_raises():
    from app.schemas.events import EventPayload
    from pydantic import TypeAdapter, ValidationError
    ta = TypeAdapter(EventPayload)
    try:
        ta.validate_python({"type": "nonexistent"})
        assert False, "should have raised"
    except ValidationError:
        pass
