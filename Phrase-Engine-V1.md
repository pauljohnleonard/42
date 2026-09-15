# Phrase engine V1 — milestones

A standalone Python MIDI brain: capture phrases, loop them, rewrite harmony like a Pa style, send chords (and parts) to hardware or plugins.

Not a DAW. Not Max. Not Ableton scripting. Live/Logic stay optional hosts for *virtual* synths.

Related hardware jam: [PA5X-Live-Jam-Reference.md](PA5X-Live-Jam-Reference.md), [PA5X-MODX-M7-MIDI-Setup.md](PA5X-MODX-M7-MIDI-Setup.md).

---

## What V1 is

Four **slots** (drums, bass, harm, hook) + a **chord bus** + a **phrase library** + **scenes**.

| You do this | What should happen |
|---|---|
| Tap or play a phrase, hit capture | Slot loops it |
| Change chord (keys, or a loaded progression) | Bass/harm rewrite; drums stay put |
| Load a phrase from disk | Same slot, same NTT rules |
| Recall a scene | Four slots + a chord pattern |
| Play clarinet | Hands off: engine is the band |

**Chord MIDI out** on channel **16** (same as the Pa → Midihub plan). Synths and plugins do not care who wrote the chord.

---

## What V1 is not

- Audio engine or soft-synth host (M1 + Live/AUM do that)
- Full Pa NTT / Guitar Mode
- Piano-roll editor
- Running on the iPad (iPad = module or controller; brain = Mac)

Three NTT tables only: **none** (drums), **Parallel Root** (bass / lines), **Fixed Chord** (pads / stabs). Hook defaults to none or Parallel Root — pick when we hear it.

---

## Stack

| Piece | Choice |
|---|---|
| Language | Python 3 |
| MIDI | `python-rtmidi` |
| Phrase on disk | SMF + JSON sidecar (role, original chord, NTT, length in bars) |
| UI | Ugly is fine (terminal or one window) |
| Clock | Engine is master; optional MIDI clock out |
| Out | IAC (plugins) and/or Midihub DIN (hardware) |

MIDI in/out on a **dedicated thread**. UI never blocks that thread.

---

## MIDI sketch (keep it boring)

| Bus | Channel | Job |
|---|---|---|
| Chord | **16** | Chord tones to MODX / Jupiter / plugins (same as today) |
| Drums | 10 | Kit |
| Bass | 2 | Bass module or plugin |
| Harm | 3 | Pad / stab |
| Hook | 4 | Extra line |
| Chord in (optional) | 1 | Keys that *set* the bus, not a slot |

Capture can come from any input port. Output ports are named in a small config file (`iac`, `midihub a`, …).

---

## First milestones (in order)

Each milestone is done when you can **play** the test, not when the code exists.

### M0 — Ports talk

Python lists MIDI ports, echoes notes in → out.

**Play:** Press a key on the MODX (or IAC from Live). Hear it on a plugin or another module.

### M1 — Chord bus

Hold a chord on the keyboard → bus shows `C`, `F#m7`, etc. Engine sends those tones on **ch 16**. Next chord replaces the previous (note-offs clean).

**Play:** Jupiter or a pad plugin follows your left hand. No slots yet.

### M2 — Drum slot (loop, no NTT)

Arm drums, play 1 or 2 bars, capture, loop. Start / stop / mute. Length is in **bars**, not ticks you think about.

**Play:** A tapped groove keeps going while you drink tea.

### M3 — Bass slot + Parallel Root

Capture bass while the bus is e.g. C. Stamp **original chord = C**. Change bus to F or Am; riff transposes in a Pa-ish way (root-based). Wrap so it does not dive off the instrument.

**Play:** Same riff, new chord, still sounds like bass.

### M4 — Harm slot + Fixed Chord

Capture a stab or pad voicing. Rewrite with **Fixed** (move as few notes as possible).

**Play:** Pad follows chords without jumping an octave every change.

### M5 — Four slots + clarinet test

Drums + bass + harm + hook together. Per-slot rec / play / mute. Chord out still on 16.

**Play:** Build a jam from nothing, walk away with the clarinet, harmony still changes from the bus (keys or a *single* looping chord phrase if we already have it — otherwise change chords with one hand / a pedal).

This is the go/no-go. If this is not more fun than Pa Matrix + a factory Style, stop or narrow. Do not start a library for a boring loop.

---

## Rest of V1 (after M5 is fun)

### M6 — Clock you can trust

Fixed bar size, quantise capture to the loop, optional MIDI clock out so MODX arps / Live sync. Tap tempo.

**Play:** Slot loops stay with the click; a plugin arp locks if you want it.

### M7 — Phrase library

Save slot → `phrases/<name>.mid` + `.json`. Browse and load into a slot. Tags optional (role is enough).

**Play:** Last week’s bass in this week’s drum groove.

### M8 — Scenes

A scene = four phrase IDs + chord pattern (list of bars: `Am | F | C | G`). Recall does not stop like a Pa SongBook reload if we can help it — finish the bar, then switch (Loop All instinct).

**Play:** Pad 1 vs pad 2 feels like the Pa Matrix, but the band is *your* phrases.

### M9 — Fill (thin)

One fill phrase per slot or one global fill slot. Trigger → plays once → back to the loop.

**Play:** Clarinet still going; you stamp a fill with a pad/foot.

### M10 — Two outputs, one brain

Config: Chord + parts to **IAC** (Mac portable) and/or **Midihub** (hardware). Same phrases.

**Play:** Same scene on headphones in a hotel, then on MODX + Jupiter at home.

---

## Suggested repo layout (when code starts)

```
phrase-engine/
  README.md          (how to run)
  config.example.json
  engine/            (clock, chord bus, ntt, slots)
  midi/              (rtmidi thread)
  phrases/           (user library, gitignored except examples)
  scenes/
```

Milestones M0–M2 can live as a single `python -m phrase_engine` before the folder gets fancy.

---

## Order of attack

Do **M0 → M5** on the Mac with IAC + one Live instrument (or one hardware module). Do not wire all four synths until M3 sounds like bass.

Library (M7) and scenes (M8) are what we called V1 in conversation. They are useless without M5.

---

## Done for V1

- [ ] M0 echo
- [ ] M1 chord bus + ch 16 out
- [ ] M2 drum loop
- [ ] M3 bass NTT
- [ ] M4 harm NTT
- [ ] M5 four-slot clarinet jam
- [ ] M6 clock
- [ ] M7 library
- [ ] M8 scenes
- [ ] M9 fill
- [ ] M10 IAC and Midihub

V2 (prettier UI, more NTT tables, iPad as brain) is **after** that list, not in it.
