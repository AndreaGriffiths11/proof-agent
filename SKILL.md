---
name: proof-agent
description: Adversarial verification of AI-generated work. Spawns an independent verifier to check for false claims, broken code, and security issues.
---

# Proof Agent

Independent adversarial verification for AI work. The worker and the verifier are always separate agents — self-verification is not verification.

## When to Verify

Verify automatically when:
- Subagent changed **3+ files**
- ANY changed file matches: `*auth*`, `*secret*`, `*permission*`, `Dockerfile`, `*.env*`
- User explicitly asks for verification

Skip verification for:
- Formatting-only changes (whitespace, linting fixes)
- `.gitignore` changes

## How to Verify

Use the sealed prompt generator and Copilot verifier pipeline:

```bash
bash scripts/verify.sh [base-ref] | proof-agent-verify-copilot
```

When the threshold is not met, the verifier prints the `SKIP:` notice without
contacting Copilot.

GitHub Actions authenticates with `GITHUB_TOKEN` or `COPILOT_GITHUB_TOKEN` and
fails closed when neither is set. To explicitly use an existing Copilot CLI
login in CI, set `PROOF_AGENT_USE_CLI_LOGIN=1`.

The worker must not replace this pipeline with a hand-written verification
prompt or share its self-assessment with the verifier.

## Verdicts

- **PASS** — All checks passed with evidence
- **FAIL** — Issues found. Report to user with specifics. Retry up to 3 times if fixable.
- **PARTIAL** — Some checks passed, others couldn't be verified. Report what's unverifiable.

## After Verification

- **PASS**: Report summary to user, proceed
- **FAIL**: Report issues to user. If auto-fixable, spawn worker to fix, then re-verify (max 3 attempts)
- **PARTIAL**: Report to user, let them decide whether to proceed

## Scripts

### `scripts/verify.sh [base-ref] [--force]`
Auto-extracts git diff, changed files, commit messages, and sensitive file detection. Outputs a filled static-review prompt ready to send to the verifier subagent. Default base: `HEAD~1`.

```bash
bash scripts/verify.sh         # verify last commit
bash scripts/verify.sh main    # verify all changes since main
bash scripts/verify.sh main --force
```

### `scripts/fact-check.sh <file> [file2 ...]`
Extracts and validates factual claims from files:
- URLs → HTTP status check
- npm packages → registry version lookup
- GitHub Actions → tag/SHA existence check

```bash
bash scripts/fact-check.sh src/content/articles/en/my-article.md
bash scripts/fact-check.sh .github/workflows/*.yml
```

Returns exit code 1 if any checks fail.

## Configuration

Projects can customize via `proof-agent.yaml` in the repo root (loaded by `proof_agent/config.py`):

```yaml
thresholds:
  min_files_changed: 3
  always_verify:
    - "**/*auth*"
    - "**/*secret*"
    - "**/*permission*"
    - "**/Dockerfile"
    - "**/*.env*"
  never_verify:
    - "**/.gitignore"

retry:
  max_attempts: 3
  escalate_on_max: true
```

## Key Principle

> The worker and verifier must be separate agents. Self-verification is not verification.
