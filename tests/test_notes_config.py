from pathlib import Path

import pytest

from phrase_engine.config import (
    ConfigError,
    guess_device,
    load_config,
    pick_defaults,
    suggest_devices,
)
from phrase_engine.notes import format_message, note_name


def test_note_name_c4():
    assert note_name(60) == "C4"
    assert note_name(61) == "C#4"
    assert note_name(0) == "C-1"


def test_format_note_on_off():
    assert format_message((0x90, 60, 96)) == "ch1 C4 on vel 96"
    assert format_message((0x90, 60, 0)) == "ch1 C4 off"
    assert format_message((0x80, 60, 64)) == "ch1 C4 off vel 64"
    assert format_message((0x9F, 64, 1)) == "ch16 E4 on vel 1"


def test_format_cc_and_pc():
    assert format_message((0xB0, 1, 127)) == "ch1 cc1 127"
    assert format_message((0xC1, 12)) == "ch2 pc 12"


def test_load_example_config():
    cfg = load_config(Path("config.example.json"))
    assert cfg.midi.input == "pa5x"
    assert cfg.midi.output == "modx"
    assert cfg.lookup("pa5x") == "Midihub A"
    assert cfg.device_map()["modx"].label == "Yamaha MODX M7"


def test_guess_midihub_rig():
    pa = guess_device("Midihub MH-0CNQEC3 A")
    mx = guess_device("Midihub MH-0CNQEC3 B")
    assert pa is not None and pa.alias == "pa5x" and pa.label == "Korg PA5X"
    assert mx is not None and mx.alias == "modx"
    devices = suggest_devices(
        ["Midihub MH-0CNQEC3 A", "IAC Driver Bus 1"],
        ["Midihub MH-0CNQEC3 B", "IAC Driver Bus 2"],
    )
    defaults = pick_defaults(devices)
    assert defaults.input == "pa5x"
    assert defaults.output == "modx"


def test_load_config_rejects_garbage(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text("{", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(p)
