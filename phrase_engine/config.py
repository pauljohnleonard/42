"""Load a small JSON config. Missing file is fine — CLI flags win."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class MidiConfig:
    input: str | None = None
    output: str | None = None


@dataclass(frozen=True)
class EngineConfig:
    midi: MidiConfig


def default_config() -> EngineConfig:
    return EngineConfig(midi=MidiConfig())


def load_config(path: str | Path) -> EngineConfig:
    p = Path(path)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise ConfigError(f"config not found: {p}") from e
    except json.JSONDecodeError as e:
        raise ConfigError(f"config is not JSON: {p}: {e}") from e
    if not isinstance(raw, dict):
        raise ConfigError(f"config root must be an object: {p}")
    return _from_dict(raw)


def _from_dict(raw: dict[str, Any]) -> EngineConfig:
    midi_raw = raw.get("midi") or {}
    if not isinstance(midi_raw, dict):
        raise ConfigError("midi must be an object")
    input_name = midi_raw.get("input") or None
    output_name = midi_raw.get("output") or None
    if input_name is not None and not isinstance(input_name, str):
        raise ConfigError("midi.input must be a string")
    if output_name is not None and not isinstance(output_name, str):
        raise ConfigError("midi.output must be a string")
    return EngineConfig(midi=MidiConfig(input=input_name, output=output_name))
