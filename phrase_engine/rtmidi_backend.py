"""python-rtmidi backend. Imported only when talking to real ports."""

from __future__ import annotations

from collections.abc import Callable

from phrase_engine.midi import PortError, VIRTUAL_IN, VIRTUAL_OUT, resolve_port


def _explain_rtmidi(exc: BaseException) -> str:
    text = str(exc)
    lowered = text.lower()
    if "alsa" in lowered or "sequencer" in lowered or "/dev/snd/seq" in lowered:
        return (
            "No MIDI sequencer on this machine "
            f"({text}).\n"
            "On a Mac, CoreMIDI is enough — run: python -m phrase_engine ports"
        )
    return text


def _new_port(factory, what: str):
    try:
        return factory()
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        raise PortError(f"Could not open MIDI {what}: {_explain_rtmidi(e)}") from e


class RtMidiBackend:
    def __init__(self) -> None:
        try:
            import rtmidi
        except ImportError as e:
            raise PortError(
                "python-rtmidi is not installed. From the repo: pip install -e ."
            ) from e
        self._rtmidi = rtmidi
        self._in = None
        self._out = None

    def list_inputs(self) -> list[str]:
        midi = _new_port(self._rtmidi.MidiIn, "input")
        try:
            return list(midi.get_ports())
        finally:
            midi.close_port()

    def list_outputs(self) -> list[str]:
        midi = _new_port(self._rtmidi.MidiOut, "output")
        try:
            return list(midi.get_ports())
        finally:
            midi.close_port()

    def open_input(self, name: str | None, *, virtual: bool = False) -> str:
        midi = _new_port(self._rtmidi.MidiIn, "input")
        try:
            midi.ignore_types(sysex=True, timing=True, active_sense=True)
            if virtual:
                resolved = name or VIRTUAL_IN
                midi.open_virtual_port(resolved)
            else:
                if name is None:
                    raise PortError("input port name is required (or pass --virtual)")
                index, resolved = resolve_port(list(midi.get_ports()), name)
                midi.open_port(index)
        except PortError:
            midi.close_port()
            raise
        except Exception as e:
            midi.close_port()
            raise PortError(f"Could not open MIDI input: {_explain_rtmidi(e)}") from e
        self._in = midi
        return resolved

    def open_output(self, name: str | None, *, virtual: bool = False) -> str:
        midi = _new_port(self._rtmidi.MidiOut, "output")
        try:
            if virtual:
                resolved = name or VIRTUAL_OUT
                midi.open_virtual_port(resolved)
            else:
                if name is None:
                    raise PortError("output port name is required (or pass --virtual)")
                index, resolved = resolve_port(list(midi.get_ports()), name)
                midi.open_port(index)
        except PortError:
            midi.close_port()
            raise
        except Exception as e:
            midi.close_port()
            raise PortError(f"Could not open MIDI output: {_explain_rtmidi(e)}") from e
        self._out = midi
        return resolved

    def set_input_callback(self, callback: Callable) -> None:
        if self._in is None:
            raise PortError("open an input before setting a callback")
        self._in.set_callback(callback)

    def send(self, data: list[int]) -> None:
        if self._out is None:
            raise PortError("open an output before sending")
        self._out.send_message(data)

    def close(self) -> None:
        if self._in is not None:
            try:
                self._in.cancel_callback()
            except Exception:
                pass
            self._in.close_port()
            self._in = None
        if self._out is not None:
            self._out.close_port()
            self._out = None
