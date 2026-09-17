import threading
import time
from io import StringIO

from phrase_engine.clock import CLOCK, START, STOP, ticks_per_bar
from phrase_engine.loop import LoopSession
from phrase_engine.midi import FakeMidiBackend, MidiEngine, MidiMessage
from phrase_engine.phrase import NoteEvent, Phrase, PhrasePlayer, PhraseRecorder
from phrase_engine.__main__ import main


def _msg(*data: int, wall: float = 0.0) -> MidiMessage:
    return MidiMessage(data=data, wall_s=wall)


def test_record_one_bar_then_loop_plays():
    sent: list[list[int]] = []
    session = LoopSession(sent.append, bars=1)
    session.handle(_msg(START))
    session.handle(_msg(0x90, 60, 100))
    length = ticks_per_bar()
    for i in range(length):
        session.handle(_msg(CLOCK, wall=0.01 * (i + 1)))
    assert session.phase == "play"
    assert session.phrase is not None
    assert len(session.phrase.events) == 1
    assert session.phrase.events[0].note == 60
    ons = [m for m in sent if m and (m[0] & 0xF0) == 0x90]
    assert ons
    assert ons[0][1] == 60


def test_stop_silences_player():
    sent: list[list[int]] = []
    session = LoopSession(sent.append, bars=1)
    session.handle(_msg(START))
    session.handle(_msg(0x90, 64, 90))
    for i in range(ticks_per_bar()):
        session.handle(_msg(CLOCK, wall=0.01 * (i + 1)))
    sent.clear()
    session.handle(_msg(STOP))
    assert any(m[1] == 123 for m in sent if m and (m[0] & 0xF0) == 0xB0)


def test_player_note_off_at_duration():
    sent: list[list[int]] = []
    player = PhrasePlayer(sent.append)
    player.load(
        Phrase(
            length_ticks=96,
            events=(NoteEvent(tick=0, note=60, velocity=100, duration=24, channel=1),),
        )
    )
    player.on_abs_tick(0)
    assert [0x90, 60, 100] in sent
    sent.clear()
    player.on_abs_tick(24)
    assert [0x80, 60, 0] in sent


def test_recorder_stamps_tick():
    rec = PhraseRecorder(96)
    rec.arm()
    rec.note(_msg(0x90, 67, 80), tick=12)
    rec.note(_msg(0x80, 67, 0), tick=36)
    phrase = rec.finish(96)
    assert phrase.events == (
        NoteEvent(tick=12, note=67, velocity=80, duration=24, channel=1),
    )


def test_engine_clock_callback_does_not_echo():
    backend = FakeMidiBackend(["keys"], ["synth"])
    backend.open_input("keys")
    backend.open_output("synth")
    clocks: list[int] = []
    engine = MidiEngine(
        backend,
        echo=True,
        on_clock=lambda m: clocks.append(m.status),
    )
    engine.start()
    try:
        backend.simulate_in([0xF8])
        backend.simulate_in([0x90, 72, 10])
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline and backend.sent != [[0x90, 72, 10]]:
            time.sleep(0.01)
    finally:
        engine.stop()
    assert clocks == [0xF8]
    assert backend.sent == [[0x90, 72, 10]]


def test_loop_cli_records_on_start(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fake = FakeMidiBackend(["keys"], ["synth"])

    def poke():
        deadline = time.monotonic() + 1.0
        while fake._callback is None and time.monotonic() < deadline:
            time.sleep(0.01)
        fake.simulate_in([0xFA])
        fake.simulate_in([0x90, 60, 96])
        for _ in range(ticks_per_bar()):
            fake.simulate_in([0xF8])

    threading.Thread(target=poke, daemon=True).start()
    out, err = StringIO(), StringIO()
    rc = main(
        [
            "loop",
            "--in",
            "keys",
            "--out",
            "synth",
            "--bars",
            "1",
            "--once",
            "--seconds",
            "2",
        ],
        backend_factory=lambda: fake,
        stdout=out,
        stderr=err,
    )
    assert rc == 0, err.getvalue()
    assert "REC" in out.getvalue() or "LOOP" in out.getvalue()
    ons = [m for m in fake.sent if m and (m[0] & 0xF0) == 0x90]
    assert any(m[1] == 60 for m in ons)
