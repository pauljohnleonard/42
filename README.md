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

Copy `config.example.json` to `config.json` and put your port names in it if you do not want to type `--in` / `--out` every time. `config.json` is gitignored.

## M0 — ports talk

The engine lists ports and can echo a note. Echo is a **port test**, not the jam: live playing stays keyboard → synth. Capture later is listen-only.

```bash
python -m phrase_engine ports
```

Use **two** IAC buses (Audio MIDI Setup → IAC Driver → + bus). Same port in and out is a MIDI loop; the engine refuses that.

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
