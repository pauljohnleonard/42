from io import StringIO
import sys
import time

import pytest

from phrase_engine.__main__ import main
from phrase_engine.midi import MidiEngine, PortError, VIRTUAL_IN, VIRTUAL_OUT, resolve_port


def test_real_ports_command_does_not_traceback():
    """Headless VMs have no /dev/snd/seq; a Mac will just list CoreMIDI ports."""
    out, err = StringIO(), StringIO()
    rc = main(["ports"], stdout=out, stderr=err)
    assert rc in (0, 2)
    if rc == 0:
        assert "Inputs:" in out.getvalue()
        assert "Outputs:" in out.getvalue()
    else:
        combined = err.getvalue() + out.getvalue()
        assert "python-rtmidi is not installed" in combined or "MIDI" in combined
        assert "Traceback" not in combined


def test_rtmidi_backend_friendly_error_without_alsa():
    rtmidi = pytest.importorskip("rtmidi")
    from phrase_engine.rtmidi_backend import RtMidiBackend

    backend = RtMidiBackend()
    try:
        names = backend.list_inputs()
    except PortError as e:
        assert "sequencer" in str(e).lower() or "MIDI" in str(e)
        return
    assert isinstance(names, list)
    # imported so skipif has a reference if the backend never uses it
    assert rtmidi is not None


@pytest.mark.skipif(sys.platform != "darwin", reason="CoreMIDI virtual ports")
def test_virtual_echo_loopback():
    """M0 hear-a-note without IAC: send into PhraseEngine IN, read PhraseEngine OUT."""
    rtmidi = pytest.importorskip("rtmidi")
    from phrase_engine.rtmidi_backend import RtMidiBackend

    backend = RtMidiBackend()
    backend.open_input(VIRTUAL_IN, virtual=True)
    backend.open_output(VIRTUAL_OUT, virtual=True)
    engine = MidiEngine(backend, echo=True)
    engine.start()
    sender = rtmidi.MidiOut()
    receiver = rtmidi.MidiIn()
    got: list[list[int]] = []
    try:
        time.sleep(0.15)
        try:
            send_idx, _ = resolve_port(list(sender.get_ports()), VIRTUAL_IN)
            recv_idx, _ = resolve_port(list(receiver.get_ports()), VIRTUAL_OUT)
        except PortError as e:
            pytest.skip(str(e))
        receiver.ignore_types(sysex=True, timing=True, active_sense=True)
        receiver.set_callback(lambda event, _data: got.append(list(event[0])))
        sender.open_port(send_idx)
        receiver.open_port(recv_idx)
        sender.send_message([0x90, 60, 100])
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline and not got:
            time.sleep(0.01)
        assert got, "virtual echo did not return a note"
        assert got[0][:3] == [0x90, 60, 100]
    finally:
        engine.stop()
        sender.close_port()
        receiver.close_port()
