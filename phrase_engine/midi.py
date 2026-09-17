"""MIDI I/O on a dedicated thread.

The live playing path stays local (keyboard → synth). This thread is for
listing ports, the M0 echo *test*, and later capture / phrase playback.
"""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from typing import Callable, Protocol

from phrase_engine.notes import channel_of, format_message, is_channel_voice

VIRTUAL_IN = "PhraseEngine IN"
VIRTUAL_OUT = "PhraseEngine OUT"


class MidiError(RuntimeError):
    pass


class PortError(MidiError):
    pass


@dataclass(frozen=True)
class MidiMessage:
    data: tuple[int, ...]
    wall_s: float
    delta_s: float = 0.0

    @property
    def status(self) -> int:
        return self.data[0] if self.data else 0


class MidiBackend(Protocol):
    def list_inputs(self) -> list[str]: ...

    def list_outputs(self) -> list[str]: ...

    def open_input(self, name: str | None, *, virtual: bool = False) -> str: ...

    def open_output(self, name: str | None, *, virtual: bool = False) -> str: ...

    def set_input_callback(self, callback: Callable) -> None: ...

    def send(self, data: list[int]) -> None: ...

    def close(self) -> None: ...


def resolve_port(ports: list[str], query: str) -> tuple[int, str]:
    """Match a port by exact name, then unique case-insensitive substring."""
    q = (query or "").strip()
    if not q:
        raise PortError("MIDI port name is empty")
    if not ports:
        raise PortError(f"no MIDI ports available (looked for {q!r})")

    for i, name in enumerate(ports):
        if name == q:
            return i, name

    lowered = q.lower()
    exact_ci = [(i, name) for i, name in enumerate(ports) if name.lower() == lowered]
    if len(exact_ci) == 1:
        return exact_ci[0]
    if len(exact_ci) > 1:
        raise PortError(_ambiguous(q, [n for _, n in exact_ci]))

    partial = [(i, name) for i, name in enumerate(ports) if lowered in name.lower()]
    if len(partial) == 1:
        return partial[0]
    if len(partial) > 1:
        raise PortError(_ambiguous(q, [n for _, n in partial]))
    raise PortError(_missing(q, ports))


def _ambiguous(query: str, matches: list[str]) -> str:
    listed = "\n".join(f"  - {n}" for n in matches)
    return f"MIDI port {query!r} is ambiguous. Matches:\n{listed}"


def _missing(query: str, ports: list[str]) -> str:
    listed = "\n".join(f"  - {n}" for n in ports) if ports else "  (none)"
    return f"No MIDI port matching {query!r}. Available:\n{listed}"


def format_port_list(inputs: list[str], outputs: list[str]) -> str:
    def block(title: str, names: list[str]) -> str:
        if not names:
            return f"{title}:\n  (none)"
        return f"{title}:\n" + "\n".join(f"  [{i}] {n}" for i, n in enumerate(names))

    return f"{block('Inputs', inputs)}\n{block('Outputs', outputs)}"


class MidiEngine:
    """Drain incoming MIDI on a dedicated thread. Optionally echo to output."""

    def __init__(
        self,
        backend: MidiBackend,
        *,
        echo: bool = False,
        channel: int | None = None,
        on_message: Callable[[MidiMessage], None] | None = None,
    ) -> None:
        if channel is not None and not 1 <= channel <= 16:
            raise MidiError("channel must be 1–16")
        self.backend = backend
        self.echo = echo
        self.channel = channel
        self._on_message = on_message
        self._incoming: queue.SimpleQueue[MidiMessage | None] = queue.SimpleQueue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="midi", daemon=True)
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self.backend.set_input_callback(self._on_rtmidi)
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="midi", daemon=True)
        self._thread.start()
        self._started = True

    def stop(self, timeout: float = 1.0) -> None:
        if not self._started:
            self.backend.close()
            return
        self._stop.set()
        self._incoming.put(None)
        self._thread.join(timeout=timeout)
        self.backend.close()
        self._started = False

    def push(self, data: list[int] | tuple[int, ...], *, delta_s: float = 0.0) -> None:
        """Test helper: inject a message as if it arrived from MIDI in."""
        self._incoming.put(
            MidiMessage(data=tuple(int(b) for b in data), wall_s=time.monotonic(), delta_s=delta_s)
        )

    def _on_rtmidi(self, event: tuple[list[int], float], _data: object = None) -> None:
        message, delta = event
        self._incoming.put(
            MidiMessage(
                data=tuple(int(b) for b in message),
                wall_s=time.monotonic(),
                delta_s=float(delta),
            )
        )

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                item = self._incoming.get(timeout=0.05)
            except queue.Empty:
                continue
            if item is None:
                break
            self._handle(item)

    def _handle(self, msg: MidiMessage) -> None:
        if not msg.data:
            return
        status = msg.status
        if not is_channel_voice(status):
            return
        if self.channel is not None and channel_of(status) != self.channel:
            return
        if self.echo:
            self.backend.send(list(msg.data))
        if self._on_message is not None:
            self._on_message(msg)


class FakeMidiBackend:
    """In-memory backend for tests. No python-rtmidi required."""

    def __init__(
        self,
        inputs: list[str] | None = None,
        outputs: list[str] | None = None,
    ) -> None:
        self.inputs = list(inputs or ["Fake In"])
        self.outputs = list(outputs or ["Fake Out"])
        self.sent: list[list[int]] = []
        self.opened_input: str | None = None
        self.opened_output: str | None = None
        self.closed = False
        self._callback: Callable | None = None

    def list_inputs(self) -> list[str]:
        return list(self.inputs)

    def list_outputs(self) -> list[str]:
        return list(self.outputs)

    def open_input(self, name: str | None, *, virtual: bool = False) -> str:
        if virtual:
            self.opened_input = name or VIRTUAL_IN
            if self.opened_input not in self.inputs:
                self.inputs.append(self.opened_input)
            return self.opened_input
        if name is None:
            raise PortError("input port name is required")
        _, resolved = resolve_port(self.inputs, name)
        self.opened_input = resolved
        return resolved

    def open_output(self, name: str | None, *, virtual: bool = False) -> str:
        if virtual:
            self.opened_output = name or VIRTUAL_OUT
            if self.opened_output not in self.outputs:
                self.outputs.append(self.opened_output)
            return self.opened_output
        if name is None:
            raise PortError("output port name is required")
        _, resolved = resolve_port(self.outputs, name)
        self.opened_output = resolved
        return resolved

    def set_input_callback(self, callback: Callable) -> None:
        self._callback = callback

    def send(self, data: list[int]) -> None:
        self.sent.append(list(data))

    def simulate_in(self, data: list[int], delta_s: float = 0.0) -> None:
        if self._callback is None:
            raise MidiError("simulate_in before the engine started")
        self._callback((list(data), delta_s), None)

    def close(self) -> None:
        self.closed = True
        self._callback = None
