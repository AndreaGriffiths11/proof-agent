# Proof Agent

**Adversarial verification for AI-generated work.**

The worker and the verifier are always separate agents. Self-verification is not verification.

---

## The Problem

AI agents generate code that breaks in production. They hallucinate package versions. They make security claims that fall apart under scrutiny. And when you ask them to verify their own work? They rationalize the mistakes instead of catching them.

Self-verification doesn't work because the same model that made the error will defend it.

---

## How It Works

Proof Agent enforces separation:

1. **Worker agent** makes changes
2. **Verifier agent** (separate, independent) checks the work
3. Verifier runs commands, checks facts, assigns a verdict

The verifier has no access to the worker's self-assessment. It must verify with evidence.

**Verdicts:**
- **PASS** — All checks passed with evidence
- **FAIL** — Issues found. Report specifics. Retry up to 3 times if auto-fixable.
- **PARTIAL** — Some checks passed, others couldn't be verified

---

## What It Checks

- **Correctness** — Does the code do what was requested?
- **Bugs & Edge Cases** — Regressions, unhandled errors, missed cases?
- **Security** — Vulnerabilities, exposed secrets, permission issues?
- **Build** — Does it build/compile/lint cleanly?
- **Facts** — Are claims, version numbers, URLs verifiable?

**Rule:** No PASS without ≥3 verification commands with evidence.

---

## Quick Start

### GitHub Action (Zero Setup)

Add this workflow to your repo:

**`.github/workflows/proof-agent.yml`:**
```yaml
name: Proof Agent

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  models: read  # Required for GitHub Models API

jobs:
  verify:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - uses: AndreaGriffiths11/proof-agent@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          base-ref: origin/main
          block-on-fail: true
          post-comment: true
```

That's it. Every PR gets automatic verification.

**Uses GitHub Models API (free tier).** No API keys or tokens needed.

---

### OpenClaw Skill (Interactive)

```bash
clawhub install proof-agent
```

Talk to your agent:

> "I added OAuth login. Verify it's safe."

The agent spawns a verifier subagent and runs checks.

---

### Command Line (Manual)

```bash
git clone https://github.com/AndreaGriffiths11/proof-agent.git
cd proof-agent

# Generate verification prompt
bash scripts/verify.sh > verification_prompt.txt

# Send to your LLM
cat verification_prompt.txt | your-llm-cli
```

---

## Configuration

### Action Inputs

```yaml
- uses: AndreaGriffiths11/proof-agent@main
  with:
    # GitHub token (use built-in GITHUB_TOKEN)
    github-token: ${{ secrets.GITHUB_TOKEN }}
    
    # Git ref to compare against
    base-ref: origin/main
    
    # Block PR merge if FAIL
    block-on-fail: true
    
    # Post verdict as PR comment
    post-comment: true
    
    # Comment format: collapse (default), summary, or full
    comment-mode: collapse
    
    # Max comment length in characters
    max-comment-length: 2000
```

**Comment modes:**
- `collapse` — First paragraph visible, rest in expandable section
- `summary` — Verdict + key findings only
- `full` — Everything visible (truncates at max-comment-length)

---

### Proof Agent Config (proof-agent.yaml)

Customize thresholds and patterns:

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

---

## When Verification Triggers

**Auto-verify when:**
- ≥3 files changed
- ANY file matches: `*auth*`, `*secret*`, `*permission*`, `Dockerfile`, `*.env*`
- User explicitly requests verification

**Skip for:**
- Formatting-only changes
- `.gitignore` changes

---

## Example Workflow

**Scenario:** AI agent writes authentication code

1. **Worker agent** generates `src/auth.py`, `tests/test_auth.py`, updates `requirements.txt`
2. **Proof Agent** detects: 3+ files changed + `*auth*` pattern → triggers verification
3. **Verifier agent** spawns, receives:
   - Original request
   - Files changed
   - Approach taken
4. **Verifier runs:**
   ```bash
   python -m pytest tests/test_auth.py -v
   grep -r "secret\|password\|token" src/auth.py
   pip install -r requirements.txt --dry-run
   ```
5. **Verifier finds:**
   - Tests pass
   - Hardcoded API key in `src/auth.py:42`
   - Dependencies install cleanly
6. **Verdict:** **FAIL** — Security issue (hardcoded secret)
7. **Proof Agent** spawns worker to fix → re-verifies → **PASS**

---

## Troubleshooting

### Action fails with "No access to model"

**Check workflow permissions:**
```yaml
permissions:
  contents: read
  pull-requests: write
  models: read  # ← Required for GitHub Models API
```

**Verify GitHub Models is enabled:**
- Go to https://github.com/marketplace?type=models
- Confirm you can access models (free tier available)

---

### PR comment not posted (403/404 error)

**Check workflow permissions:**
```yaml
permissions:
  pull-requests: write  # ← Required for posting comments
  contents: read
  models: read
```

For private repos, use `secrets.GITHUB_TOKEN` (already has correct permissions).

---

### SKIP on every PR

Proof Agent skips if <3 files changed AND no sensitive files detected.

**To force verification:**
- Change 3+ files, OR
- Touch a sensitive file: `*auth*`, `*secret*`, `Dockerfile`, `*.env*`

---

## Why Adversarial Verification?

**Single-agent limitations:**
- Same model that made the mistake will rationalize it
- Confirmation bias in self-review
- No incentive to find flaws

**Adversarial separation:**
- Verifier has no stake in worker's success
- Forced to provide evidence
- Different prompts catch different issues

**Real-world analogy:**
- Code review (separate developer)
- Security audit (external team)
- Peer review (different researcher)

---

## License

MIT — Andrea Griffiths, 2026
