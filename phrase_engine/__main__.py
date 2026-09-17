"""CLI: list ports, echo (M0 port test), listen (capture path), chords (M1)."""

from __future__ import annotations

import argparse
import queue
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path

from phrase_engine.chords import CHORD_CHANNEL, ChordBus
from phrase_engine.loop import LoopSession
from phrase_engine.config import (
    ConfigError,
    EngineConfig,
    MidiConfig,
    default_config,
    device_for_port,
    load_config,
    pick_defaults,
    save_config,
    suggest_devices,
)
from phrase_engine.midi import (
    MidiBackend,
    MidiEngine,
    MidiError,
    MidiMessage,
    VIRTUAL_IN,
    VIRTUAL_OUT,
    format_port_list,
    resolve_port,
)
from phrase_engine.notes import format_message

_ECHO_BANNER = """\
M0 port test — Python is in the note path on purpose.
This is not the jam: live playing stays local (keyboard → synth).
Do not open the same port for in and out (MIDI feedback loop).
"""

_CHORD_BANNER = """\
M1 chord bus — held notes set the chord; tones go out on ch 16.
Live playing stays local (keyboard → synth). This is not Python thru.
"""

_LOOP_BANNER = """\
M2 loop — slave to PA MIDI clock. Live sound stays on the Pa.
First Start records N bars; then that take loops to the output (not thru).
Stop/Start the Style to sync. Ctrl+C to quit.
"""


def main(
    argv: Sequence[str] | None = None,
    *,
    backend_factory: Callable[[], MidiBackend] | None = None,
    stdout=None,
    stderr=None,
) -> int:
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    parser = _parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    factory = backend_factory or _default_backend

    try:
        if args.command == "ports":
            return _cmd_ports(args, factory(), out)
        if args.command == "setup":
            return _cmd_setup(args, factory, out, err)
        if args.command == "echo":
            return _cmd_echo(args, factory, out, err)
        if args.command == "listen":
            return _cmd_listen(args, factory, out, err)
        if args.command == "chords":
            return _cmd_chords(args, factory, out, err)
        if args.command == "loop":
            return _cmd_loop(args, factory, out, err)
        parser.print_help(out)
        return 2
    except (MidiError, ConfigError, FileNotFoundError) as e:
        print(e, file=err)
        return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="phrase-engine",
        description="Phrase engine MIDI brain. M0 ports, M1 chords, M2 clock loop.",
    )
    sub = parser.add_subparsers(dest="command")

    ports = sub.add_parser("ports", help="list MIDI inputs and outputs")
    ports.add_argument("--config", default=None, help="JSON config (see config.example.json)")

    setup = sub.add_parser(
        "setup",
        help="name devices and pick default MIDI in/out (writes config.json)",
    )
    setup.add_argument("--in", dest="input", default=None, help="default input alias or port")
    setup.add_argument("--out", dest="output", default=None, help="default output alias or port")
    setup.add_argument("--config", default=None, help="path to write (default: config.json)")
    setup.add_argument(
        "--yes",
        action="store_true",
        help="write guessed names without prompting",
    )

    echo = sub.add_parser(
        "echo",
        help="copy notes in → out (M0 hear-a-note test, not the jam path)",
    )
    _add_common(echo)
    echo.add_argument("--out", dest="output", default=None, help="output port or alias")

    listen = sub.add_parser(
        "listen",
        help="print incoming notes; do not send (capture path)",
    )
    _add_common(listen)

    chords = sub.add_parser(
        "chords",
        help="name held notes and send them on ch 16 (M1 chord bus)",
    )
    _add_common(chords)
    chords.add_argument("--out", dest="output", default=None, help="output port or alias")

    loop = sub.add_parser(
        "loop",
        help="slave to PA clock, record N bars, loop that phrase (M2)",
    )
    _add_common(loop)
    loop.add_argument("--out", dest="output", default=None, help="playback port or alias")
    loop.add_argument("--bars", type=int, default=2, help="capture length in bars (default 2)")
    return parser


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--in", dest="input", default=None, help="input port or alias (substring ok)")
    p.add_argument("--virtual", action="store_true", help="open PhraseEngine IN/OUT virtual ports")
    p.add_argument("--config", default=None, help="JSON config (see config.example.json)")
    p.add_argument("--channel", type=int, default=None, help="only this MIDI channel (1–16)")
    p.add_argument("--once", action="store_true", help="exit after the first channel message")
    p.add_argument("--seconds", type=float, default=None, help="exit after N seconds")


def _default_backend() -> MidiBackend:
    from phrase_engine.rtmidi_backend import RtMidiBackend

    return RtMidiBackend()


def _cmd_ports(args, backend: MidiBackend, out) -> int:
    cfg = _load(args)
    inputs = backend.list_inputs()
    outputs = backend.list_outputs()
    print(
        format_port_list(
            inputs,
            outputs,
            annotate=_port_annotate(cfg, inputs, outputs),
        ),
        file=out,
    )
    if cfg.midi.input or cfg.devices:
        print(
            "\nAliases are from config.json. "
            "Change default in with: python -m phrase_engine setup",
            file=out,
        )
    print(
        "\nNo ports? On a Mac enable IAC in Audio MIDI Setup, "
        "or try: python -m phrase_engine echo --virtual",
        file=out,
    )
    return 0


def _port_annotate(cfg: EngineConfig, inputs: list[str], outputs: list[str]):
    def annotate(name: str, which: str) -> str:
        ports = inputs if which == "in" else outputs
        d = device_for_port(name, cfg.devices, ports)
        tags: list[str] = []
        if d is not None:
            tags.append(d.alias)
            if d.label:
                tags.append(d.label)
        default = cfg.midi.input if which == "in" else cfg.midi.output
        if default:
            try:
                resolved = resolve_port(ports, cfg.lookup(default))[1]
            except (MidiError, ValueError):
                resolved = None
            if resolved == name:
                tags.append(f"default {which}")
        return ("  " + "  ".join(tags)) if tags else ""

    return annotate


def _load(args) -> EngineConfig:
    path = getattr(args, "config", None)
    if path:
        return load_config(path)
    local = Path("config.json")
    if local.is_file():
        return load_config(local)
    return default_config()


def _cmd_setup(args, factory: Callable[[], MidiBackend], out, err) -> int:
    dest = Path(args.config) if args.config else Path("config.json")
    backend = factory()
    inputs = backend.list_inputs()
    outputs = backend.list_outputs()
    devices = suggest_devices(inputs, outputs)
    guessed = pick_defaults(devices)
    existing = load_config(dest) if dest.is_file() else default_config()
    inn = args.input or existing.midi.input or guessed.input
    outp = args.output or existing.midi.output or guessed.output

    cfg = EngineConfig(midi=MidiConfig(input=inn, output=outp), devices=devices)
    print(
        format_port_list(inputs, outputs, annotate=_port_annotate(cfg, inputs, outputs)),
        file=out,
    )
    if not devices:
        print("\nNo named devices guessed. Write port names into config.json.", file=out)

    if not args.yes and sys.stdin.isatty():
        inn = _prompt_choice("Default MIDI in", inn, devices, inputs, out) or inn
        outp = _prompt_choice("Default MIDI out", outp, devices, outputs, out) or outp
        cfg = EngineConfig(midi=MidiConfig(input=inn, output=outp), devices=devices)

    save_config(dest, cfg)
    print(f"\nWrote {dest}", file=out)
    if cfg.midi.input:
        print(f"  in   {cfg.midi.input}", file=out)
    if cfg.midi.output:
        print(f"  out  {cfg.midi.output}", file=out)
    print(
        "\nThen: python -m phrase_engine listen\n"
        "      python -m phrase_engine loop",
        file=out,
    )
    backend.close()
    return 0


def _prompt_choice(
    label: str,
    current: str | None,
    devices: tuple,
    ports: list[str],
    out,
) -> str | None:
    rows: list[str] = []
    for d in devices:
        try:
            resolve_port(ports, d.port)
        except MidiError:
            continue
        rows.append(d.alias)
    hint = f" [{current}]" if current else ""
    print(f"\n{label}{hint} — alias, number, or port:", file=out, flush=True)
    for i, alias in enumerate(rows):
        print(f"  [{i}] {alias}", file=out)
    try:
        raw = input("> ").strip()
    except EOFError:
        return current
    if not raw:
        return current
    if raw.isdigit():
        idx = int(raw)
        if 0 <= idx < len(rows):
            return rows[idx]
        print(f"No choice [{idx}]", file=out)
        return current
    return raw


def _cmd_echo(args, factory: Callable[[], MidiBackend], out, err) -> int:
    backend = factory()
    opened = _open_pair(args, backend, err)
    if isinstance(opened, int):
        return opened
    opened_in, opened_out = opened

    print(_ECHO_BANNER, file=out)
    cfg = _load(args)
    print(
        f"Echoing {cfg.named(opened_in, backend.list_inputs())} → "
        f"{cfg.named(opened_out, backend.list_outputs())}. Ctrl+C to stop.",
        file=out,
    )
    return _run_engine(
        backend,
        echo=True,
        channel=args.channel,
        once=args.once,
        seconds=args.seconds,
        out=out,
    )


def _cmd_listen(args, factory: Callable[[], MidiBackend], out, err) -> int:
    cfg = _load(args)
    backend = factory()
    in_name = args.input or cfg.midi.input

    if args.virtual:
        opened_in = backend.open_input(VIRTUAL_IN, virtual=True)
        shown_in = opened_in
    else:
        if not in_name:
            print(
                "listen needs --in (or --virtual), or midi.input in config.json.\n",
                file=err,
            )
            print(format_port_list(backend.list_inputs(), backend.list_outputs()), file=err)
            return 2
        opened_in = backend.open_input(cfg.lookup(in_name))
        shown_in = cfg.named(opened_in, backend.list_inputs())

    print(f"Listening on {shown_in} (no echo). Ctrl+C to stop.", file=out)
    return _run_engine(
        backend,
        echo=False,
        channel=args.channel,
        once=args.once,
        seconds=args.seconds,
        out=out,
    )


def _open_pair(args, backend: MidiBackend, err) -> tuple[str, str] | int:
    cfg = _load(args)
    in_name = args.input or cfg.midi.input
    out_name = args.output or cfg.midi.output
    if args.virtual:
        return backend.open_input(VIRTUAL_IN, virtual=True), backend.open_output(
            VIRTUAL_OUT, virtual=True
        )
    if not in_name or not out_name:
        print(
            f"{args.command} needs --in and --out (or --virtual), "
            "or midi.input / midi.output in config.json.\n",
            file=err,
        )
        print(format_port_list(backend.list_inputs(), backend.list_outputs()), file=err)
        return 2
    opened_in = backend.open_input(cfg.lookup(in_name))
    opened_out = backend.open_output(cfg.lookup(out_name))
    if opened_in == opened_out:
        backend.close()
        print(
            f"Refusing to open {opened_in!r} as in and out — that is a MIDI loop.\n"
            "Use two IAC buses (Bus 1 → engine → Bus 2) or different devices.",
            file=err,
        )
        return 2
    return opened_in, opened_out


def _cmd_chords(args, factory: Callable[[], MidiBackend], out, err) -> int:
    backend = factory()
    opened = _open_pair(args, backend, err)
    if isinstance(opened, int):
        return opened
    opened_in, opened_out = opened
    print(_CHORD_BANNER, file=out)
    cfg = _load(args)
    print(
        f"Chord bus {cfg.named(opened_in, backend.list_inputs())} → "
        f"{cfg.named(opened_out, backend.list_outputs())} ch{CHORD_CHANNEL}. "
        "Ctrl+C to stop.",
        file=out,
        flush=True,
    )
    log_q: queue.SimpleQueue[str] = queue.SimpleQueue()
    bus = ChordBus(backend.send, on_change=log_q.put)

    def on_message(msg: MidiMessage) -> None:
        bus.handle(msg)

    engine = MidiEngine(
        backend,
        echo=False,
        channel=args.channel,
        on_message=on_message,
        on_tick=bus.tick,
    )
    engine.start()
    deadline = time.monotonic() + args.seconds if args.seconds is not None else None
    try:
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                return 0
            try:
                line = log_q.get(timeout=0.05)
            except queue.Empty:
                continue
            print(line, file=out, flush=True)
            if args.once:
                return 0
    except KeyboardInterrupt:
        print("\nstopping", file=out)
        return 0
    finally:
        bus.panic()
        engine.stop()


def _cmd_loop(args, factory: Callable[[], MidiBackend], out, err) -> int:
    if args.bars < 1:
        print("bars must be >= 1", file=err)
        return 2
    backend = factory()
    opened = _open_pair(args, backend, err)
    if isinstance(opened, int):
        return opened
    opened_in, opened_out = opened
    cfg = _load(args)
    print(_LOOP_BANNER, file=out)
    print(
        f"Clock/notes {cfg.named(opened_in, backend.list_inputs())} → "
        f"loop {cfg.named(opened_out, backend.list_outputs())}  {args.bars} bars. "
        "Ctrl+C to stop.",
        file=out,
        flush=True,
    )
    log_q: queue.SimpleQueue[str] = queue.SimpleQueue()
    session = LoopSession(backend.send, bars=args.bars, on_status=log_q.put)
    print(session.status_line(), file=out, flush=True)

    def on_message(msg: MidiMessage) -> None:
        session.handle(msg)

    engine = MidiEngine(
        backend,
        echo=False,
        channel=args.channel,
        on_message=on_message,
        on_clock=on_message,
        on_tick=session.tick,
    )
    engine.start()
    deadline = time.monotonic() + args.seconds if args.seconds is not None else None
    try:
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                return 0
            try:
                line = log_q.get(timeout=0.05)
            except queue.Empty:
                continue
            print(line, file=out, flush=True)
            if args.once and session.phrase is not None and session.phase == "play":
                return 0
    except KeyboardInterrupt:
        print("\nstopping", file=out)
        return 0
    finally:
        session.panic()
        engine.stop()


def _run_engine(
    backend: MidiBackend,
    *,
    echo: bool,
    channel: int | None,
    once: bool,
    seconds: float | None,
    out,
) -> int:
    log_q: queue.SimpleQueue[str] = queue.SimpleQueue()

    def on_message(msg: MidiMessage) -> None:
        log_q.put(format_message(msg.data))

    engine = MidiEngine(backend, echo=echo, channel=channel, on_message=on_message)
    engine.start()
    deadline = time.monotonic() + seconds if seconds is not None else None
    try:
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                return 0
            try:
                line = log_q.get(timeout=0.05)
            except queue.Empty:
                continue
            print(line, file=out, flush=True)
            if once:
                return 0
    except KeyboardInterrupt:
        print("\nstopping", file=out)
        return 0
    finally:
        engine.stop()


if __name__ == "__main__":
    sys.exit(main())
