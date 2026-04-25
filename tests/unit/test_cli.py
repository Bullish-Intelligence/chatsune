from __future__ import annotations

from chatsune import cli


class _FakeConfig:
    data = {"vllm": {"model": "test/model"}, "health": {"check_path": "/v1/models"}}

    def build_vllm_command(self) -> list[str]:
        return ["vllm", "serve", "test/model", "--api-key", "super-secret"]


def test_print_config_show_command_redacts_api_key(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "load_runtime_config", lambda: _FakeConfig())

    exit_code = cli.main(["print-config", "--show-command"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "super-secret" not in captured.out
    assert "***REDACTED***" in captured.out


def test_smoke_test_prefers_health_check_path_from_config(monkeypatch) -> None:
    monkeypatch.setattr(cli, "load_runtime_config", lambda: _FakeConfig())

    captured: dict[str, str | int | None] = {"base_url": None, "timeout": None, "preferred_path": None}

    def _fake_check_health(base_url: str, timeout: int = 5, preferred_path: str | None = None):
        captured["base_url"] = base_url
        captured["timeout"] = timeout
        captured["preferred_path"] = preferred_path
        return True, "OK"

    monkeypatch.setattr(cli, "check_health", _fake_check_health)

    exit_code = cli.main(["smoke-test", "--server-url", "http://localhost:9000"])

    assert exit_code == 0
    assert captured["base_url"] == "http://localhost:9000"
    assert captured["preferred_path"] == "/v1/models"


def test_smoke_test_check_path_arg_overrides_config(monkeypatch) -> None:
    monkeypatch.setattr(cli, "load_runtime_config", lambda: _FakeConfig())

    captured: dict[str, str | int | None] = {"preferred_path": None}

    def _fake_check_health(base_url: str, timeout: int = 5, preferred_path: str | None = None):
        captured["preferred_path"] = preferred_path
        return True, "OK"

    monkeypatch.setattr(cli, "check_health", _fake_check_health)

    exit_code = cli.main(["smoke-test", "--check-path", "/custom-health"])

    assert exit_code == 0
    assert captured["preferred_path"] == "/custom-health"
