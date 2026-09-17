"""Human-readable MIDI note names and message formatting."""

from __future__ import annotations

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

_STATUS = {
    0x80: "off",
    0x90: "on",
    0xA0: "poly-at",
    0xB0: "cc",
    0xC0: "pc",
    0xD0: "ch-at",
    0xE0: "bend",
}


def note_name(note: int) -> str:
    """MIDI note number → scientific pitch (60 = C4)."""
    if not 0 <= note <= 127:
        return f"n{note}"
    return f"{NOTE_NAMES[note % 12]}{(note // 12) - 1}"


def channel_of(status: int) -> int | None:
    """MIDI channel 1–16, or None for system messages."""
    if 0x80 <= status <= 0xEF:
        return (status & 0x0F) + 1
    return None


def is_channel_voice(status: int) -> bool:
    return 0x80 <= status <= 0xEF


def is_realtime(status: int) -> bool:
    """MIDI clock / start / continue / stop."""
    return status in (0xF8, 0xFA, 0xFB, 0xFC)


def format_message(data: tuple[int, ...] | list[int]) -> str:
    if not data:
        return "(empty)"
    status = data[0]
    if status == 0xF0:
        return f"sysex {len(data)} bytes"
    if status >= 0xF0:
        return " ".join(f"{b:02X}" for b in data)

    ch = channel_of(status)
    kind = _STATUS.get(status & 0xF0, f"{status:02X}")
    payload = data[1:]

    if (status & 0xF0) == 0x90:
        note = payload[0] if payload else 0
        vel = payload[1] if len(payload) > 1 else 0
        if vel == 0:
            return f"ch{ch} {note_name(note)} off"
        return f"ch{ch} {note_name(note)} on vel {vel}"
    if (status & 0xF0) == 0x80:
        note = payload[0] if payload else 0
        vel = payload[1] if len(payload) > 1 else 0
        return f"ch{ch} {note_name(note)} off vel {vel}"
    if (status & 0xF0) == 0xB0:
        cc = payload[0] if payload else 0
        val = payload[1] if len(payload) > 1 else 0
        return f"ch{ch} cc{cc} {val}"
    if (status & 0xF0) == 0xC0:
        return f"ch{ch} pc {payload[0] if payload else 0}"
    if (status & 0xF0) == 0xE0:
        lsb = payload[0] if payload else 0
        msb = payload[1] if len(payload) > 1 else 0
        value = (msb << 7) | lsb
        return f"ch{ch} bend {value}"
    extra = " ".join(str(b) for b in payload)
    return f"ch{ch} {kind} {extra}".rstrip()
