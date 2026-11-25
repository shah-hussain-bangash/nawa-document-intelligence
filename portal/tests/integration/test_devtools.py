import argparse
import subprocess
import sys
from pathlib import Path
from typing import NoReturn, cast

import pytest

from scripts import devtools
from scripts.local_config import initialise_env, local_environment, read_env


def test_utf8_bom_quotes_and_literal_values(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    _ = path.write_text(
        '\ufeff# preserved\nDATA_DIR="بيانات عمل"\nTEST_KEY=literal#value\nLABEL=hello # comment\nexport ROUTE="${NOT_EXECUTED}"\n',
        encoding="utf-8",
    )
    saved = read_env(path)
    assert saved["DATA_DIR"] == "بيانات عمل"
    assert saved["TEST_KEY"] == "literal#value"
    assert saved["LABEL"] == "hello"
    assert saved["ROUTE"] == "${NOT_EXECUTED}"


def test_invalid_env_never_echoes_value(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    _ = path.write_text('KEY="do-not-print-this-value\n', encoding="utf-8")
    with pytest.raises(ValueError) as exc:
        _ = read_env(path)
    assert "do-not-print-this-value" not in str(exc.value)


def test_env_initialiser_preserves_user_content_and_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    _ = (tmp_path / ".env.example").write_text("APP_ENV=local\n", encoding="utf-8")
    path = tmp_path / ".env"
    original = "# user comment\nMODEL_MODE=extractive\n"
    _ = path.write_text(original, encoding="utf-8")
    _ = initialise_env(tmp_path)
    once = path.read_text()
    assert once.startswith(original)
    assert read_env(path)["POSTGRES_PASSWORD"]
    _ = initialise_env(tmp_path)
    assert path.read_text() == once


def test_shell_binding_wins_without_copying_secret(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ = (tmp_path / ".env").write_text("APP_ENV=local\nMODEL_MODE=extractive\n")
    monkeypatch.setenv("MODEL_MODE", "hosted")
    monkeypatch.setenv("POSTGRES_PASSWORD", "injected-test-value")
    assert local_environment(tmp_path)["MODEL_MODE"] == "hosted"
    _ = initialise_env(tmp_path)
    assert "injected-test-value" not in (tmp_path / ".env").read_text()


@pytest.mark.parametrize("value", ["0", "80", "65536", "-1"])
def test_invalid_ports_fail_clearly(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        _ = devtools.port_number(value)  # pyright: ignore[reportUnknownMemberType]  # Legacy launcher function is untyped.


def test_checked_command_preserves_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_args: object, **kwargs: object) -> None:
        assert kwargs["check"] is True
        raise subprocess.CalledProcessError(17, ["test-command"])

    monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises(subprocess.CalledProcessError) as exc:
        devtools.checked(["test-command"])  # pyright: ignore[reportUnknownMemberType]  # Legacy launcher function is untyped.
    assert exc.value.returncode == 17


def prepare_launcher(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def ignore_path(_path: object) -> None:
        return None

    monkeypatch.setattr(devtools, "ROOT", tmp_path)
    monkeypatch.setattr(devtools, "require_environment", lambda: Path(sys.executable))
    monkeypatch.setattr(devtools, "dependency_probe", ignore_path)
    monkeypatch.setattr(devtools, "require_frontend_ready", ignore_path)
    monkeypatch.setattr(devtools, "node_version", lambda: "24.22.1")
    monkeypatch.setattr(devtools, "npm_executable", lambda: "test-npm")
    path = tmp_path / "apps/web/node_modules"
    path.mkdir(parents=True)
    _ = (path / ".package-lock.json").write_text("{}")
    _ = (tmp_path / ".env.example").write_text("APP_ENV=local\n")


def test_occupied_port_stops_before_spawning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def occupied(_port: object) -> bool:
        return False

    def must_not_start(*_args: object, **_kwargs: object) -> NoReturn:
        pytest.fail("Must not start on an occupied port")

    prepare_launcher(tmp_path, monkeypatch)
    monkeypatch.setattr(devtools, "port_is_free", occupied)
    monkeypatch.setattr(subprocess, "Popen", must_not_start)
    assert devtools.main(["run"]) == 1  # pyright: ignore[reportUnknownMemberType]  # Legacy launcher function is untyped.
    output = capsys.readouterr()
    assert "already occupied" in output.err
    assert "READY:" not in output.out


def test_exited_child_is_not_reported_as_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def do_not_attach(_self: object, _process: object) -> None:
        return None

    def available(_port: object) -> bool:
        return True

    prepare_launcher(tmp_path, monkeypatch)
    monkeypatch.setattr("scripts.process_control.WindowsJob.attach", do_not_attach)
    monkeypatch.setattr(devtools, "port_is_free", available)

    class Exited:
        pid: int = 123

        def poll(self) -> int:
            return 0

    def exited(*_args: object, **_kwargs: object) -> Exited:
        return Exited()

    stopped: list[object] = []

    def stop(children: list[object]) -> None:
        stopped.extend(children)

    monkeypatch.setattr(subprocess, "Popen", exited)
    monkeypatch.setattr(devtools, "stop_children", stop)
    assert devtools.main(["run"]) == 1  # pyright: ignore[reportUnknownMemberType]  # Legacy launcher function is untyped.
    output = capsys.readouterr()
    assert "exited unexpectedly" in output.err
    assert "READY:" not in output.out
    assert len(stopped) == 2


def test_same_ports_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare_launcher(tmp_path, monkeypatch)
    assert devtools.main(["run", "--api-port", "5173"]) == 1  # pyright: ignore[reportUnknownMemberType]  # Legacy launcher function is untyped.


def test_smoke_refuses_remote_or_credential_urls(
    capsys: pytest.CaptureFixture[str],
) -> None:
    for url in [
        "https://remote.example",
        "http://user:secret@localhost:5173",
        "http://localhost:5173/other",
    ]:
        assert devtools.main(["smoke", "--url", url]) == 1  # pyright: ignore[reportUnknownMemberType]  # Legacy launcher function is untyped.
    assert "secret" not in capsys.readouterr().err


def test_auto_ports_avoid_occupied_and_duplicate_ports() -> None:
    import socket

    with socket.socket() as occupied:
        occupied.bind(("127.0.0.1", 0))
        port = cast(tuple[str, int], occupied.getsockname())[1]
        api, web = devtools.choose_available_ports(port, port)  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]  # Legacy launcher function is untyped.
        assert api != web
        assert port not in (api, web)
        assert devtools.port_is_free(api)  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]  # Legacy launcher function is untyped.
        assert devtools.port_is_free(web)  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]  # Legacy launcher function is untyped.
