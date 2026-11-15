import pytest


@pytest.fixture(autouse=True)
def _usage_log_in_tmp(tmp_path, monkeypatch):
    """Tests must never write to the real data/usage.jsonl."""
    monkeypatch.setenv("USAGE_LOG", str(tmp_path / "usage.jsonl"))
