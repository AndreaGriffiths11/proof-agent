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


class _StringIO:
    def __init__(self, data):
        self._data = data

    def read(self):
        return self._data
