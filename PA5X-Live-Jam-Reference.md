# PA5X live jam reference

How you want to use the Korg PA5X: remixed Styles, Pads as extra players, Matrix Chord Sequences with **Loop All** so the current progression finishes before the next one starts.

Print this or keep it on a phone at the keyboard.

Related:

- [PA5X-MODX-M7-MIDI-Setup.md](PA5X-MODX-M7-MIDI-Setup.md) — PA5X chords driving MODX arps
- [MODX-M7-Copy-Parts.md](MODX-M7-Copy-Parts.md) — stealing a Part from another MODX Performance
- [Phrase-Engine-V1.md](Phrase-Engine-V1.md) — optional software brain (phrases + NTT); not required for the Pa jam

---

## Goal

Live improv, not “play a finished song.”

| Layer | Job |
|---|---|
| **Style** (tweaked User Style) | The band: drums, bass, acc |
| **Pads** (1–4) | Extra players on top (loops, hits, extra grooves) |
| **Chord Sequences** on the **Matrix** | Harmony. Jam on sequence A until it **ends**, then B starts |
| **Keyboard Sets** | Your right/left-hand sounds |
| **SongBook** | Recall a whole setup **between** jams, not mid-solo |

Do **not** use Event Edit or MIDI-to-Style as the main path. Copy tracks, change Sounds, assign Pads.

---

## The pieces (do not mix them up)

| Thing | What it actually does |
|---|---|
| **Style** | Looping band that **follows chords** |
| **Pads** (4 PAD buttons) | Extra grooves/hits. They **follow** chords. They do **not** choose the chord. |
| **Chord Sequence** | A recorded progression (Am–F–C–G…). **This** drives the Style when you are not playing chords. |
| **Matrix** (16 rubber pads) | Can start **different Chord Sequences** (and other jobs) |
| **SongBook Entry** | Snapshot: Style + Keyboard Sets + Pads + which sequence is loaded. Changing Entry **stops** the chord sequencer. |

SongBook mid-jam is why the sequence died and needed a restart. Harmony changes belong on the **Matrix**, with the Style left running.

---

## 1. Remix Styles (high level)

Factory Styles cannot be overwritten. Work in **User**.

### Steal tracks

1. Load the Style you want as the **body** on Player 1.
2. **REC/EDIT** → **Style Edit** → **MENU** → **Style Copy**.
3. Copy **Drum** (and/or Bass, Acc…) from another Style.
4. Mute Perc / extra Acc if it is busy.
5. Page menu → **Save Style** into User.

Player 2 is useful to audition a donor Style. **Tempo Lock** keeps both in time while you shop for grooves.

Same time signature helps. After a copy, check MFX sends if drums/perc sound soaked in the wrong effect.

### Change instruments

Home mixer → **TRACK SELECT** until it says **Style** (not Keyboard) → tap a track Sound → pick a new one → **Save Style**.

That is the whole-Style sound. Keyboard Upper/Lower is **Save Keyboard Set**, not Save Style.

If a Fill snaps the Sound back, the pattern contains a Program Change. Ignore that until you care; most remixes never need Event Edit.

### Skip

- Style Creator Bot (MIDI → Style) unless you like a rare result
- Event Edit except for one wrong note
- Export SMF → DAW unless you are writing a new groove from scratch

---

## 2. Pads = additional players

The four **PAD** buttons are extra clips on top of the band, not another Style and not the chord engine.

| Kind | Use |
|---|---|
| Loop | Shaker, congas, synth pulse, extra guitar pattern |
| One-shot | Crash, stab, FX |

They transpose with the **current chord** (from your hand, Chord Memory, or a Chord Sequence).

**Setup**

1. Load your User Style.
2. Assign Pads 1–4 from the Pad library (Home Pad area / Pad select).
3. Set Pad mix on the Mixer (Pad tracks).
4. **Save Style** and/or the SongBook Entry so the four Pads stick.

Live: Style running, fire Pad 1 for extra motion, Pad 2 for a stab. Turning Pads on/off does **not** change the chord sequence.

---

## 3. Matrix Chord Sequences + Loop All

This is how you go from jam A to jam B **without** stopping the Style.

### Behaviour you want

**Loop All = On**

- Sequences play **one after the other**
- Current pad = **steady** light
- Next pad = **flashing** until the current sequence **finishes**, then it enters
- After the last in the list, it returns to the first

That is **end of the whole sequence**, not “next bar.”

**Loop All = Off** would punch a new sequence on the next **measure** while the current one is still looping. You do not want that for this plan.

### Setup

1. Record or pick User Chord Sequences (one progression per jam, e.g. dorian vamp, blues, pop cycle).
2. Home → **Matrix** pane.
3. Choose / assign a **Chord Sequence** Matrix Preset (hold a Matrix Preset button until that preset is on it).
4. Expand the pane. Tick **Loop All**.
5. Assign sequences to Matrix pads (see Programming the Matrix in the Pa5X manual if the preset is empty).
6. These Matrix assignments **stay** when you change Style or SongBook. They are your standing jam palette.

### Live

1. Load the User Style. Start the Player.
2. Enable **CHORD → SEQUENCE** if needed.
3. Hit Matrix pad A. Improvise until that sequence **ends**.
4. Before it ends, you can pre-select B (it flashes). B starts when A finishes.
5. Style, Pads, and your solo keep going. Do **not** change SongBook here.

Stop the sequence: hit the same Matrix pad again, or stop the Player.

---

## 4. SongBook (between jams only)

Use an Entry to recall:

- Which User Style
- Keyboard Sets
- Which four Pads
- Mixer / FX as you saved them

Do **not** use SongBook to change chord progressions mid-jam.

If you still change Entry for sounds while a sequence should keep going, **lock** the Chord Sequence:

- Home → Chords pane → padlock, or
- Settings → Menu → General Controls → Lock → Style → Chord Sequence

Harmony still switches on the Matrix.

---

## Live layout (one jam)

1. SongBook Entry (or just the User Style) for the **band + Pads + your sounds**.
2. Matrix Chord Sequence preset, **Loop All on**.
3. Start Style. Hit sequence pad A.
4. Variations / Fills = arrangement density.
5. Pads 1–4 = extra players.
6. Let A finish → B enters. Keep soloing.
7. Next tune: **then** change SongBook.

---

## First build (do this once)

- [ ] User Style: copy drums (and bass if needed) from Styles you like
- [ ] Mute tracks that clutter
- [ ] Change Bass / Acc Sounds on the Style mixer
- [ ] Assign four Pads as extra players
- [ ] Save Style
- [ ] Save Keyboard Set(s) you actually play
- [ ] Record or choose 4–8 Chord Sequences
- [ ] Matrix Chord Sequence preset, Loop All **On**, sequences on pads
- [ ] Optional SongBook Entry for this kit
- [ ] Test: Style running, pad A → wait for end → B, no SongBook change

---

## If something feels wrong

| Symptom | Cause | Fix |
|---|---|---|
| Sequence stops when you change “song” | SongBook Entry reload | Stay on Matrix; lock Chord Sequence if you must change Entry |
| Next harmony arrives too soon | Loop All **Off** | Turn Loop All **On** |
| Next harmony waits forever | Waiting for the **whole** sequence | That is Loop All. Shorten the sequence, or use Loop All Off for next-bar punches |
| Pad changed the chords | Pads do not drive chords | Use Matrix Chord Sequences |
| New Drum copy sounds drowned | FX came with the copy | Lower Drum/Perc MFX send |
| Sound jumps back on a Fill | Program Change in the pattern | Live with it, or fix later in Style Edit |

---

## MODX (if you still chain it)

PA5X Chord MIDI (channel **16**) can drive MODX arp Parts only. That is separate from Pads and from Matrix sequences. The Chord Sequence **is** what those MIDI chord notes follow. Setup: [PA5X-MODX-M7-MIDI-Setup.md](PA5X-MODX-M7-MIDI-Setup.md).

### Use the Midihub, not MODX Thru

Put the Blokas Midihub in the middle: PA5X OUT → Midihub IN A, Midihub OUT A → MODX, OUT B → Jupiter. Filter so **only channel 16 notes** (and optional clock) reach the synths. MODX **MIDI Thru** stays **Off**.

Details and the Editor pipelines: [PA5X-MODX-M7-MIDI-Setup.md](PA5X-MODX-M7-MIDI-Setup.md).
