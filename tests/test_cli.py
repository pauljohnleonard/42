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


def test_echo_requires_ports(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
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


def test_chords_cli_names_and_sends_ch16():
    fake = FakeMidiBackend(["keys"], ["synth"])

    def poke():
        deadline = time.monotonic() + 1.0
        while fake._callback is None and time.monotonic() < deadline:
            time.sleep(0.01)
        fake.simulate_in([0x90, 60, 96])
        fake.simulate_in([0x90, 64, 96])
        fake.simulate_in([0x90, 67, 96])

    threading.Thread(target=poke, daemon=True).start()
    out, err = StringIO(), StringIO()
    rc = main(
        ["chords", "--in", "keys", "--out", "synth", "--once", "--seconds", "2"],
        backend_factory=lambda: fake,
        stdout=out,
        stderr=err,
    )
    assert rc == 0, err.getvalue()
    lines = [ln.strip() for ln in out.getvalue().splitlines()]
    assert "C" in lines
    assert "M1 chord bus" in out.getvalue()
    ons = [m for m in fake.sent if m and m[0] == 0x9F]
    assert {m[1] for m in ons} == {60, 64, 67}
    assert fake.closed


def test_setup_yes_writes_named_devices(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fake = FakeMidiBackend(
        ["Midihub MH-0CNQEC3 A", "Midihub MH-0CNQEC3 B", "IAC Driver Bus 1"],
        ["Midihub MH-0CNQEC3 A", "Midihub MH-0CNQEC3 B", "IAC Driver Bus 2"],
    )
    out, err = StringIO(), StringIO()
    rc = main(["setup", "--yes"], backend_factory=lambda: fake, stdout=out, stderr=err)
    assert rc == 0, err.getvalue()
    text = (tmp_path / "config.json").read_text(encoding="utf-8")
    assert "pa5x" in text
    assert "Korg PA5X" in text
    assert "Midihub MH-0CNQEC3 A" in text
    assert '"input": "pa5x"' in text
    assert '"output": "modx"' in text
    assert fake.closed


def test_echo_uses_device_alias(tmp_path):
    cfg = tmp_path / "rig.json"
    cfg.write_text(
        """
        {
          "devices": {
            "pa5x": {"port": "Midihub MH-0CNQEC3 A", "label": "Korg PA5X"},
            "modx": {"port": "Midihub MH-0CNQEC3 B", "label": "Yamaha MODX M7"}
          },
          "midi": {"input": "pa5x", "output": "modx"}
        }
        """,
        encoding="utf-8",
    )
    fake = FakeMidiBackend(
        ["Midihub MH-0CNQEC3 A"],
        ["Midihub MH-0CNQEC3 B"],
    )

    def poke():
        deadline = time.monotonic() + 1.0
        while fake._callback is None and time.monotonic() < deadline:
            time.sleep(0.01)
        fake.simulate_in([0x90, 60, 10])

    threading.Thread(target=poke, daemon=True).start()
    out, err = StringIO(), StringIO()
    rc = main(
        ["echo", "--config", str(cfg), "--once", "--seconds", "2"],
        backend_factory=lambda: fake,
        stdout=out,
        stderr=err,
    )
    assert rc == 0, err.getvalue()
    assert fake.opened_input == "Midihub MH-0CNQEC3 A"
    assert fake.opened_output == "Midihub MH-0CNQEC3 B"
    assert "Korg PA5X" in out.getvalue()


def test_ports_shows_aliases(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.json").write_text(
        '{"devices": {"pa5x": {"port": "Midihub A", "label": "Korg PA5X"}},'
        ' "midi": {"input": "pa5x"}}',
        encoding="utf-8",
    )
    fake = FakeMidiBackend(["Midihub MH-0CNQEC3 A"], ["Midihub MH-0CNQEC3 B"])
    out, err = StringIO(), StringIO()
    rc = main(["ports"], backend_factory=lambda: fake, stdout=out, stderr=err)
    assert rc == 0, err.getvalue()
    listed = out.getvalue()
    assert "pa5x" in listed
    assert "Korg PA5X" in listed
    assert "default in" in listed
