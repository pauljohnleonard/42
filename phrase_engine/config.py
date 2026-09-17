"""Load a small JSON config. Missing file is fine — CLI flags win."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from phrase_engine.midi import PortError, resolve_port


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Device:
    alias: str
    port: str
    label: str | None = None

    def title(self) -> str:
        return self.label or self.alias


@dataclass(frozen=True)
class MidiConfig:
    input: str | None = None
    output: str | None = None


@dataclass(frozen=True)
class EngineConfig:
    midi: MidiConfig
    devices: tuple[Device, ...] = ()

    def device_map(self) -> dict[str, Device]:
        return {d.alias: d for d in self.devices}

    def lookup(self, query: str) -> str:
        """Turn an alias into a port pattern; unknown names pass through."""
        d = self.device_map().get(query.strip())
        return d.port if d else query

    def named(self, opened: str, ports: list[str]) -> str:
        """Pretty name for a resolved CoreMIDI port."""
        d = device_for_port(opened, self.devices, ports)
        if d is None:
            return opened
        if d.label:
            return f"{d.alias} ({d.label}, {opened})"
        return f"{d.alias} ({opened})"


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


def save_config(path: str | Path, cfg: EngineConfig) -> None:
    devices: dict[str, Any] = {}
    for d in cfg.devices:
        if d.label:
            devices[d.alias] = {"port": d.port, "label": d.label}
        else:
            devices[d.alias] = d.port
    raw = {
        "devices": devices,
        "midi": {
            "input": cfg.midi.input,
            "output": cfg.midi.output,
        },
    }
    Path(path).write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")


def guess_device(name: str) -> Device | None:
    """Friendly alias for a CoreMIDI port. Rig: PA5X on Midihub A, MODX on B."""
    n = (name or "").strip()
    lower = n.lower()
    if lower.startswith("midihub") and n.endswith(" A"):
        return Device("pa5x", n, "Korg PA5X")
    if lower.startswith("midihub") and n.endswith(" B"):
        return Device("modx", n, "Yamaha MODX M7")
    if lower.startswith("midihub") and n.endswith(" C"):
        return Device("hub-c", n, "Midihub C")
    if lower.startswith("midihub") and n.endswith(" D"):
        return Device("hub-d", n, "Midihub D")
    if n == "IAC Driver Bus 1":
        return Device("iac-in", n, "IAC Bus 1")
    if n == "IAC Driver Bus 2":
        return Device("iac-out", n, "IAC Bus 2")
    if "logic pro virtual out" in lower:
        return Device("logic", n, "Logic Pro")
    return None


def suggest_devices(inputs: list[str], outputs: list[str]) -> tuple[Device, ...]:
    seen: dict[str, Device] = {}
    for name in [*inputs, *outputs]:
        guessed = guess_device(name)
        if guessed is None or guessed.alias in seen:
            continue
        seen[guessed.alias] = guessed
    return tuple(seen.values())


def pick_defaults(devices: tuple[Device, ...]) -> MidiConfig:
    aliases = {d.alias for d in devices}
    inn = "pa5x" if "pa5x" in aliases else "iac-in" if "iac-in" in aliases else None
    if inn is None and devices:
        inn = devices[0].alias
    out = None
    for candidate in ("modx", "iac-out", "hub-c"):
        if candidate in aliases and candidate != inn:
            out = candidate
            break
    if out is None:
        for d in devices:
            if d.alias != inn:
                out = d.alias
                break
    return MidiConfig(input=inn, output=out)


def device_for_port(
    port: str, devices: tuple[Device, ...], ports: list[str]
) -> Device | None:
    for d in devices:
        try:
            _, resolved = resolve_port(ports, d.port)
        except PortError:
            if d.port == port:
                return d
            continue
        if resolved == port:
            return d
    return None


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

    devices_raw = raw.get("devices") or {}
    if devices_raw and not isinstance(devices_raw, dict):
        raise ConfigError("devices must be an object")
    devices = tuple(_parse_device(alias, spec) for alias, spec in devices_raw.items())
    return EngineConfig(midi=MidiConfig(input=input_name, output=output_name), devices=devices)


def _parse_device(alias: str, spec: Any) -> Device:
    if not alias or not isinstance(alias, str):
        raise ConfigError("device alias must be a string")
    if isinstance(spec, str):
        if not spec.strip():
            raise ConfigError(f"devices.{alias} port is empty")
        return Device(alias=alias, port=spec.strip())
    if not isinstance(spec, dict):
        raise ConfigError(f"devices.{alias} must be a string or object")
    port = spec.get("port")
    if not isinstance(port, str) or not port.strip():
        raise ConfigError(f"devices.{alias}.port must be a string")
    label = spec.get("label") or None
    if label is not None and not isinstance(label, str):
        raise ConfigError(f"devices.{alias}.label must be a string")
    return Device(alias=alias, port=port.strip(), label=label.strip() if label else None)
