#!/usr/bin/env python3
"""Smoke PTY para comprobar que Claude descubre el slash command global /alfred.

No ejecuta el comando ni consume modelo: arranca una sesion interactiva de
Claude, escribe "/alfred" en el prompt y analiza el selector de comandos. Esta
prueba cubre el fallo de UX donde Claude mostraba "No commands match
\"/alfred\"" aunque el plugin estuviera instalado.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
import select
import shutil
import signal
import subprocess
import sys
import time


DEFAULT_WORKDIR = Path("/tmp/alfred-command-discovery-test")
ANSI_RE = re.compile(
    r"\x1b\][^\x07]*(?:\x07|\x1b\\)"
    r"|\x1b\[[0-?]*[ -/]*[@-~]"
    r"|\x1b[()][A-Za-z0-9]"
)


@dataclass(frozen=True)
class DiscoveryAnalysis:
    ok: bool
    problems: tuple[str, ...]
    alias_visible: bool
    alias_entry_count: int
    namespaced_visible: bool
    no_match_visible: bool


class CommandDiscoveryError(AssertionError):
    """Claude no mostro /alfred como comando descubrible."""


def strip_terminal_control(text: str) -> str:
    """Quita secuencias ANSI/OSC y normaliza espacios para analizar la UI."""

    cleaned = ANSI_RE.sub("", text)
    cleaned = cleaned.replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def analyze_discovery_output(raw_output: str) -> DiscoveryAnalysis:
    text = strip_terminal_control(raw_output)
    lowered = text.lower()
    compact_lowered = re.sub(r"\s+", "", lowered)
    no_match_visible = "no commands match" in lowered and "/alfred" in lowered
    alias_entry_count = sum(
        1
        for line in text.splitlines()
        if line.startswith("/alfred")
        and not line.startswith("/alfred-dev:")
        and (
            "alias global" in line.lower()
            or "aliasglobal" in re.sub(r"\s+", "", line.lower())
        )
    )
    alias_visible = alias_entry_count >= 1 or (
        "/alfred" in text and (
            "alias global" in lowered or "aliasglobal" in compact_lowered
        )
    )
    namespaced_visible = "/alfred-dev:" in text

    problems: list[str] = []
    if no_match_visible:
        problems.append('Claude muestra "No commands match" para /alfred')
    if not alias_visible:
        problems.append("No se ve /alfred como alias global en el selector")
    if alias_entry_count > 1:
        problems.append("Claude muestra mas de una entrada /alfred en el selector")
    if not namespaced_visible:
        problems.append("No se ven comandos /alfred-dev:* junto al alias")

    return DiscoveryAnalysis(
        ok=not problems,
        problems=tuple(problems),
        alias_visible=alias_visible,
        alias_entry_count=alias_entry_count,
        namespaced_visible=namespaced_visible,
        no_match_visible=no_match_visible,
    )


def _read_until_quiet(fd: int, deadline: float, quiet_seconds: float = 0.25) -> str:
    chunks: list[bytes] = []
    last_read = time.monotonic()
    while time.monotonic() < deadline:
        timeout = min(0.1, max(0.0, deadline - time.monotonic()))
        readable, _writable, _error = select.select([fd], [], [], timeout)
        if readable:
            try:
                chunk = os.read(fd, 8192)
            except OSError:
                break
            if not chunk:
                break
            chunks.append(chunk)
            last_read = time.monotonic()
            continue
        if chunks and time.monotonic() - last_read >= quiet_seconds:
            break
    return b"".join(chunks).decode("utf-8", errors="replace")


def _write(fd: int, value: str) -> None:
    os.write(fd, value.encode("utf-8"))


def _terminate(proc: subprocess.Popen[str], fd: int) -> None:
    if proc.poll() is not None:
        return
    for payload in ("\x03", "/exit\r", "\x03"):
        try:
            _write(fd, payload)
        except OSError:
            pass
        try:
            proc.wait(timeout=0.8)
            return
        except subprocess.TimeoutExpired:
            continue

    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except OSError:
        proc.terminate()
    try:
        proc.wait(timeout=1.5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except OSError:
            proc.kill()
        proc.wait(timeout=1.5)


def run_interactive_discovery(workdir: Path, timeout: float = 18.0) -> str:
    claude = shutil.which("claude")
    if claude is None:
        raise CommandDiscoveryError("No se encontro 'claude' en PATH")

    workdir.mkdir(parents=True, exist_ok=True)
    master_fd, slave_fd = os.openpty()
    env = os.environ.copy()
    env.setdefault("TERM", "xterm-256color")
    proc = subprocess.Popen(
        [claude],
        cwd=str(workdir),
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        text=True,
        close_fds=True,
        env=env,
        preexec_fn=os.setsid,
    )
    os.close(slave_fd)

    raw_output = ""
    deadline = time.monotonic() + timeout
    try:
        raw_output += _read_until_quiet(master_fd, min(deadline, time.monotonic() + 5.0))
        initial = strip_terminal_control(raw_output).lower()
        compact_initial = re.sub(r"\s+", "", initial)
        if (
            "quick safety check" in initial
            or "quicksafetycheck" in compact_initial
            or "yes, i trust this folder" in initial
            or "yes,itrustthisfolder" in compact_initial
        ):
            _write(master_fd, "\r")
            raw_output += _read_until_quiet(master_fd, min(deadline, time.monotonic() + 5.0))

        # Claude pinta el prompt antes de terminar de enganchar el input raw. Si
        # escribimos justo en ese instante, algunas versiones aceptan la sesion
        # pero descartan la primera tecla; esperamos y drenamos una vez mas.
        time.sleep(min(2.0, max(0.0, deadline - time.monotonic())))
        raw_output += _read_until_quiet(master_fd, min(deadline, time.monotonic() + 2.0), quiet_seconds=0.5)

        _write(master_fd, "/alfred")
        raw_output += _read_until_quiet(master_fd, min(deadline, time.monotonic() + 5.0), quiet_seconds=0.8)
        if "/alfred" not in strip_terminal_control(raw_output):
            time.sleep(min(1.0, max(0.0, deadline - time.monotonic())))
            _write(master_fd, "\x15/alfred")
            raw_output += _read_until_quiet(master_fd, min(deadline, time.monotonic() + 5.0), quiet_seconds=0.8)
        return raw_output
    finally:
        _terminate(proc, master_fd)
        try:
            os.close(master_fd)
        except OSError:
            pass


def _excerpt(raw_output: str, limit: int = 1400) -> str:
    text = strip_terminal_control(raw_output)
    if len(text) <= limit:
        return text
    return text[-limit:].strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", default=str(DEFAULT_WORKDIR))
    parser.add_argument("--timeout", type=float, default=18.0)
    parser.add_argument("--print-raw", action="store_true")
    args = parser.parse_args(argv)

    try:
        raw_output = run_interactive_discovery(Path(args.workdir), timeout=args.timeout)
        analysis = analyze_discovery_output(raw_output)
        if args.print_raw:
            print(_excerpt(raw_output, limit=6000))
        if not analysis.ok:
            raise CommandDiscoveryError("; ".join(analysis.problems) + "\n" + _excerpt(raw_output))
        print(
            "ok claude interactive command discovery: "
            "/alfred visible; /alfred-dev commands visible; missing-command warning absent"
        )
        return 0
    except CommandDiscoveryError as exc:
        print(f"FAIL claude-command-discovery: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
