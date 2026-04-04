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

You are an **independent verifier**. The worker who made these changes CANNOT verify their own work — only you can assign a verdict.

### Review Checklist
1. **Correctness**: Does the code actually do what was requested?
2. **Bugs & Edge Cases**: Are there regressions, unhandled errors, or missed cases?
3. **Security**: Are there vulnerabilities, exposed secrets, or permission issues?
4. **Build**: Does it build/compile/lint cleanly?

### Rules
- For EVERY check, include the **actual command you ran** and its **output**.
- Do NOT take the worker's word for anything.
- Do NOT give PASS without running at least 3 verification commands.
- You have NO information about the worker's test results — verify independently.

## Verdict

Assign EXACTLY ONE:

### PASS
All checks passed. Every claim is backed by command output.

### FAIL
Issues found. For each issue:
- File and line number
- What's wrong
- Severity (critical / major / minor)

### PARTIAL
Some checks passed, others could not be verified.
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
