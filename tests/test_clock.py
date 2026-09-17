from phrase_engine.clock import CLOCK, START, STOP, MidiClock, ticks_per_bar


def test_start_is_bar1_beat1():
    clock = MidiClock()
    assert clock.handle(START, 0.0) == "start"
    assert clock.running
    assert clock.tick == 0
    assert clock.bar == 1
    assert clock.beat == 1


def test_one_bar_is_96_clocks():
    clock = MidiClock()
    clock.handle(START, 0.0)
    for i in range(ticks_per_bar()):
        clock.handle(CLOCK, 0.02 * (i + 1))
    assert clock.tick == 96
    assert clock.bar == 2
    assert clock.beat == 1


def test_bpm_from_clock_spacing():
    clock = MidiClock()
    clock.handle(START, 10.0)
    # 120 bpm → 24 clocks/beat → 48 clocks/s → 20.833 ms
    t = 10.0
    for _ in range(30):
        t += 60.0 / (120.0 * 24)
        clock.handle(CLOCK, t)
    assert clock.bpm is not None
    assert 110 < clock.bpm < 130


def test_stop_freezes_tick():
    clock = MidiClock()
    clock.handle(START, 0.0)
    clock.handle(CLOCK, 0.02)
    clock.handle(STOP, 0.04)
    frozen = clock.tick
    clock.handle(CLOCK, 0.06)
    assert not clock.running
    assert clock.tick == frozen
