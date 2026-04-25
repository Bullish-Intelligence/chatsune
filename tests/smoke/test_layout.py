from pathlib import Path


def test_expected_files_exist() -> None:
    expected = [
        "compose.yaml",
        "compose.auth.yaml",
        "compose.profiles.yaml",
        ".env.example",
        "config/server-config.example.yaml",
        "docs/configuration.md",
        "images/vllm/Dockerfile",
        "scripts/smoke_test.py",
        "scripts/adapter_manager.py",
    ]
    for rel in expected:
        assert Path(rel).exists(), rel
