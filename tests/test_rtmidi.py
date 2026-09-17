from io import StringIO

import pytest

from phrase_engine.__main__ import main
from phrase_engine.midi import PortError


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
