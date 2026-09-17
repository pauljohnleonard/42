# Phrase engine

Python MIDI brain for jams: capture phrases, loop them, rewrite over chords, drive hardware (PA5X / MODX / Midihub) or plugins.

GitHub name can stay `42` or you can rename the repo in Settings.

## Spec (start here)

- **[Phrase-Engine-V1.md](Phrase-Engine-V1.md)** — milestones, MIDI, NTT/genomes, guard rail (get to the fun first)

## Hardware notes (same rig)

- [PA5X-Live-Jam-Reference.md](PA5X-Live-Jam-Reference.md)
- [PA5X-MODX-M7-MIDI-Setup.md](PA5X-MODX-M7-MIDI-Setup.md)
- [MODX-M7-Copy-Parts.md](MODX-M7-Copy-Parts.md)

## Install (Mac)

```bash
cd 42
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

`python-rtmidi` needs a working C++ toolchain. On a Mac that is Xcode command-line tools.

If install fails with `sem_timedwait` (Homebrew JACK is present), build CoreMIDI only, then the engine:

```bash
pip install python-rtmidi --config-settings=setup-args="-Djack=false"
pip install -e ".[dev]"
```

Copy `config.example.json` to `config.json`, or name the rig from live ports:

```bash
python -m phrase_engine setup
```

That writes aliases (`pa5x`, `modx`, …) and a **default MIDI in**. `--yes` skips the prompt. `config.json` is gitignored.

This machine: **PA5X on Midihub A**, **MODX M7 on Midihub B** (USB thru, no Midihub filter yet). After setup:

```bash
python -m phrase_engine ports
python -m phrase_engine listen
python -m phrase_engine chords
```

`--in pa5x` / `--out modx` override the defaults. Raw CoreMIDI names still work.

## M0 — ports talk

The engine lists ports and can echo a note. Echo is a **port test**, not the jam: live playing stays keyboard → synth. Capture later is listen-only.

```bash
python -m phrase_engine ports
```

Use **two** IAC buses. Same port in and out is a MIDI loop; the engine refuses that.

1. Audio MIDI Setup → Window → Show MIDI Studio
2. Double-click **IAC Driver** → check **Device is online**
3. Click **+** so you have **Bus 1** and **Bus 2** (one bus is not enough)

Then `python -m phrase_engine ports` should list `IAC Driver Bus 1` and `IAC Driver Bus 2`.

| From | To |
|---|---|
| Live / MODX MIDI out | **IAC Bus 1** (engine in) |
| **IAC Bus 2** (engine out) | Live instrument / another module |

```bash
python -m phrase_engine echo --in "IAC Driver Bus 1" --out "IAC Driver Bus 2"
```

**Play:** press a key. You should hear the plugin (or module) on Bus 2, and the terminal should print `ch1 C4 on vel …`. Ctrl+C stops.

Listen-only (the capture path — prints notes, sends nothing):

```bash
python -m phrase_engine listen --in "IAC Driver Bus 1"
```

`--virtual` opens CoreMIDI / ALSA ports named `PhraseEngine IN` and `PhraseEngine OUT` if you have no IAC yet.

```bash
python -m phrase_engine echo --virtual
```

`--channel 16` filters to one MIDI channel. `--once` / `--seconds N` are for scripts.

## M1 — chord bus

Hold a chord. The terminal shows `C`, `F#m7`, … and those tones go out on **channel 16**. The next chord replaces the previous (note-offs clean). Live playing still stays local — this is not Python thru.

```bash
python -m phrase_engine chords
```

Or `--in pa5x --out modx`. A pad (or the MODX) on the **out** port, MIDI channel **16**, follows the held chord. Live playing still stays local — this is not Python thru.

## M2 — loop on PA clock

Slave to PA5X MIDI clock. First **Start** records N bars (default 2); that take then loops to the config **out** port (IAC, not back into the Pa). Live sound stays on the Pa.

```bash
python -m phrase_engine loop
```

**Play:** Style running. Stop/Start so the engine sees Start. Play 2 bars. The terminal goes `REC` then `LOOP`. Hear the take on IAC Bus 2. `--bars 1` for a shorter take. `--channel` if Style MIDI is too busy.

## Tests

```bash
pytest
```

No hardware required. MIDI is faked on a dedicated thread, same as the real engine.

## Layout

```
phrase_engine/     MIDI thread, CLI
tests/
config.example.json
phrases/           library later (gitignored)
scenes/
```
