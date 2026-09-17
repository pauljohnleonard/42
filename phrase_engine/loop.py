"""M2: capture N bars on the PA clock, then loop that phrase."""

from __future__ import annotations

from collections.abc import Callable

from phrase_engine.chords import ChordBus
from phrase_engine.clock import MidiClock, ticks_per_bar
from phrase_engine.midi import MidiMessage
from phrase_engine.phrase import Phrase, PhrasePlayer, PhraseRecorder


class LoopSession:
    def __init__(
        self,
        send: Callable[[list[int]], None],
        *,
        bars: int = 2,
        on_status: Callable[[str], None] | None = None,
    ) -> None:
        if bars < 1:
            raise ValueError("bars must be >= 1")
        self.bars = bars
        self.length_ticks = bars * ticks_per_bar()
        self.clock = MidiClock()
        self.recorder = PhraseRecorder(self.length_ticks)
        self.player = PhrasePlayer(send)
        self.phrase: Phrase | None = None
        self.phase = "wait"
        self._on_status = on_status
        self._last_beat: tuple[str, int, int] | None = None
        self._chord = "(none)"
        self._chords = ChordBus(lambda _data: None, on_change=self._chord_changed, debounce_s=0.04)

    def handle(self, msg: MidiMessage) -> None:
        if not msg.data:
            return
        status = msg.status
        kind = self.clock.handle(status, msg.wall_s)
        if kind == "start":
            self._on_start()
        elif kind == "stop":
            self._on_stop()
        elif kind == "clock":
            self._on_clock()
        elif kind == "continue":
            self._emit()
        if kind is None and status < 0xF0:
            self._chords.handle(msg)
            self._chords.tick()
            if self.phase == "rec":
                self.recorder.note(msg, self.clock.tick)

    def tick(self) -> None:
        self._chords.tick()

    def panic(self) -> None:
        self.player.silence()

    def _on_start(self) -> None:
        if self.phrase is None:
            self.phase = "rec"
            self.recorder.arm()
            self.player.silence()
        else:
            self.phase = "play"
            self.player.load(self.phrase)
            self.player.on_abs_tick(0)
        self._last_beat = None
        self._emit()

    def _on_stop(self) -> None:
        if self.phase == "rec" and self.clock.tick >= ticks_per_bar():
            bars = max(1, self.clock.tick // ticks_per_bar())
            self.recorder.length_ticks = bars * ticks_per_bar()
            self.phrase = self.recorder.finish(self.recorder.length_ticks, self._chord)
            self.length_ticks = self.phrase.length_ticks
            self.bars = bars
        self.phase = "wait" if self.phrase is None else "armed"
        self.player.silence()
        self._last_beat = None
        self._emit()

    def _on_clock(self) -> None:
        if self.phase == "rec" and self.clock.tick >= self.length_ticks:
            self.phrase = self.recorder.finish(self.length_ticks, self._chord)
            self.phase = "play"
            self.player.load(self.phrase)
            self.player.on_abs_tick(self.clock.tick)
        elif self.phase == "play":
            self.player.on_abs_tick(self.clock.tick)
        self._emit()

    def _chord_changed(self, label: str) -> None:
        self._chord = label
        if self.phase == "rec" and label != "(none)":
            self.recorder.chord = label
        self._emit(force=True)

    def _emit(self, *, force: bool = False) -> None:
        if self._on_status is None:
            return
        beat_key = (self.phase, self.clock.bar, self.clock.beat)
        if not force and beat_key == self._last_beat:
            return
        self._last_beat = beat_key
        self._on_status(self.status_line())

    def status_line(self) -> str:
        bpm = f"{self.clock.bpm:.0f} bpm" if self.clock.bpm else "no tempo yet"
        chord = f"  {self._chord}" if self._chord and self._chord != "(none)" else ""
        if not self.clock.running:
            if self.phrase is None:
                return f"waiting for Start (stop/start the Style)  {bpm}"
            return (
                f"armed {self.bars} bar loop "
                f"({len(self.phrase.events)} notes)  {bpm}  Start to play"
            )
        if self.phase == "rec":
            rec_bar = min(self.bars, self.clock.bar)
            return f"REC  bar {rec_bar}/{self.bars} beat {self.clock.beat}  {bpm}{chord}"
        loop_bar = self.clock.bar_in_loop(self.length_ticks)
        return f"LOOP bar {loop_bar}/{self.bars} beat {self.clock.beat}  {bpm}{chord}"
