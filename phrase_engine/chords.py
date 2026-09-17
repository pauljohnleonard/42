"""M1 chord bus: name held notes, send those tones on MIDI channel 16."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from phrase_engine.midi import MidiMessage
from phrase_engine.notes import channel_of, note_name

CHORD_CHANNEL = 16  # 1–16, same as the Pa → Midihub chord path
_STATUS_ON = 0x90 | (CHORD_CHANNEL - 1)
_STATUS_OFF = 0x80 | (CHORD_CHANNEL - 1)
_STATUS_CC = 0xB0 | (CHORD_CHANNEL - 1)
CC_ALL_NOTES_OFF = 123

# Jazz-chart accidentals (F#m7, not Gb; Bb, not A#).
ROOT_NAMES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")

# Exact pitch-class sets relative to the root. More tones first so C6 ≠ C.
_QUALITIES: tuple[tuple[frozenset[int], str], ...] = (
    (frozenset({0, 2, 4, 7, 11}), "maj9"),
    (frozenset({0, 2, 4, 7, 10}), "9"),
    (frozenset({0, 2, 3, 7, 10}), "m9"),
    (frozenset({0, 4, 7, 10}), "7"),
    (frozenset({0, 3, 7, 10}), "m7"),
    (frozenset({0, 4, 7, 11}), "maj7"),
    (frozenset({0, 3, 7, 11}), "m(maj7)"),
    (frozenset({0, 3, 6, 10}), "m7b5"),
    (frozenset({0, 3, 6, 9}), "dim7"),
    (frozenset({0, 4, 8, 10}), "aug7"),
    (frozenset({0, 4, 7, 9}), "6"),
    (frozenset({0, 3, 7, 9}), "m6"),
    (frozenset({0, 5, 7, 10}), "7sus4"),
    (frozenset({0, 2, 4, 7}), "add9"),
    (frozenset({0, 4, 8}), "aug"),
    (frozenset({0, 3, 6}), "dim"),
    (frozenset({0, 4, 7}), ""),
    (frozenset({0, 3, 7}), "m"),
    (frozenset({0, 5, 7}), "sus4"),
    (frozenset({0, 2, 7}), "sus2"),
    (frozenset({0, 4, 10}), "7"),
    (frozenset({0, 3, 10}), "m7"),
    (frozenset({0, 7}), "5"),
    (frozenset({0}), ""),
)


@dataclass(frozen=True)
class Chord:
    root: int
    quality: str
    bass: int
    notes: tuple[int, ...]
    named: bool

    def label(self) -> str:
        if not self.notes:
            return "(none)"
        if not self.named:
            return " ".join(note_name(n) for n in sorted(self.notes))
        name = f"{ROOT_NAMES[self.root]}{self.quality}"
        if self.bass != self.root:
            return f"{name}/{ROOT_NAMES[self.bass]}"
        return name


def detect_chord(notes: list[int] | tuple[int, ...]) -> Chord | None:
    """Name a held set. None if nothing is down."""
    held = tuple(sorted({n for n in notes if 0 <= n <= 127}))
    if not held:
        return None
    pcs = {n % 12 for n in held}
    bass = held[0] % 12
    roots = [bass] + [p for p in sorted(pcs) if p != bass]
    for root in roots:
        intervals = frozenset((p - root) % 12 for p in pcs)
        for pattern, quality in _QUALITIES:
            if intervals == pattern:
                return Chord(
                    root=root,
                    quality=quality,
                    bass=bass,
                    notes=held,
                    named=True,
                )
    return Chord(root=bass, quality="", bass=bass, notes=held, named=False)


class ChordBus:
    """Track held notes, debounce, send the voicing on channel 16."""

    def __init__(
        self,
        send: Callable[[list[int]], None],
        *,
        on_change: Callable[[str], None] | None = None,
        debounce_s: float = 0.04,
        now: Callable[[], float] | None = None,
    ) -> None:
        self._send = send
        self._on_change = on_change
        self.debounce_s = debounce_s
        self._now = now or time.monotonic
        self._held: dict[int, int] = {}
        self._sounding: dict[int, int] = {}
        self._label = "(none)"
        self._dirty = False
        self._dirty_at = 0.0

    @property
    def label(self) -> str:
        return self._label

    def handle(self, msg: MidiMessage) -> None:
        data = msg.data
        if len(data) < 2:
            return
        status = data[0]
        if channel_of(status) is None:
            return
        kind = status & 0xF0
        note = data[1]
        if not 0 <= note <= 127:
            return
        if kind == 0x90:
            vel = data[2] if len(data) > 2 else 0
            if vel == 0:
                self._held.pop(note, None)
            else:
                self._held[note] = vel
        elif kind == 0x80:
            self._held.pop(note, None)
        else:
            return
        self._dirty = True
        self._dirty_at = self._now()

    def tick(self) -> None:
        if not self._dirty:
            return
        if self._now() - self._dirty_at < self.debounce_s:
            return
        self._commit()

    def panic(self) -> None:
        self._held.clear()
        self._dirty = False
        for note in list(self._sounding):
            self._note_off(note)
        self._sounding.clear()
        self._send([_STATUS_CC, CC_ALL_NOTES_OFF, 0])
        self._set_label("(none)")

    def _commit(self) -> None:
        self._dirty = False
        chord = detect_chord(list(self._held))
        wanted = dict(self._held)
        for note in list(self._sounding):
            if note not in wanted:
                self._note_off(note)
                del self._sounding[note]
        for note, vel in wanted.items():
            if note not in self._sounding:
                self._send([_STATUS_ON, note, max(1, min(vel, 127))])
                self._sounding[note] = vel
        self._set_label(chord.label() if chord else "(none)")

    def _note_off(self, note: int) -> None:
        self._send([_STATUS_OFF, note, 0])

    def _set_label(self, label: str) -> None:
        if label == self._label:
            return
        self._label = label
        if self._on_change is not None:
            self._on_change(label)
