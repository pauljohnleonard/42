"""CLI: list ports, echo (M0 port test), listen (capture path)."""

from __future__ import annotations

import argparse
import queue
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path

from phrase_engine.config import ConfigError, EngineConfig, default_config, load_config
from phrase_engine.midi import (
    MidiBackend,
    MidiEngine,
    MidiError,
    MidiMessage,
    PortError,
    VIRTUAL_IN,
    VIRTUAL_OUT,
    format_port_list,
)
from phrase_engine.notes import format_message

_ECHO_BANNER = """\
M0 port test — Python is in the note path on purpose.
This is not the jam: live playing stays local (keyboard → synth).
Do not open the same port for in and out (MIDI feedback loop).
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
            return _cmd_ports(factory(), out)
        if args.command == "echo":
            return _cmd_echo(args, factory, out, err)
        if args.command == "listen":
            return _cmd_listen(args, factory, out, err)
        parser.print_help(out)
        return 2
    except (MidiError, ConfigError, FileNotFoundError) as e:
        print(e, file=err)
        return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="phrase-engine",
        description="Phrase engine MIDI brain. M0: ports talk.",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("ports", help="list MIDI inputs and outputs")

    echo = sub.add_parser(
        "echo",
        help="copy notes in → out (M0 hear-a-note test, not the jam path)",
    )
    _add_common(echo)
    echo.add_argument("--out", dest="output", default=None, help="output port (substring ok)")

    listen = sub.add_parser(
        "listen",
        help="print incoming notes; do not send (capture path)",
    )
    _add_common(listen)
    return parser


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--in", dest="input", default=None, help="input port (substring ok)")
    p.add_argument("--virtual", action="store_true", help="open PhraseEngine IN/OUT virtual ports")
    p.add_argument("--config", default=None, help="JSON config (see config.example.json)")
    p.add_argument("--channel", type=int, default=None, help="only this MIDI channel (1–16)")
    p.add_argument("--once", action="store_true", help="exit after the first channel message")
    p.add_argument("--seconds", type=float, default=None, help="exit after N seconds")


def _default_backend() -> MidiBackend:
    from phrase_engine.rtmidi_backend import RtMidiBackend

    return RtMidiBackend()


def _cmd_ports(backend: MidiBackend, out) -> int:
    print(format_port_list(backend.list_inputs(), backend.list_outputs()), file=out)
    print(
        "\nNo ports? On a Mac enable IAC in Audio MIDI Setup, "
        "or try: python -m phrase_engine echo --virtual",
        file=out,
    )
    return 0


def _load(args) -> EngineConfig:
    if args.config:
        return load_config(args.config)
    local = Path("config.json")
    if local.is_file():
        return load_config(local)
    return default_config()


def _cmd_echo(args, factory: Callable[[], MidiBackend], out, err) -> int:
    cfg = _load(args)
    backend = factory()
    in_name = args.input or cfg.midi.input
    out_name = args.output or cfg.midi.output

    if args.virtual:
        opened_in = backend.open_input(VIRTUAL_IN, virtual=True)
        opened_out = backend.open_output(VIRTUAL_OUT, virtual=True)
    else:
        if not in_name or not out_name:
            print(
                "echo needs --in and --out (or --virtual), "
                "or midi.input / midi.output in config.json.\n",
                file=err,
            )
            print(format_port_list(backend.list_inputs(), backend.list_outputs()), file=err)
            return 2
        opened_in = backend.open_input(in_name)
        opened_out = backend.open_output(out_name)
        if opened_in == opened_out:
            backend.close()
            print(
                f"Refusing to echo {opened_in!r} to itself — that is a MIDI loop.\n"
                "Use two IAC buses (Bus 1 → engine → Bus 2) or different devices.",
                file=err,
            )
            return 2

    print(_ECHO_BANNER, file=out)
    print(f"Echoing {opened_in!r} → {opened_out!r}. Ctrl+C to stop.", file=out)
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
    else:
        if not in_name:
            print(
                "listen needs --in (or --virtual), or midi.input in config.json.\n",
                file=err,
            )
            print(format_port_list(backend.list_inputs(), backend.list_outputs()), file=err)
            return 2
        opened_in = backend.open_input(in_name)

    print(f"Listening on {opened_in!r} (no echo). Ctrl+C to stop.", file=out)
    return _run_engine(
        backend,
        echo=False,
        channel=args.channel,
        once=args.once,
        seconds=args.seconds,
        out=out,
    )


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
