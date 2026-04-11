"""Tests for proof_agent.cli."""
import subprocess
import sys
import pytest


class TestParseVerdictCLI:
    """Test the proof-agent-parse-verdict CLI command."""
    
    def test_pass_verdict(self):
        """CLI should output PASS for pass verdict."""
        input_text = "Everything ok\n### PASS\nAll good"
        result = subprocess.run(
            [sys.executable, "-m", "proof_agent.cli", "parse-verdict"],
            input=input_text,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "PASS"
    
    def test_fail_verdict(self):
        """CLI should output FAIL for fail verdict."""
        input_text = "Review:\n### FAIL\n- Bug found\n"
        result = subprocess.run(
            [sys.executable, "-m", "proof_agent.cli", "parse-verdict"],
            input=input_text,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "FAIL"
    
    def test_partial_verdict(self):
        """CLI should output PARTIAL for partial verdict."""
        input_text = "Some things\n### PARTIAL\nSome passed"
        result = subprocess.run(
            [sys.executable, "-m", "proof_agent.cli", "parse-verdict"],
            input=input_text,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "PARTIAL"
    
    def test_no_verdict_defaults_partial(self):
        """CLI should output PARTIAL when no structured verdict found."""
        input_text = "No structured verdict here"
        result = subprocess.run(
            [sys.executable, "-m", "proof_agent.cli", "parse-verdict"],
            input=input_text,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "PARTIAL"
    
    def test_prompt_echo_uses_last_verdict(self):
        """CLI should use LAST verdict occurrence (avoid prompt-echo bug)."""
        input_text = """Here's an example of a FAIL verdict:

### FAIL
Critical issues found.

But actually, the code is fine:

### PASS
No security issues found.
Code is safe to merge.
"""
        result = subprocess.run(
            [sys.executable, "-m", "proof_agent.cli", "parse-verdict"],
            input=input_text,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "PASS"  # Should use last, not first
    
    def test_empty_input_fallback(self):
        """CLI should handle empty input gracefully."""
        result = subprocess.run(
            [sys.executable, "-m", "proof_agent.cli", "parse-verdict"],
            input="",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "PARTIAL"  # Safe fallback
