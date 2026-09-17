"""Slave to MIDI clock (PA5X Style). 24 pulses per quarter, 4/4 bars."""

from __future__ import annotations


CLOCK = 0xF8
START = 0xFA
CONTINUE = 0xFB
STOP = 0xFC
PPQN = 24
BEATS_PER_BAR = 4


def ticks_per_bar(beats: int = BEATS_PER_BAR, ppqn: int = PPQN) -> int:
    return beats * ppqn


class MidiClock:
    def __init__(self, *, beats: int = BEATS_PER_BAR) -> None:
        self.beats_per_bar = beats
        self.running = False
        self.tick = 0
        self.bpm: float | None = None
        self._last_clock_s: float | None = None

    @property
    def ticks_per_bar(self) -> int:
        return ticks_per_bar(self.beats_per_bar)

    @property
    def bar(self) -> int:
        """1-based bar since Start."""
        return (self.tick // self.ticks_per_bar) + 1

    @property
    def beat(self) -> int:
        """1-based beat in the bar."""
        return ((self.tick // PPQN) % self.beats_per_bar) + 1

    def bar_in_loop(self, length_ticks: int) -> int:
        if length_ticks <= 0:
            return 1
        t = self.tick % length_ticks
        return (t // self.ticks_per_bar) + 1

    def handle(self, status: int, wall_s: float) -> str | None:
        if status == CLOCK:
            self._update_bpm(wall_s)
            if self.running:
                self.tick += 1
                return "clock"
            return None
        if status == START:
            self.running = True
            self.tick = 0
            self._last_clock_s = None
            return "start"
        if status == CONTINUE:
            self.running = True
            return "continue"
        if status == STOP:
            self.running = False
            return "stop"
        return None

    def _update_bpm(self, wall_s: float) -> None:
        if self._last_clock_s is not None:
            dt = wall_s - self._last_clock_s
            if dt > 1e-4:
                inst = 60.0 / (dt * PPQN)
                if 20.0 <= inst <= 400.0:
                    if self.bpm is None:
                        self.bpm = inst
                    else:
                        self.bpm = (0.85 * self.bpm) + (0.15 * inst)
        self._last_clock_s = wall_s
