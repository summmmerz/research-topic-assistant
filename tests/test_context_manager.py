from app.core.context import ContextManager


def make_manager(**overrides):
    config = {
        "storage_backend": "json",
        "auto_save": False,
        "auto_load": False,
        "max_history_length": 6,
        "max_context_depth": 2,
        "summary_trigger_length": 4,
        "summary_keep_recent": 2,
        "max_summary_chars": 500,
    }
    config.update(overrides)
    return ContextManager(config)


def test_context_is_summarized_when_trigger_length_is_exceeded():
    manager = make_manager()

    for index in range(5):
        manager.update_context("user-1", f"message-{index}", "user")

    stored = manager.export_context("user-1")["context"]

    assert len(stored) == 3
    assert stored[0]["role"] == "system"
    assert stored[0]["type"] == "context_summary"
    assert "message-0" in stored[0]["content"]
    assert "message-2" in stored[0]["content"]
    assert [msg["content"] for msg in stored[1:]] == ["message-3", "message-4"]


def test_get_context_returns_summary_plus_recent_messages():
    manager = make_manager()

    for index in range(5):
        manager.update_context("user-1", f"message-{index}", "user")

    context = manager.get_context("user-1")

    assert [msg["role"] for msg in context] == ["system", "user", "user"]
    assert "message-0" in context[0]["content"]
    assert [msg["content"] for msg in context[1:]] == ["message-3", "message-4"]


def test_auto_summarize_can_be_disabled():
    manager = make_manager(
        auto_summarize=False,
        max_history_length=3,
        max_context_depth=3,
    )

    for index in range(5):
        manager.update_context("user-1", f"message-{index}", "user")

    context = manager.get_context("user-1")

    assert [msg["content"] for msg in context] == [
        "message-2",
        "message-3",
        "message-4",
    ]
