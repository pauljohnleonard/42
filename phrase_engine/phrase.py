"""Captured phrase on a MIDI-clock grid, and playback of that loop."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from phrase_engine.midi import MidiMessage
from phrase_engine.notes import channel_of


@dataclass(frozen=True)
class NoteEvent:
    tick: int
    note: int
    velocity: int
    duration: int
    channel: int


@dataclass
class Phrase:
    length_ticks: int
    events: tuple[NoteEvent, ...]
    chord: str | None = None


class PhraseRecorder:
    def __init__(self, length_ticks: int) -> None:
        if length_ticks <= 0:
            raise ValueError("length_ticks must be positive")
        self.length_ticks = length_ticks
        self.active = False
        self.events: list[NoteEvent] = []
        self._held: dict[int, tuple[int, int, int]] = {}
        self.chord: str | None = None

    def arm(self) -> None:
        self.active = True
        self.events.clear()
        self._held.clear()
        self.chord = None

    def note(self, msg: MidiMessage, tick: int) -> None:
        if not self.active or tick >= self.length_ticks:
            return
        data = msg.data
        if len(data) < 2:
            return
        status = data[0]
        kind = status & 0xF0
        note = data[1]
        ch = channel_of(status) or 1
        if kind == 0x90:
            vel = data[2] if len(data) > 2 else 0
            if vel == 0:
                self._off(note, tick)
            else:
                self._held[note] = (tick, vel, ch)
        elif kind == 0x80:
            self._off(note, tick)

    def finish(self, end_tick: int, chord: str | None = None) -> Phrase:
        for note in list(self._held):
            self._off(note, end_tick)
        self.active = False
        label = chord if chord and chord != "(none)" else self.chord
        return Phrase(
            length_ticks=self.length_ticks,
            events=tuple(self.events),
            chord=label,
        )

    def _off(self, note: int, tick: int) -> None:
        start = self._held.pop(note, None)
        if start is None:
            return
        start_tick, vel, ch = start
        dur = max(1, tick - start_tick)
        if start_tick + dur > self.length_ticks:
            dur = self.length_ticks - start_tick
        if dur <= 0:
            return
        self.events.append(
            NoteEvent(tick=start_tick, note=note, velocity=vel, duration=dur, channel=ch)
        )


@dataclass
class PhrasePlayer:
    send: Callable[[list[int]], None]
    phrase: Phrase | None = None
    muted: bool = False
    _last_tick: int | None = field(default=None, init=False)
    _sounding: set[tuple[int, int]] = field(default_factory=set, init=False)

    def load(self, phrase: Phrase) -> None:
        self.silence()
        self.phrase = phrase
        self._last_tick = None

    def on_abs_tick(self, abs_tick: int) -> None:
        if self.phrase is None or self.phrase.length_ticks <= 0:
            return
        t = abs_tick % self.phrase.length_ticks
        if self._last_tick == t:
            return
        prev = self._last_tick
        self._last_tick = t
        if prev is not None and t < prev:
            self.silence()
        if self.muted:
            return
        for ev in self.phrase.events:
            off_at = ev.tick + ev.duration
            if off_at > self.phrase.length_ticks:
                off_at = self.phrase.length_ticks
            if off_at == t:
                self._off(ev.channel, ev.note)
        for ev in self.phrase.events:
            if ev.tick == t:
                self._on(ev)

    def silence(self) -> None:
        for ch, note in list(self._sounding):
            self._off(ch, note)
        self._sounding.clear()
        self.send([0xB0, 123, 0])

    def _on(self, ev: NoteEvent) -> None:
        status = 0x90 | (ev.channel - 1)
        self.send([status, ev.note, max(1, min(ev.velocity, 127))])
        self._sounding.add((ev.channel, ev.note))

    def _off(self, channel: int, note: int) -> None:
        status = 0x80 | (channel - 1)
        self.send([status, note, 0])
        self._sounding.discard((channel, note))
