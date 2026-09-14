# MODX M7: reuse a Part from another Performance

How to pull **one Part** (one sound / arp slot) out of a factory or User Performance and drop it into **your** Performance.

Print this or keep it open on a phone while you are at the MODX.

Related: [PA5X-MODX-M7-MIDI-Setup.md](PA5X-MODX-M7-MIDI-Setup.md) (Chord MIDI routing after the Part is in place).

---

## What went wrong

Tapping **+** does **not** open a list of Parts. It opens a list of **Performances**.

That is normal. You pick the Performance that **contains** the sound, then tell the MODX **which Part number** to copy. That control is **Source**.

Always look at the **title in the upper left**. That tells you which search you are in.

---

## The three searches

| How you open it | Title (upper left) | What it does |
|---|---|---|
| `[CATEGORY]` from Home, **no** Part selected | Performance Category Search | Loads a **whole** Performance. **Replaces** the one you were editing. |
| Tap **+** on an empty Part slot | Part X – **Performance Merge** | **Adds** into your current Performance. |
| Select a Part that already has a sound, then search | Part X – **Category Search** | **Replaces** that one Part only. |

If you meant to add a drum Part and the whole piano Performance disappeared, you were in **Performance Category Search**. Do not Store. Go back to your User Performance and use **+** or Part Category Search instead.

---

## Before you copy: find the Part number

Parts are not stored as independent files. They live **inside** a Performance as Part 1, Part 2, Part 3, …

1. Load the factory (or User) Performance that has the sound you like.
2. On Home, look at the Part slots. Note the number (for example drums = **Part 4**).
3. Load **your** Performance again (the one you are building).
4. Then copy, using **Source = Part 4**.

You can also type part of the Performance name in the search box once you are in Merge / Part Category Search.

---

## Method A — Add a Part into an empty slot

Use this when your Performance still has a **+** slot.

1. Stay in **your** Performance. Do not load the factory one as the current sound.
2. On Home, tap **+** on the next empty slot.
3. Confirm the title: **Part X – Performance Merge**.
4. Find the source Performance (category, bank, or name search).
5. Set **Source** at the top:
   - **All** = every Part from that Performance (usually too many)
   - **Part 1** … **Part 16** = **only that slot**
6. Set **Param. with Part** (green = bring it along):

   | Switch | Bring it if… | Turn off if… |
   |---|---|---|
   | Mixing | You want its volume/pan/FX send | You already mixed this slot |
   | **Arp/MS** | You want its arps / motion sequences | You only want the raw sound |
   | Scene | You want its Scene data | You already built Scenes |
   | Zone | You want its MIDI / zone settings | You will set Tx/Rx yourself (PA5X setup) |

   For a PA5X arp Part, leave **Arp/MS on**, turn **Zone off**, then set Keyboard Control / Tx/Rx yourself after the copy.

7. Select the Performance and confirm / Enter.
8. **Store** your Performance.

Example: factory Performance `Something Cool`, drums on Part 4 → Merge with **Source = Part 4**.

---

## Method B — Replace a Part you already have

Use this when the slot is not empty (you want to swap the sound).

1. On Home, tap the **Part name** (the Type/Name box), not **+**.
2. Choose **Category Search** from the side menu.  
   Or: select the Part, then **[SHIFT] + [CATEGORY]**.
3. Confirm the title: **Part X – Category Search**.
4. Find the source Performance.
5. Set **Source** to the Part number you want. (**All** is not available here — this search replaces one Part.)
6. Set **Param. with Part** as in Method A.
7. Confirm / Enter.
8. **Store**.

---

## After the Part is in your Performance

Copying does **not** automatically make it a PA5X Chord Part.

If this slot should follow PA5X chords (see the MIDI guide):

- Keyboard icon **off**
- `[EDIT]` → `Part Settings` → `Zone Settings` → **Tx/Rx Ch = 16**
- Part Mode = **Internal**
- **Arp Play Only = On**, Part Arp **On**, Arp Master **On**

If you will play it from the MODX keys:

- Keyboard icon **on**
- Leave Tx/Rx alone (it uses MIDI I/O Channel 1)

Then press `[PERFORMANCE]` so no Part is selected, and **Store**.

---

## Suggested template slots

Keep a consistent layout so copies always land in the same place:

| Parts | Role | After copy |
|---|---|---|
| 1–4 | Play from MODX keys | Keyboard Control **on** |
| 5–8 | Arps / sequences from PA5X | Keyboard Control **off**, Tx/Rx **16** |

Workflow:

1. Store **PA5X ARP TEMPLATE** with routing already set on slots 5–8.
2. Use **Method B** to replace those Parts with factory sounds.
3. On Part Category Search, turn **Zone off** so the template’s Tx/Rx **16** is kept.
4. Leave **Arp/MS on** if you want the factory arps.
5. Store as a new User Performance.

---

## What you cannot do (and the workaround)

There is no “Part library” of orphan sounds. Every sound you reuse is **Part N of some Performance**.

If you only want **one Element** (one layer inside a Part):

1. Merge / replace to bring the **whole Part** in.
2. Copy or mute Elements inside that Part.
3. Delete the extra Part if you no longer need it: tap the Part name → **Delete**.

Part 1 cannot be left empty. The MODX always keeps something in Part 1.

---

## Troubleshooting

| What you see | Cause | Fix |
|---|---|---|
| Whole Performance changed | Performance Category Search | Do not Store. Reload your User Performance. Use **+** or tap a Part name → Category Search |
| Too many new Parts appeared | **Source = All** | Delete extras, or Merge again with **Source = Part N** |
| Got the piano, not the drums | Wrong **Source** Part number | Check the factory Performance’s Part list, Merge with the correct number |
| Arps disappeared after swap | **Arp/MS** was off | Method B again with Arp/MS **on**, or re-assign arps |
| Keyboard Control / Tx/Rx got overwritten | **Zone** was on | Set Zone **off** when using a template, then set Tx/Rx again |
| Title does not say Merge or Part X | Home with no Part selected | Select a Part, or tap **+** |

---

## Copy-this checklist

### Find the source

- [ ] Open the factory Performance and note **Part number** of the sound
- [ ] Load **your** Performance again

### Add (empty slot)

- [ ] Tap **+**
- [ ] Title = **Performance Merge**
- [ ] **Source = Part N** (not All)
- [ ] Param. with Part set (Arp/MS / Zone as needed)
- [ ] Store

### Replace (slot already filled)

- [ ] Tap Part name → **Category Search** (or SHIFT + CATEGORY)
- [ ] Title = **Part X – Category Search**
- [ ] **Source = Part N**
- [ ] Param. with Part set
- [ ] Store

### If it is a PA5X arp Part

- [ ] Keyboard icon **off**
- [ ] Tx/Rx Ch = **16**
- [ ] Arp Play Only / Part Arp / Arp Master on
- [ ] Home, no Part selected
- [ ] Store
