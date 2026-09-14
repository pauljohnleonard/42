# PA5X chords → MODX M7 arps / sequences

A setup guide for driving **Yamaha MODX M7** arpeggio and sequence Parts from **Korg PA5X** Chord MIDI, without other MODX Parts playing those chord notes.

Print this or keep it open on a phone while you are at the keyboards.

Related: [MODX-M7-Copy-Parts.md](MODX-M7-Copy-Parts.md) (how to pull one Part out of another Performance).
Related: [PA5X-Live-Jam-Reference.md](PA5X-Live-Jam-Reference.md) (PA5X live jam: remixed Styles, Pads, Matrix Chord Sequences).

---

## What you are building

| You do this | What should happen |
|---|---|
| Play chords on the PA5X (style / chord scan) | MODX arp / sequence Parts follow the chord |
| Play the MODX keys | Only the Parts you want to play by hand sound |
| Use MODX arp buttons, Hold, variations, tempo | Those still work on the MODX |

PA5X Chord out is **normal MIDI notes** (the recognized chord tones). The MODX will play anything that is listening on that channel. The work is making **only the arp Parts** listen.

---

## Do not look for “Hybrid”

The MODX M **does not have** `MIDI I/O Mode: Multi / Single / Hybrid`. That page is on the older MODX / MODX+ / Montage.

You do **not** need a firmware update for this. On the M7 the equivalent is already how MIDI works:

- Keyboard Control **ON** → Part listens to global **MIDI I/O Channel**
- Keyboard Control **OFF** → Part listens to that Part’s **Tx/Rx Ch**

Check firmware anytime with `[UTILITY]` → `Settings` → `System`.

---

## Channel plan (use this everywhere)

| Device | Setting | Value |
|---|---|---|
| PA5X | MIDI OUT Chord | **Channel 16** |
| MODX | MIDI I/O Channel | **Channel 1** |
| MODX arp / sequence Parts | Tx/Rx Ch | **16** |
| MODX play-by-hand Parts | Keyboard Control | **ON** (they use channel 1, not 16) |

Channel 16 is safer than 4. On the PA5X, 4 is often **Lower**. On the MODX, 4 is often Part 4, which is usually in the Keyboard Control group.

If Chord is already on **4** and you do not want to move it, use **4** everywhere this guide says **16**. Then set MODX **MIDI I/O Channel** to **1**, never to 4.

---

## Part 1 — PA5X (do once)

MIDI channel assignments are **not** saved automatically. Save a MIDI Preset at the end.

### 1. Open MIDI OUT channels

`SETTINGS` → `Menu` → `MIDI` → `MIDI OUT Channels`

### 2. Assign Chord only

For each MIDI channel 1–16:

- Set **one** channel to **Chord** → use **16**
- Set **Upper 1**, **Upper 2**, **Upper 3**, **Lower** to **Off** unless you *want* those to play the MODX
- Set Style / Player tracks (**Sty Drum**, **Sty Bass**, **Sty Acc**, **Ply …**) to **Off** unless you *want* style MIDI on the MODX

Nothing else should share channel 16.

### 3. Optional: lock arps to style tempo

If you want MODX arps in time with the PA5X style:

- Send MIDI clock from the PA5X (`SETTINGS` → `MIDI` sync / clock out — On)
- On the MODX later, set MIDI Sync to **MIDI**

If you skip this, MODX arps use the MODX’s own tempo.

### 4. Save a MIDI Preset

Save this as something obvious, for example **MODX Arps**.

Recall that preset whenever you connect the M7.

### 5. Cable

PA5X **MIDI OUT** → MODX M7 **MIDI IN**

(Or USB-MIDI if that is how you already connect them. The channel plan is the same.)

### 6. Daisy-chain another synth (Jupiter-Xm, etc.)

The MODX M has **MIDI IN** and **MIDI OUT** only. There is **no dedicated THRU jack**. The OUT jack can still pass the PA5X through:

`[UTILITY]` → `Settings` → `MIDI I/O`

| Parameter | Setting |
|---|---|
| MIDI IN/OUT | **MIDI** (5-pin). **MIDI Thru** is hidden if this is USB. |
| **MIDI Thru** | **On** |

Cables:

PA5X **MIDI OUT** → MODX **MIDI IN**  
MODX **MIDI OUT** → Jupiter (or the next synth) **MIDI IN**

With **MIDI Thru On**, notes arriving at MODX IN are copied to MODX OUT. The PA5X Chord channel (16) still arrives as channel 16 on the Jupiter. The MODX still *plays* those notes internally. The MODX keyboard itself is **not** sent out that jack while Thru is On.

With **MIDI Thru Off**, OUT is only what the MODX *generates* (keys, Zones, arp MIDI Out). The PA5X will **not** reach the Jupiter.

Keep the chain to two synths. If Thru feels late or messy, skip the daisy-chain: use a small MIDI thru/splitter from the PA5X so MODX and Jupiter each get their own copy.

Do **not** also send PA5X Chord into the Jupiter by a second cable while Thru is On — that double-triggers.

---

## Part 2 — MODX M7 globals (do once)

These apply to every Performance.

### 1. Open MIDI I/O

`[UTILITY]` → `Settings` → `MIDI I/O`

You can also tap the **Quick Setup** icon in the top bar.

### 2. Set these

| Parameter | Setting |
|---|---|
| MIDI IN/OUT | **MIDI** (5-pin) or **USB** (if that is your connection) |
| Local Control | **On** |
| **MIDI I/O Channel** | **1** (must **not** be the Chord channel) |

### 3. Optional tempo sync

On the same MIDI I/O screen:

| Parameter | Setting |
|---|---|
| MIDI Sync | **MIDI** (if PA5X is sending clock) |
| Clock Out | Off unless something else needs clock from the MODX |

If arps feel stuck or will not start, set MIDI Sync back to **Internal** and set tempo on the MODX.

---

## Part 3 — Each Performance you want the PA5X to control

Factory Performances are built for the MODX keys, not for a Chord channel. Repeat this, then **Store** as a User Performance.

### Suggested layout (template)

Keep this layout if you can. It makes the next sounds faster.

| Parts | Role | Keyboard icon | Tx/Rx Ch |
|---|---|---|---|
| 1–4 | Play from MODX keys (piano, pad, lead, …) | **ON** (green) | Leave it (uses MIDI I/O Ch 1) |
| 5–8 | Arps / sequences from PA5X | **OFF** | **16** |
| Other Parts you must not hear from MIDI | Silent extras | **OFF** | **Off** |

You do not have to use slots 5–8. Any arp Part can be Keyboard Control off + Tx/Rx 16.

### Step-by-step

1. Load the Performance.
2. For **each arp / sequence Part**:
   - Tap the small **keyboard icon** so it is **off** (not green).
3. Select that Part → `[EDIT]` → `Part Settings` → `Zone Settings`:
   - Part Mode = **Internal** (not External)
   - **Tx/Rx Ch** = **16**
4. Still on that Part:
   - `Part Settings` → `General` → **Arp Play Only** = **On**
   - Part Arp = **On**
5. Turn the front-panel **Arp Master** **On**.
6. Arp **Key Mode** should not be **Direct** (Direct lets the raw chord sound under the arp).
7. For Parts you play by hand: keyboard icon **ON**.
8. For Parts that must never play from the PA5X: keyboard icon **OFF**, Tx/Rx Ch = **Off**.
9. Press `[PERFORMANCE]` (**HOME**) so **no Part is selected** (no white box around a Part).
10. **Store** as a User Performance. Name it so you can find it (for example `Init Sound PA`).

If you skip Store, the routing is lost when you change Performances.

### Keyboard Control off does **not** disable the arp

You still use the MODX for:

- Arp Master on/off
- Part Arp on/off
- Hold
- Variations / ARP SELECT
- Tempo, scenes, ARP/MS knobs

What Keyboard Control off *does*: the **MODX keys** no longer feed notes into that Part (unless that Part is selected). The **PA5X** feeds the notes over MIDI.

To trigger one arp from the MODX keys anyway: select that Part, play, then press `[PERFORMANCE]` to go back.

---

## Part 4 — Faster method: make a template once

1. Build one User Performance with the table in Part 3 already correct (even with simple placeholder sounds).
2. Store it as **PA5X ARP TEMPLATE**.
3. For each new sound:
   - Load the template
   - Replace Parts 1–4 and 5–8 with the voices you want
   - **Do not** turn the arp Parts’ keyboard icons back on
   - **Do not** change Tx/Rx Ch off 16
   - Store as a new User Performance
4. Put those User Performances in a **Live Set** for gigs.

---

## Part 5 — Test it

Do this after the first stored Performance.

1. Recall the PA5X MIDI Preset **MODX Arps**.
2. Load the stored MODX User Performance.
3. Press `[PERFORMANCE]` so no Part is selected.
4. Arp Master **On**.
5. Play a chord on the PA5X.

**Pass:** only arp / sequence Parts sound, in the new chord.

6. Turn Arp Master **Off**. Play the same chord on the PA5X.

**Pass:** MODX is silent. If anything still sounds, that Part is still on channel 16 (Keyboard Control on, or Tx/Rx 16).

7. Play the MODX keys.

**Pass:** only Keyboard Control **on** Parts sound. Arps do not run from the keys.

8. Optional: start a PA5X style with clock sent. MODX arps should follow tempo if MIDI Sync = MIDI.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Chord plays piano/pad/lead as well as arps | Those Parts have Keyboard Control **on** and MIDI I/O Ch = Chord channel, **or** they share the Keyboard Control group with a Part on channel 16 | MIDI I/O Ch = **1**. Arp Parts Keyboard Control **off**, Tx/Rx = **16** |
| Arps do not start from PA5X | Arp Part still Keyboard Control **on**, or Tx/Rx is not 16, or Part Mode is External, or Arp Master / Part Arp off | Match Part 3. Part Mode **Internal**. Arp switches on |
| Arps work but you also hear the held chord on the arp sound | Arp Play Only off, or Key Mode = Direct | Arp Play Only **On**. Key Mode not Direct |
| One extra Part plays only while you are editing | That Keyboard Control–off Part is **selected** | Press `[PERFORMANCE]` (HOME) |
| Changing Performance loses the setup | Not stored | Store a User Performance |
| PA5X MIDI channels “forgot” Chord on 16 | MIDI Preset not saved / not recalled | Save and recall the MIDI Preset |
| Right-hand PA5X playing also triggers MODX | Upper 1/2/3 still assigned on MIDI OUT | Set those tracks **Off** |
| Arps will not run, or run at the wrong speed | MIDI Sync = MIDI but no clock from PA5X | Send clock from PA5X, or set MODX MIDI Sync = **Internal** |
| Looking for Hybrid / MIDI I/O Mode | That menu is not on MODX M | Use MIDI I/O Channel + Keyboard Control + Tx/Rx Ch |
| Jupiter (or next synth) silent on the chain | MIDI Thru Off, or MIDI IN/OUT = USB so Thru is hidden | MIDI IN/OUT = **MIDI**, **MIDI Thru** = **On** |

---

## Copy-this checklist

### Once

- [ ] PA5X MIDI OUT: Chord = **16**, other tracks Off on that port
- [ ] PA5X MIDI Preset saved
- [ ] PA5X MIDI OUT → MODX MIDI IN
- [ ] Optional chain: MODX MIDI Thru **On**, MODX OUT → next synth IN
- [ ] MODX MIDI I/O Channel = **1**
- [ ] MODX Local Control = **On**
- [ ] Optional: both instruments sharing MIDI clock

### Each Performance, then Store

- [ ] Arp / sequence Parts: keyboard icon **off**
- [ ] Those Parts: Tx/Rx Ch = **16**, Part Mode Internal
- [ ] Arp Play Only **On**, Part Arp **On**, Arp Master **On**
- [ ] Play-by-hand Parts: keyboard icon **on**
- [ ] Home screen, no Part selected
- [ ] Store User Performance

### Quick test

- [ ] PA5X chord + Arp On → only arps
- [ ] PA5X chord + Arp Off → silence
- [ ] MODX keys → only hand-played Parts
