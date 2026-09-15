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
| Phrase on disk | SMF + JSON sidecar (role, original chord, NTT, length, **sound targets**) |
| UI | Ugly is fine (terminal or one window) |
| Clock | Engine is master; optional MIDI clock out |
| Out | IAC (plugins) and/or Midihub DIN (hardware) |

MIDI in/out on a **dedicated thread**. UI never blocks that thread.

### Latency (do not put Python in the playing path)

**Budget:** live monitor path **under 10 ms**, **under 5 ms** if we can. Phrase playback can sit in the same band.

The scary number is **software thru**: keyboard → Python → synth. That is extra delay on top of DIN (~1 ms per note-on) and whatever the sound engine adds (hardware: tiny; Live: the audio buffer).

`python-rtmidi` is thin C++ under the hood. On a quiet thread, thru is often **1–5 ms**, which is playable. It gets ugly if thru runs on the GUI thread, the machine is busy, or the GC hiccups — then you feel a flap, not a constant lag.

**V1 rule:** Python **listens**, it does not sit between your fingers and the sound.

| What you are doing | Path |
|---|---|
| Play / monitor | Keyboard → synth **local** (or Midihub split to the module). You hear the box, not Python. |
| Capture | Same MIDI **copied** to the Mac (Midihub extra OUT, or USB). Engine timestamps notes. No extra hop in the audio path. |
| Phrase playback / NTT | Python **must** send those notes. That is a looped part, not your live touch. A few ms here is fine. |

Do not build “live bass through NTT as you play” in V0. Capture, then the loop is rewritten. Portable plugins: Live’s buffer is usually the bigger lag; keep IAC, keep buffer modest.

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
| PA5X Control (to Pa) | one IN channel | Start/stop, Variation/Fill PC, SongBook NRPN |

Capture can come from any input port. Output ports are named in a small config file (`iac`, `midihub a`, …).

---

## Playback brain: phrases over chord sequences

Two clocks, one rewrite.

| Clock | Job |
|---|---|
| **Phrase loop** | The captured riff (1 or 2 bars) repeats. Rhythm and velocities stay. |
| **Chord sequence** | `Am \| F \| C \| G` (or live chords on the bus). Harmony changes underneath. |

Each note-on in the loop: `out = rewrite(note, original_chord, current_chord, algo, wrap)`. Drums skip this (`none`). Chord MIDI out on 16 is just the current chord tones for MODX/Jupiter — not the phrase itself.

The Pa does **two** steps, not one:

1. **Chord Table** — pick which *recording* to use (they often recorded Cmaj **and** Cm). Closest quality wins.
2. **NTT** — rewrite that recording toward the chord you actually want (Cmaj → Cmaj7, or Cmaj → F#m7).

V1 can skip (1) and only do (2) from a single captured take. Quality jump later: capture maj **and** min of the same bass.

### What NTT actually does

Recorded in **Cmaj** (`C E G` as a mental triad; the riff may also have passing notes).

**Parallel** — shift with the **root**, keep the riff’s shape, then stay inside **Wrap Around** (if a note would leave the instrument’s sweet octave, drop/raise it). Good for bass and lines.

- **Root** — when the new chord needs extra tones (the ♭7 of a 7th chord), Korg **moves the old root** to that missing pitch. Cmaj (`C E G`) → C7: a `C` becomes nearest `Bb` → `C E G Bb` flavour.
- **Fifth** — same trick but it moves the old **fifth** (`G` → `Bb`). Different voicing, same chord.
- **No Transpose** (Parallel) — slide the whole shape to the new **key**, do not change quality. Intros that already contain a progression.

**Fixed / Chord** — **voice-lead**: move as few notes as possible, stay near the original register, prefer **common tones**. Cmaj `C E G` → Am might keep `C E` and move `G` → `A`. Pads, piano, strings. Ignores Wrap Around.

**Fixed / No Transpose** — do not follow chords. Drums use this idea without the name.

When the chord changes **under a held note**, Pa **Trigger**: cut / retrigger / **repitch** (glide). V1: retrigger is enough.

### A small rewrite we can actually code

Treat each captured pitch as a **role** in the original chord, then realise that role in the new chord. Passing notes keep their offset from the nearest chord tone.

```
src, dst = Cmaj, Fmaj
note C4 → role root → F4
note E4 → role 3rd → A4
note G4 → role 5th → C5
note D4 → passing (+2 from C) → G4   # still a 9th-ish above new root
then wrap into [low, high]
```

Maj → min: the **3rd** role becomes ♭3 (`E` → `Eb` if still in C). That is the whole point of not using naive “transpose by root interval” (which would leave a major third on a minor chord).

### Alternatives for the brain (pick one per slot)

| Brain | Idea | Use | Cost |
|---|---|---|---|
| **Root transpose only** | Add `dst.root - src.root` | Diatonic major-only, intros | Wrong 3rds on minor |
| **Chord-tone roles** (above) | Map 1–3–5–7 then tensions | **V1 default** for bass/harm | Simple, musical |
| **Korg-ish Parallel Root/Fifth** | Roles + “donor” pitch fills extensions | Closer to Pa Acc | Fiddly edge cases |
| **Nearest chord tone** (Fixed) | Each note snaps to closest pitch in `dst` | Pads, stabs | Can flatten a melody |
| **Scale quantize** | Fit to key/mode, not the triad | Hook / clarinet-ish lines | Off-chord on purpose |
| **Chord variations** | Extra capture for min / 7 | When one take sounds dumb | More tapping |
| **Bass grammar** | Force downbeat = root, keep rhythm | Safety net on ugly NTT | Less “your riff” |
| **Do nothing** | `none` | Drums, percussion Pads | — |

Do **not** start from a full Pa NTT clone or Guitar Mode. Three functions: `none`, `roles` (Parallel-ish), `nearest` (Fixed-ish). Wrap + retrigger. If a stolen Pa bass sounds wrong in F#m7, add a **min** variation, do not invent table 14.

Libraries later if we want: a tiny chord-quality table in Python is enough. `music21` is a thesis, not a jam.

---

## PA5X drums and Pads as the starter kit

Factory Drum tracks and Pads are the best drummer you already own. V1 should **play along with them**, not replace them on day one.

There are two different tricks. Do not mix them up.

### A — Pa stays the drummer (prefer this)

Pa is **clock master**. Engine **slaves**. You pick a Style (mute Acc/Bass if the engine will play those roles). Pads fire on the Pa; they already follow tempo.

| MIDI | What it actually does |
|---|---|
| Clock + Start/Stop from Pa | Engine bar 1 lines up with Style start. Capture bass/harm **on the grid**. |
| Control channel **to** Pa IN | Program Change **104** = Play/Stop Player 1. **83–86** = Var 1–4. **87–90** = Fill. |
| SongBook NRPN **to** Pa | Loads a **snapshot**: Style + the four Pads. Use **between** jams (same restart issue as live). |
| Load an arbitrary Pad from the library by MIDI | Not a first-class message. Pads come **with** the Style/SongBook, or you hit PAD 1–4. |

You do **not** need the engine to “load a Style” for this to work. Hand-select the Style, press Start, engine hears clock and records.

**Play:** Pa drums + Pad 1 looping. Engine captures a bass phrase in time. Chord bus still drives MODX/plugins. Clarinet on top.

### B — Steal the groove into a phrase (portable later)

Turn **Sty Drum** (and maybe Perc) **on** MIDI OUT. Engine records 1–2 bars on ch 10, NTT = none. Then that phrase can drive a kit plugin when the Pa is in the case.

Or: Style Edit → **Export SMF** and pull the Drum markers into the library — no realtime capture.

**Pads** use the same Export, from **Pad Edit**, not Style Edit. Cookbook below.

Do **not** send that Drum MIDI into the MODX Chord path. Midihub already filters: Chord 16 to synths; drums only to the Mac.

### Sound targets (Pa kit vs local)

Stolen MIDI is reusable **notes**. The *voice* is a separate pointer on the phrase.

When you capture from the Pa, store the **Bank MSB / LSB / Program** that was on that track (the mixer already shows that trio under the Sound name). Playback:

| Rig | Engine sends notes + that Bank/PC to… |
|---|---|
| Pa at home | PA5X MIDI IN on a channel assigned to a **Drum Kit / Pad / Acc sound** (Style **stopped**, Pa is a module). Same kit map = same experience. |
| Mac on a train | **Fallback** on the phrase: IAC → Live drum rack / GM kit / a named plugin preset. |

Config is just `output: pa5x` vs `output: local`. Same `.mid`, different port.

Do **not** run Style player drums **and** module playback of the stolen phrase at once — double kit.

Honest limit: Pa drum **note maps are not GM**. Fallback will be “a groove,” not “that factory kit,” unless you build one Live drum rack whose pads match the captured notes. Worth doing once for the kits you actually steal.

```json
{
  "role": "drums",
  "ntt": "none",
  "sound": {
    "pa5x": { "msb": 0, "lsb": 12, "program": 5, "channel": 10 },
    "local": { "port": "iac", "channel": 10, "preset": "live-drum-rack-pa-kit" }
  }
}
```

Bass, harm, and stolen Pads use the same shape.

### How to steal a Pad (MIDI + program)

A Pad is a **one-track mini-Style**. Factory Pads are protected: Pad Edit makes a temp copy; you only **Save Pad** if you edited. Export does not require saving.

**Sound (the program)**

1. Home mixer (or Mixer button).
2. **TRACK SELECT** until you are on **Keyboard / Pads**, not Style.
3. Pad 1–4: the Sound name is on that strip.
4. Under the name: **Bank Select MSB, LSB, Program Change**. Write those three numbers on the phrase JSON (`sound.pa5x`).

**Notes (the groove)**

1. Load the Style (or SongBook) so the four Pads you care about are the current set. Or pick a Pad from the Pad library onto one of the four slots first.
2. `REC/EDIT` → **Pad Edit** → choose Pad 1, 2, 3, or 4.
3. `MENU` → **Import/Export** → **Export SMF** → Execute. Same exporter as a Style; the file is SMF 0 with markers per Chord Variation.
4. Optional check: Pad Edit → **Pad Type & Control** — Loop vs One Shot; if it is a Drum-type loop, engine NTT = **none**; if it follows chords, stamp original chord and use **Fixed** or **Parallel Root**.

**Live capture (if you would rather not Export)**

MIDI OUT Channels: set **Pad 1** (etc.) to a channel, fire the PAD button, record that stream. The mixer trio above is still the program — the Pa may not send Bank/PC every time you hit PAD.

Then playback: same as stolen drums. Pa as module on a MIDI IN channel assigned to **Ply Pad 1** (or any channel that can hold that Sound), Style not also playing that Pad.

### Clock

M6 is not “engine always master.” For a Pa jam: **Clock Source on the engine = MIDI from Pa**. Pa **Clock Send** on. When you unplug the Pa, engine is master (tap tempo / internal).

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

**Pa variant:** Skip tapping. Slave to Pa clock, Start with the Style, leave drums on the Pa. M2 is then “engine knows bars”; the slot can stay empty.

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

Fixed bar size, quantise capture to the loop. **Slave to PA5X clock** when the Pa is the drummer. Internal / tap / MIDI clock **out** when the Pa is away (plugins, MODX arps).

**Play:** Bass capture starts on bar 1 of a Pa Style; loops stay glued when you hit Fill.

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

Config: Chord + parts to **IAC** (Mac portable) and/or **Midihub** (hardware). Same phrases. Each phrase has a **Pa sound** (Bank/PC) and a **local** fallback; `output: pa5x | local` picks the port.

**Play:** Stolen drum phrase on the Pa kit at home. Same file, Live drum rack, on the train. No double drums.

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

- [ ] Playback rewrite: `none` / chord-tone **roles** / **nearest** (Fixed); wrap; retrigger on chord change
- [ ] M1 chord bus + ch 16 out
- [ ] M2 drum loop (tap **or** slave to Pa clock)
- [ ] M3 bass NTT
- [ ] M4 harm NTT
- [ ] M5 four-slot clarinet jam
- [ ] M6 clock (slave to Pa / internal)
- [ ] M7 library
- [ ] M8 scenes
- [ ] M9 fill
- [ ] M10 IAC and Midihub + `output: pa5x | local`
- [ ] Steal Style drums: Export SMF + mixer MSB/LSB/PC
- [ ] Steal Pad: Pad Edit → Export SMF + TRACK SELECT Pads for MSB/LSB/PC
- [ ] Phrase JSON `sound.pa5x` and `sound.local` fallback

V2 (prettier UI, more NTT tables, iPad as brain) is **after** that list, not in it.
