from __future__ import annotations

import socket
import threading
from pathlib import Path

from reactivated_dev.procs import (
    PROCESSES_ENV,
    PROCESSES_EXTRA_ENV,
    collect_processes,
    is_socket_serving,
    parse_processes,
)


def test_parse_processes_reads_one_command_per_line() -> None:
    assert parse_processes("first\nsecond") == ["first", "second"]


def test_parse_processes_drops_blank_and_whitespace_lines() -> None:
    assert parse_processes("\n  first  \n\n   \nsecond\n") == ["first", "second"]


def test_parse_processes_collapses_duplicates_keeping_first_order() -> None:
    # The variable is exported, so a nested shell re-running a project's env
    # setup appends the same line again — spawning the side-car twice.
    assert parse_processes("a\nb\na\nc\nb") == ["a", "b", "c"]


def test_parse_processes_dedupes_after_stripping() -> None:
    assert parse_processes("  tunnel \ntunnel\n\ttunnel\t") == ["tunnel"]


def test_parse_processes_keeps_an_injected_line_a_project_re_appends() -> None:
    # A caller injects a side-car, the project's setup inherits and re-appends
    # its own: deduping is what lets a project seed from the inherited value
    # instead of clearing it and dropping the injected line.
    injected = "socat UNIX-LISTEN:/tmp/app.sock TCP:127.0.0.1:8000"
    assert parse_processes(f"{injected}\nserve\n{injected}") == [injected, "serve"]


def test_parse_processes_empty_is_no_commands() -> None:
    assert parse_processes("") == []
    assert parse_processes("\n  \n") == []


def test_collect_processes_runs_injected_before_project_owned() -> None:
    assert collect_processes(
        {PROCESSES_EXTRA_ENV: "bridge", PROCESSES_ENV: "tunnel"}
    ) == ["bridge", "tunnel"]


def test_collect_processes_keeps_injected_when_project_clears_its_own() -> None:
    # The whole point of the second variable: clearing PROCESSES_ENV is the
    # obvious way for a project to stay idempotent when its setup re-runs, and
    # it must not cost the caller its side-car.
    assert collect_processes({PROCESSES_EXTRA_ENV: "bridge", PROCESSES_ENV: ""}) == [
        "bridge"
    ]


def test_collect_processes_keeps_injected_when_project_overwrites_its_own() -> None:
    assert collect_processes(
        {PROCESSES_EXTRA_ENV: "bridge", PROCESSES_ENV: "tunnel"}
    ) == ["bridge", "tunnel"]


def test_collect_processes_dedupes_across_both_variables() -> None:
    assert collect_processes(
        {PROCESSES_EXTRA_ENV: "bridge\nshared", PROCESSES_ENV: "shared\ntunnel"}
    ) == ["bridge", "shared", "tunnel"]


def test_collect_processes_with_neither_variable_set() -> None:
    assert collect_processes({}) == []


def test_is_socket_serving_false_when_path_absent(tmp_path: Path) -> None:
    assert is_socket_serving(str(tmp_path / "nope.sock")) is False


def test_is_socket_serving_false_for_a_crashed_runs_leftover(tmp_path: Path) -> None:
    # The file outlives the process that made it, so existence cannot stand in
    # for liveness — binding over it is the whole point of the check.
    stale = tmp_path / "stale.sock"
    stale.touch()
    assert is_socket_serving(str(stale)) is False


def test_is_socket_serving_true_while_a_listener_accepts(tmp_path: Path) -> None:
    path = str(tmp_path / "live.sock")
    server = socket.socket(socket.AF_UNIX)
    server.bind(path)
    server.listen(1)
    accepting = threading.Thread(target=server.accept, daemon=True)
    accepting.start()

    try:
        assert is_socket_serving(path) is True
    finally:
        server.close()
