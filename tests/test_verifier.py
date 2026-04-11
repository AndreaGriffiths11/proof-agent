"""Tests for proof_agent.verifier."""
import pytest
from proof_agent.verifier import should_verify, parse_verdict, Verdict
from proof_agent.config import ProofConfig, ThresholdConfig


# --- should_verify ---

class TestShouldVerify:
    def test_under_threshold_skips(self):
        assert should_verify(["a.py", "b.py"]) is False

    def test_at_threshold_verifies(self):
        assert should_verify(["a.py", "b.py", "c.py"]) is True

    def test_above_threshold_verifies(self):
        assert should_verify(["a.py", "b.py", "c.py", "d.py"]) is True

    def test_sensitive_file_always_verifies(self):
        assert should_verify(["src/auth.py"]) is True

    def test_sensitive_dockerfile(self):
        assert should_verify(["Dockerfile"]) is True

    def test_sensitive_env(self):
        assert should_verify([".env.production"]) is True

    def test_never_verify_excluded(self):
        # .gitignore files don't count toward threshold
        assert should_verify([".gitignore", "a.py", "b.py"]) is False

    def test_custom_threshold(self):
        config = ProofConfig(thresholds=ThresholdConfig(min_files_changed=1))
        assert should_verify(["a.py"], config=config) is True

    def test_empty_files(self):
        assert should_verify([]) is False


# --- parse_verdict ---

class TestParseVerdict:
    def test_pass(self):
        result = parse_verdict("Everything ok\n### PASS\nAll good")
        assert result.verdict == Verdict.PASS

    def test_fail_with_issues(self):
        text = "Review:\n### FAIL\n- Bug in auth.py line 5\n- Missing validation\n### Other"
        result = parse_verdict(text)
        assert result.verdict == Verdict.FAIL
        assert len(result.issues) == 2
        assert "Bug in auth.py line 5" in result.issues[0]

    def test_partial(self):
        result = parse_verdict("Some things\n### PARTIAL\nSome passed")
        assert result.verdict == Verdict.PARTIAL

    def test_no_heading_defaults_partial(self):
        result = parse_verdict("No structured verdict here")
        assert result.verdict == Verdict.PARTIAL

    def test_summary_preserved(self):
        text = "Full response text"
        result = parse_verdict(text)
        assert result.summary == text

    def test_fail_issues_extraction_stops_at_next_heading(self):
        text = "### FAIL\n- issue1\n- issue2\n### Notes\n- not an issue"
        result = parse_verdict(text)
        assert len(result.issues) == 2

    def test_prompt_echo_false_fail(self):
        """Regression: Verifier echoes prompt example, uses LAST verdict."""
        text = """Here's an example of a FAIL verdict:

### FAIL
Critical issues found.

But actually, the code is fine:

### PASS
No security issues found.
Code is safe to merge.
"""
        result = parse_verdict(text)
        # Should use LAST occurrence (PASS), not first (FAIL from example)
        assert result.verdict == Verdict.PASS


# --- ProofConfig.load ---

class TestProofConfigLoad:
    def test_defaults_when_no_file(self, tmp_path):
        config = ProofConfig.load(tmp_path / "nonexistent.yaml")
        assert config.thresholds.min_files_changed == 3
        assert config.retry.max_attempts == 3

    def test_load_from_yaml(self, tmp_path):
        f = tmp_path / "proof-agent.yaml"
        f.write_text("thresholds:\n  min_files_changed: 5\nretry:\n  max_attempts: 2\n")
        config = ProofConfig.load(f)
        assert config.thresholds.min_files_changed == 5
        assert config.retry.max_attempts == 2

    def test_partial_yaml(self, tmp_path):
        f = tmp_path / "proof-agent.yaml"
        f.write_text("thresholds:\n  min_files_changed: 10\n")
        config = ProofConfig.load(f)
        assert config.thresholds.min_files_changed == 10
        assert config.retry.max_attempts == 3  # default
