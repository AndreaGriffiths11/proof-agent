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

1. Create a Fine-Grained Personal Access Token:
   - **[Create token here](https://github.com/settings/personal-access-tokens/new)**
   - **Repository permissions:**
     - Pull requests: Read and write
     - Contents: Read
     - Issues: Read and write
   - **Account permissions:**
     - Copilot Requests: Read and write

2. Add token as repository secret:
   ```bash
   gh secret set COPILOT_TOKEN --body "YOUR_TOKEN_HERE" --repo OWNER/REPO
   ```

3. Create `.github/workflows/proof-agent.yml`:
   ```yaml
   name: Proof Agent

   on:
     pull_request:
       types: [opened, synchronize, reopened]

   permissions:
     contents: read
     pull-requests: write

   jobs:
     verify:
       runs-on: ubuntu-latest
       
       steps:
         - uses: actions/checkout@v4
           with:
             fetch-depth: 0
         
         - uses: AndreaGriffiths11/proof-agent@main
           with:
             github-token: ${{ secrets.COPILOT_TOKEN }}
             base-ref: origin/main
             block-on-fail: true
             post-comment: true
   ```

That's it. Every PR gets automatic verification.

**Uses your GitHub Copilot license.** No extra API costs.

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
    # Token with Copilot + repo access
    github-token: ${{ secrets.COPILOT_TOKEN }}
    
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

### Action fails with "Authentication failed"

**Check token permissions:**
- [Your Personal Access Tokens](https://github.com/settings/tokens)
- Edit your token
- Ensure **Copilot Requests** is set to **Read and write**

**Verify token is set:**
```bash
gh secret list --repo OWNER/REPO
```

**Regenerate if expired:**
- [Create new Fine-Grained PAT](https://github.com/settings/personal-access-tokens/new)
- Update secret: `gh secret set COPILOT_TOKEN --body "NEW_TOKEN"`

---

### PR comment not posted (404 error)

Token needs `repo` scope for private repos or `pull-requests: write` for public repos.

**Fine-Grained PAT:**
- Repository permissions → Pull requests: Read and write
- Repository permissions → Issues: Read and write

**Classic PAT:**
- Scope: `repo`

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
