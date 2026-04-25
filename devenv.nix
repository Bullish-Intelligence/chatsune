{ pkgs, ... }:

{
  env = {
    UV_CACHE_DIR = "/tmp/.uv-cache";
    UV_LINK_MODE = "copy";
  };

  packages = [
    pkgs.git
    pkgs.uv
  ];

  languages = {
    python = {
      enable = true;
      version = "3.13";
      venv.enable = true;
      uv.enable = true;
    };
  };

  scripts.test.exec = ''
    uv run --with pytest pytest tests -q
  '';

  scripts.test-unit.exec = ''
    uv run --with pytest pytest tests/unit -q
  '';

  scripts.test-smoke.exec = ''
    uv run --with pytest pytest tests/smoke -q
  '';

  enterShell = ''
    echo "Chatsune devenv ready."
    echo "Run: test | test-unit | test-smoke"
    python --version
    uv --version
  '';

  enterTest = ''
    test
  '';
}
