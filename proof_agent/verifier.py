"""
Core verification logic.

Determines whether work needs verification, builds verification prompts,
and parses verifier responses.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .config import ProofConfig


class Verdict(Enum):
    """Possible verification outcomes."""
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"


@dataclass
class VerificationRequest:
    """Everything the verifier needs to review."""
    original_request: str
    files_changed: list[str]
    approach: str
    previous_failures: list[str] = field(default_factory=list)
    attempt: int = 1


@dataclass
class VerificationResult:
    """The verifier's verdict and evidence."""
    verdict: Verdict
    summary: str
    issues: list[str] = field(default_factory=list)
    unverifiable: list[str] = field(default_factory=list)


def should_verify(
    files_changed: list[str],
    config: Optional[ProofConfig] = None,
) -> bool:
    """Determine if work requires verification.

    Returns True if:
    - Any file matches always_verify patterns, OR
    - Number of non-excluded files >= min_files_changed threshold
    """
    if config is None:
        config = ProofConfig()

    # Check always_verify first
    for f in files_changed:
        if config.matches_always_verify(f):
            return True

    # Count files excluding never_verify
    significant = [f for f in files_changed if not config.matches_never_verify(f)]
    return len(significant) >= config.thresholds.min_files_changed


def build_verification_prompt(request: VerificationRequest) -> str:
    """Build the prompt for the verifier agent.

    The prompt is structured so the verifier:
    1. Cannot see the worker's self-assessment
    2. Must run commands and include output
    3. Must assign exactly one verdict
    """
    files_list = "\n".join(f"- `{f}`" for f in request.files_changed)

    previous = ""
    if request.previous_failures:
        items = "\n".join(f"- {f}" for f in request.previous_failures)
        previous = f"""
## Previous Failures (Attempt {request.attempt})
These issues were found in previous verification. Check these FIRST:
{items}
"""

    return f"""VERIFICATION REQUEST

## Original Request
{request.original_request}

## Files Changed
{files_list}

## Approach Taken
{request.approach}
{previous}
## Your Job

You are an **independent security auditor** conducting adversarial code review. The author CANNOT verify their own work — only you can assign a verdict.

**CRITICAL:** You are reviewing the actual diff output. You CANNOT run commands or execute tests. Review the code changes directly.

### Review Checklist

Review each changed file for:

1. **Security Vulnerabilities**
   - SQL injection (string interpolation in queries)
   - Hardcoded secrets (API keys, passwords, tokens)
   - Exposed credentials (logging passwords, returning secrets)
   - Authentication bypasses (broken logic, missing checks)
   - Path traversal (unsanitized file paths)
   - Command injection (shell execution with user input)
   - XSS/CSRF vulnerabilities
   - Insecure cryptography (weak algorithms, bad practices)

2. **Correctness**
   - Does the code match the stated purpose?
   - Are there logical errors or broken assumptions?
   - Will it work with edge cases (null, empty, malformed input)?

3. **Code Quality**
   - Are there obvious bugs (typos, copy-paste errors, undefined variables)?
   - Is error handling present and correct?
   - Are there race conditions or concurrency issues?

### Critical Rules

- **Review the actual code in the diff** — do NOT suggest running commands
- **Be specific** — cite file names, line numbers, and exact code snippets
- **Assume production use** — treat everything as security-sensitive
- **Default to FAIL** — if you find ANY critical security issue, return FAIL immediately
- **Use the exact verdict format** — `### PASS`, `### FAIL`, or `### PARTIAL`

## Verdict Format

You MUST respond with EXACTLY ONE of these verdict blocks:

### PASS
No security issues, bugs, or quality problems found.
Code is safe to merge.

(Use this ONLY if the code is actually safe. Finding even one security issue = FAIL.)

### FAIL
Critical issues found. DO NOT MERGE.

**Issues:**
- **File:** `path/to/file.js`, **Line:** 42  
  **Severity:** CRITICAL  
  **Issue:** SQL injection vulnerability - user input directly interpolated into query  
  **Code:** `query = "SELECT * FROM users WHERE name = '" + userName + "'"`  
  **Fix:** Use parameterized queries

(Include ALL issues found. Be specific. Cite actual code.)

### PARTIAL
Could not complete verification due to missing context.

**What was checked:**
- (list what you successfully reviewed)

**What could not be verified:**
- (list what needs human review)
- What passed (with evidence)
- What could not be verified (with explanation of why)
"""


def parse_verdict(response: str) -> VerificationResult:
    """Parse a verifier's response into a structured result.

    Looks for verdict keywords and extracts issues/evidence.
    """
    response_lower = response.lower()

    # Determine verdict — anchor to structured format only
    if "### fail" in response_lower:
        verdict = Verdict.FAIL
    elif "### partial" in response_lower:
        verdict = Verdict.PARTIAL
    elif "### pass" in response_lower:
        verdict = Verdict.PASS
    else:
        # If no structured heading found, default to PARTIAL (safe)
        verdict = Verdict.PARTIAL

    # Extract issues (lines starting with - after FAIL section)
    issues: list[str] = []
    in_fail = False
    for line in response.split("\n"):
        if "FAIL" in line and "#" in line:
            in_fail = True
            continue
        if in_fail and line.strip().startswith("-"):
            issues.append(line.strip().lstrip("- "))
        if in_fail and line.strip().startswith("#"):
            in_fail = False

    # Extract unverifiable items (for PARTIAL)
    unverifiable: list[str] = []
    in_unverified = False
    for line in response.split("\n"):
        if "could not be verified" in line.lower() or "unverifiable" in line.lower():
            in_unverified = True
            continue
        if in_unverified and line.strip().startswith("-"):
            unverifiable.append(line.strip().lstrip("- "))
        if in_unverified and line.strip().startswith("#"):
            in_unverified = False

    return VerificationResult(
        verdict=verdict,
        summary=response,
        issues=issues,
        unverifiable=unverifiable,
    )
