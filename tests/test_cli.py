import threading
import time
from io import StringIO

from phrase_engine.__main__ import main
from phrase_engine.midi import FakeMidiBackend


def test_ports_lists_fake_devices():
    fake = FakeMidiBackend(["IAC Driver Bus 1"], ["IAC Driver Bus 2"])
    out, err = StringIO(), StringIO()
    rc = main(["ports"], backend_factory=lambda: fake, stdout=out, stderr=err)
    assert rc == 0
    assert "IAC Driver Bus 1" in out.getvalue()
    assert "IAC Driver Bus 2" in out.getvalue()


def test_echo_cli_forwards_a_note():
    fake = FakeMidiBackend(["keys"], ["synth"])

    def poke():
        deadline = time.monotonic() + 1.0
        while fake._callback is None and time.monotonic() < deadline:
            time.sleep(0.01)
        fake.simulate_in([0x90, 60, 96])

    threading.Thread(target=poke, daemon=True).start()
    out, err = StringIO(), StringIO()
    rc = main(
        ["echo", "--in", "keys", "--out", "synth", "--once", "--seconds", "2"],
        backend_factory=lambda: fake,
        stdout=out,
        stderr=err,
    )
    assert rc == 0, err.getvalue()
    assert fake.sent == [[0x90, 60, 96]]
    assert "C4 on vel 96" in out.getvalue()
    assert "M0 port test" in out.getvalue()
    assert fake.closed


def test_echo_refuses_same_port():
    fake = FakeMidiBackend(["IAC Driver Bus 1"], ["IAC Driver Bus 1"])
    out, err = StringIO(), StringIO()
    rc = main(
        ["echo", "--in", "IAC", "--out", "IAC", "--seconds", "0.1"],
        backend_factory=lambda: fake,
        stdout=out,
        stderr=err,
    )
    assert rc == 2
    assert "MIDI loop" in err.getvalue()
    assert fake.sent == []


def test_listen_cli_does_not_echo():
    fake = FakeMidiBackend(["keys"], ["synth"])

    def poke():
        deadline = time.monotonic() + 1.0
        while fake._callback is None and time.monotonic() < deadline:
            time.sleep(0.01)
        fake.simulate_in([0x91, 64, 10])

    threading.Thread(target=poke, daemon=True).start()
    out, err = StringIO(), StringIO()
    rc = main(
        ["listen", "--in", "keys", "--once", "--seconds", "2"],
        backend_factory=lambda: fake,
        stdout=out,
        stderr=err,
    )
    assert rc == 0, err.getvalue()
    assert fake.sent == []
    assert "E4 on vel 10" in out.getvalue()


def test_echo_requires_ports():
    fake = FakeMidiBackend(["keys"], ["synth"])
    out, err = StringIO(), StringIO()
    rc = main(["echo"], backend_factory=lambda: fake, stdout=out, stderr=err)
    assert rc == 2
    assert "echo needs" in err.getvalue()


def test_echo_virtual():
    fake = FakeMidiBackend([], [])

    def poke():
        deadline = time.monotonic() + 1.0
        while fake._callback is None and time.monotonic() < deadline:
            time.sleep(0.01)
        fake.simulate_in([0x80, 60, 0])

    threading.Thread(target=poke, daemon=True).start()
    out, err = StringIO(), StringIO()
    rc = main(
        ["echo", "--virtual", "--once", "--seconds", "2"],
        backend_factory=lambda: fake,
        stdout=out,
        stderr=err,
    )
    assert rc == 0, err.getvalue()
    assert fake.opened_input == "PhraseEngine IN"
    assert fake.opened_output == "PhraseEngine OUT"
    assert fake.sent == [[0x80, 60, 0]]


def test_config_file_ports(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text('{"midi": {"input": "keys", "output": "synth"}}', encoding="utf-8")
    fake = FakeMidiBackend(["keys"], ["synth"])

    def poke():
        deadline = time.monotonic() + 1.0
        while fake._callback is None and time.monotonic() < deadline:
            time.sleep(0.01)
        fake.simulate_in([0xB0, 1, 64])

    threading.Thread(target=poke, daemon=True).start()
    out, err = StringIO(), StringIO()
    rc = main(
        ["echo", "--config", str(cfg), "--once", "--seconds", "2"],
        backend_factory=lambda: fake,
        stdout=out,
        stderr=err,
    )
    assert rc == 0, err.getvalue()
    assert fake.sent == [[0xB0, 1, 64]]
