"""Tests for the run() orchestration: first-run silence, new-event notification,
state persistence, and failure counting. Uses in-memory fakes (no network)."""
from __future__ import annotations

from notifier import run
from notifier.source import Event
from notifier.state import State


class FakeSource:
    def __init__(self, key, events=None, error=None):
        self.key = key
        self.display_name = key
        self._events = events or []
        self._error = error

    def fetch(self):
        if self._error is not None:
            raise self._error
        return self._events


class FakeTelegram:
    def __init__(self, fail=False):
        self.sent = []
        self._fail = fail

    def send(self, text):
        if self._fail:
            raise RuntimeError("boom")
        self.sent.append(text)


def _state(tmp_path):
    return State(path=tmp_path / "state.json")


def test_first_run_records_without_notifying(tmp_path):
    source = FakeSource("s", [Event(id="1", url="u1")])
    telegram = FakeTelegram()

    failures = run([source], _state(tmp_path), telegram)

    assert failures == 0
    assert telegram.sent == []  # first run is silent
    assert (tmp_path / "state.json").exists()


def test_new_event_notifies_on_subsequent_run(tmp_path):
    state = _state(tmp_path)
    telegram = FakeTelegram()

    run([FakeSource("s", [Event(id="1", url="u1")])], state, telegram)
    # Reload state from disk to simulate the next scheduled run.
    run(
        [FakeSource("s", [Event(id="1", url="u1"), Event(id="2", url="u2", title="New")])],
        _state(tmp_path),
        telegram,
    )

    assert len(telegram.sent) == 1
    assert "u2" in telegram.sent[0]


def test_fetch_failure_is_counted_and_isolated(tmp_path):
    good = FakeSource("good", [Event(id="1", url="u1")])
    bad = FakeSource("bad", error=RuntimeError("network down"))
    telegram = FakeTelegram()

    failures = run([good, bad], _state(tmp_path), telegram)

    assert failures == 1
    # The healthy source still recorded its state.
    assert _state(tmp_path).is_initialised("good")
    # The failed source is left untouched so it doesn't re-notify next run.
    assert not _state(tmp_path).is_initialised("bad")


def test_send_failure_is_counted(tmp_path):
    state = _state(tmp_path)
    run([FakeSource("s", [Event(id="1", url="u1")])], state, FakeTelegram())

    failures = run(
        [FakeSource("s", [Event(id="2", url="u2")])],
        _state(tmp_path),
        FakeTelegram(fail=True),
    )

    assert failures == 1
