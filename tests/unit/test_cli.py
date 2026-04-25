from __future__ import annotations

from chatsune import cli


class _FakeConfig:
    data = {"vllm": {"model": "test/model"}}

    def build_vllm_command(self) -> list[str]:
        return ["vllm", "serve", "test/model", "--api-key", "super-secret"]


def test_print_config_show_command_redacts_api_key(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "load_runtime_config", lambda: _FakeConfig())

    exit_code = cli.main(["print-config", "--show-command"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "super-secret" not in captured.out
    assert "***REDACTED***" in captured.out
