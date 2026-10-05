from web_app.utils import session_manager


def test_get_request_stats_returns_copy():
    session_manager.request_stats["endpoints"].clear()
    session_manager.request_stats["endpoints"]["/demo"] = {
        "count": 1,
        "total_time": 0.5,
        "avg_time": 0.5,
    }

    snapshot = session_manager.get_request_stats()
    snapshot["endpoints"]["/demo"]["count"] = 99

    assert session_manager.request_stats["endpoints"]["/demo"]["count"] == 1


def test_get_user_session_updates_last_activity():
    session_id = "session-test-web"
    first = session_manager.get_user_session(session_id)
    original_activity = first["last_activity"]

    second = session_manager.get_user_session(session_id)

    assert second["session_id"] == session_id
    assert second["last_activity"] >= original_activity
