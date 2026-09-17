import threading
import time

import pytest

from phrase_engine.midi import (
    FakeMidiBackend,
    MidiEngine,
    PortError,
    resolve_port,
)


def test_resolve_exact_and_substring():
    ports = ["IAC Driver Bus 1", "IAC Driver Bus 2", "MODX M7"]
    assert resolve_port(ports, "IAC Driver Bus 1")[1] == "IAC Driver Bus 1"
    assert resolve_port(ports, "modx")[1] == "MODX M7"


def test_resolve_ambiguous():
    ports = ["IAC Driver Bus 1", "IAC Driver Bus 2"]
    with pytest.raises(PortError, match="ambiguous"):
        resolve_port(ports, "IAC")


def test_resolve_midihub_letter():
    ports = [
        "Midihub MH-0CNQEC3 A",
        "Midihub MH-0CNQEC3 B",
        "IAC Driver Bus 1",
    ]
    assert resolve_port(ports, "Midihub A")[1] == "Midihub MH-0CNQEC3 A"
    assert resolve_port(ports, "Midihub B")[1] == "Midihub MH-0CNQEC3 B"


def test_echo_copies_note_on_dedicated_thread():
    backend = FakeMidiBackend(["keys"], ["synth"])
    backend.open_input("keys")
    backend.open_output("synth")
    engine = MidiEngine(backend, echo=True)
    engine.start()
    try:
        backend.simulate_in([0x90, 60, 100])
        _wait_until(lambda: backend.sent == [[0x90, 60, 100]])
    finally:
        engine.stop()
    assert backend.closed


def test_listen_does_not_send():
    backend = FakeMidiBackend(["keys"], ["synth"])
    backend.open_input("keys")
    seen: list[tuple[int, ...]] = []
    engine = MidiEngine(backend, echo=False, on_message=lambda m: seen.append(m.data))
    engine.start()
    try:
        backend.simulate_in([0x90, 60, 100])
        _wait_until(lambda: seen == [(0x90, 60, 100)])
    finally:
        engine.stop()
    assert backend.sent == []


def test_channel_filter():
    backend = FakeMidiBackend(["keys"], ["synth"])
    backend.open_input("keys")
    backend.open_output("synth")
    engine = MidiEngine(backend, echo=True, channel=16)
    engine.start()
    try:
        backend.simulate_in([0x90, 60, 100])  # ch1
        backend.simulate_in([0x9F, 64, 80])  # ch16
        _wait_until(lambda: backend.sent == [[0x9F, 64, 80]])
        time.sleep(0.05)
    finally:
        engine.stop()
    assert backend.sent == [[0x9F, 64, 80]]


def test_drops_clock_bytes():
    backend = FakeMidiBackend(["keys"], ["synth"])
    backend.open_input("keys")
    backend.open_output("synth")
    engine = MidiEngine(backend, echo=True)
    engine.start()
    try:
        backend.simulate_in([0xF8])
        backend.simulate_in([0x90, 72, 10])
        _wait_until(lambda: backend.sent == [[0x90, 72, 10]])
    finally:
        engine.stop()


def test_self_loop_names_are_equal_after_resolve():
    backend = FakeMidiBackend(["IAC Driver Bus 1"], ["IAC Driver Bus 1"])
    opened_in = backend.open_input("IAC")
    opened_out = backend.open_output("IAC")
    assert opened_in == opened_out == "IAC Driver Bus 1"


def test_engine_rejects_bad_channel():
    with pytest.raises(Exception, match="channel"):
        MidiEngine(FakeMidiBackend(), channel=17)


def _wait_until(pred, timeout=1.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if pred():
            return
        time.sleep(0.01)
    raise AssertionError("timed out waiting for MIDI thread")


def test_midi_thread_name():
    backend = FakeMidiBackend()
    engine = MidiEngine(backend, echo=False)
    engine.start()
    try:
        names = {t.name for t in threading.enumerate()}
        assert "midi" in names
    finally:
        engine.stop()
