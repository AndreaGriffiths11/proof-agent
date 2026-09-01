"""Tests for Copilot SDK verification."""

import pytest

from proof_agent import copilot_sdk


def test_model_prefers_copilot_model(monkeypatch):
    monkeypatch.setenv("PROOF_AGENT_COPILOT_MODEL", "gpt-5")
    monkeypatch.setenv("PROOF_AGENT_MODEL", "ignored")

    assert copilot_sdk._model() == "gpt-5"


def test_model_falls_back_to_auto(monkeypatch):
    monkeypatch.delenv("PROOF_AGENT_COPILOT_MODEL", raising=False)
    monkeypatch.delenv("PROOF_AGENT_MODEL", raising=False)

    assert copilot_sdk._model() == "auto"


def test_main_requires_prompt(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", _StringIO(""))

    with pytest.raises(SystemExit) as exc_info:
        copilot_sdk.main()

    assert exc_info.value.code == 1
    assert "No verification prompt provided" in capsys.readouterr().err


def test_runtime_env_prefers_copilot_token(monkeypatch):
    monkeypatch.setenv("COPILOT_GITHUB_TOKEN", "copilot-token")
    monkeypatch.setenv("GITHUB_TOKEN", "github-token")
    monkeypatch.setenv("GH_TOKEN", "gh-token")

    env = copilot_sdk._runtime_env()

    assert env["COPILOT_GITHUB_TOKEN"] == "copilot-token"


def test_github_token_uses_same_precedence(monkeypatch):
    monkeypatch.setenv("COPILOT_GITHUB_TOKEN", "copilot-token")
    monkeypatch.setenv("GITHUB_TOKEN", "github-token")
    monkeypatch.setenv("GH_TOKEN", "gh-token")

    assert copilot_sdk._github_token() == "copilot-token"


def test_github_token_empty_mapping_ignores_ambient_env(monkeypatch):
    monkeypatch.setenv("COPILOT_GITHUB_TOKEN", "ambient-token")

    assert copilot_sdk._github_token({}) is None


def test_runtime_env_promotes_github_token(monkeypatch):
    monkeypatch.delenv("COPILOT_GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("GITHUB_TOKEN", "github-token")
    monkeypatch.setenv("GH_TOKEN", "gh-token")

    env = copilot_sdk._runtime_env()

    assert env["COPILOT_GITHUB_TOKEN"] == "github-token"


def test_runtime_env_rejects_cli_login_in_ci(monkeypatch):
    monkeypatch.delenv("COPILOT_GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("PROOF_AGENT_USE_CLI_LOGIN", raising=False)
    monkeypatch.setenv("CI", "true")

    with pytest.raises(RuntimeError, match="requires COPILOT_GITHUB_TOKEN"):
        copilot_sdk._runtime_env()


def test_explicit_cli_login_works_in_ci(monkeypatch):
    monkeypatch.delenv("COPILOT_GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setenv("PROOF_AGENT_USE_CLI_LOGIN", "1")
    monkeypatch.setenv("CI", "true")

    env = copilot_sdk._runtime_env()

    assert copilot_sdk._use_logged_in_user(env) is True
    assert "COPILOT_GITHUB_TOKEN" not in env


def test_cli_login_is_default_outside_ci(monkeypatch):
    monkeypatch.delenv("COPILOT_GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("PROOF_AGENT_USE_CLI_LOGIN", raising=False)
    monkeypatch.delenv("CI", raising=False)

    env = copilot_sdk._runtime_env()

    assert copilot_sdk._use_logged_in_user(env) is True


class _StringIO:
    def __init__(self, data):
        self._data = data

    def read(self):
        return self._data
