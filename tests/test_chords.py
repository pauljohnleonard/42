from phrase_engine.chords import CHORD_CHANNEL, ChordBus, detect_chord
from phrase_engine.midi import MidiMessage


def test_detect_c_major():
    chord = detect_chord([60, 64, 67])
    assert chord is not None
    assert chord.label() == "C"


def test_detect_g7():
    chord = detect_chord([67, 71, 74, 77])
    assert chord is not None
    assert chord.label() == "G7"


def test_detect_fsharp_m7():
    chord = detect_chord([66, 69, 73, 76])  # F# A C# E
    assert chord is not None
    assert chord.label() == "F#m7"


def test_detect_inversion():
    chord = detect_chord([64, 67, 72])  # E G C
    assert chord is not None
    assert chord.label() == "C/E"


def test_detect_empty():
    assert detect_chord([]) is None


def test_detect_unknown_cluster():
    chord = detect_chord([60, 61, 62])
    assert chord is not None
    assert chord.named is False
    assert "C4" in chord.label()


def test_am7_vs_c6_uses_bass():
    assert detect_chord([57, 60, 64, 67]).label() == "Am7"
    assert detect_chord([60, 64, 67, 69]).label() == "C6"


class _Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def _msg(*data: int) -> MidiMessage:
    return MidiMessage(data=data, wall_s=0.0)


def test_bus_sends_held_tones_on_ch16():
    sent: list[list[int]] = []
    labels: list[str] = []
    clock = _Clock()
    bus = ChordBus(sent.append, on_change=labels.append, debounce_s=0.04, now=clock)

    bus.handle(_msg(0x90, 60, 96))
    bus.handle(_msg(0x90, 64, 80))
    bus.handle(_msg(0x90, 67, 70))
    bus.tick()
    assert sent == []

    clock.t = 0.04
    bus.tick()
    ons = [m for m in sent if m[0] == 0x9F]
    assert {tuple(m) for m in ons} == {(0x9F, 60, 96), (0x9F, 64, 80), (0x9F, 67, 70)}
    assert labels == ["C"]
    assert CHORD_CHANNEL == 16


def test_bus_replaces_chord_with_clean_offs():
    sent: list[list[int]] = []
    clock = _Clock()
    bus = ChordBus(sent.append, debounce_s=0.0, now=clock)

    bus.handle(_msg(0x90, 60, 96))
    bus.handle(_msg(0x90, 64, 96))
    bus.handle(_msg(0x90, 67, 96))
    bus.tick()
    sent.clear()

    bus.handle(_msg(0x80, 60, 0))
    bus.handle(_msg(0x80, 64, 0))
    bus.handle(_msg(0x80, 67, 0))
    bus.handle(_msg(0x90, 65, 100))
    bus.handle(_msg(0x90, 69, 100))
    bus.handle(_msg(0x90, 72, 100))
    bus.tick()

    offs = {m[1] for m in sent if m[0] == 0x8F}
    ons = {m[1] for m in sent if m[0] == 0x9F}
    assert offs == {60, 64, 67}
    assert ons == {65, 69, 72}


def test_bus_panic_silences():
    sent: list[list[int]] = []
    clock = _Clock()
    bus = ChordBus(sent.append, debounce_s=0.0, now=clock)
    bus.handle(_msg(0x90, 60, 96))
    bus.tick()
    sent.clear()
    bus.panic()
    assert [0x8F, 60, 0] in sent
    assert [0xBF, 123, 0] in sent
    assert bus.label == "(none)"


def test_note_on_vel_zero_is_off():
    sent: list[list[int]] = []
    labels: list[str] = []
    clock = _Clock()
    bus = ChordBus(sent.append, on_change=labels.append, debounce_s=0.0, now=clock)
    bus.handle(_msg(0x90, 60, 96))
    bus.tick()
    bus.handle(_msg(0x90, 60, 0))
    bus.tick()
    assert labels == ["C", "(none)"]
