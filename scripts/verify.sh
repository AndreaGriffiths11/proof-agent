#!/usr/bin/env bash
# verify.sh — Auto-extract context for proof-agent verification
# Usage: ./verify.sh [base-ref]
# Default base-ref: HEAD~1 (last commit)
#
# Outputs a filled verification prompt to stdout.

set -euo pipefail

BASE="${1:-HEAD~1}"

# Get changed files
FILES=$(git diff --name-only "$BASE" HEAD 2>/dev/null || git diff --name-only --cached 2>/dev/null || echo "(no git changes detected)")

# Count
FILE_COUNT=$(echo "$FILES" | grep -c '.' || echo 0)

# Get diff output (full unified diff with context)
DIFF=$(git diff "$BASE" HEAD 2>/dev/null || echo "(no diff available)")

# Get commit messages since base
COMMITS=$(git log --oneline "$BASE"..HEAD 2>/dev/null || echo "(no commits)")

# Determine if verification is needed using the Python package (single source of truth)
# Use stdin to avoid shell injection from filenames
SHOULD_VERIFY=$(echo "$FILES" | python3 -c "
import sys
import json
from proof_agent.verifier import should_verify

files = [line.strip() for line in sys.stdin if line.strip()]
print('true' if should_verify(files) else 'false')
")

if [ "$SHOULD_VERIFY" = false ]; then
  echo "SKIP: Only $FILE_COUNT file(s) changed, no sensitive files detected."
  echo "Use --force or run manually to verify anyway."
  exit 0
fi

# Build the prompt using the Python function (single source of truth)
python3 -c "
from proof_agent.verifier import build_verification_prompt, VerificationRequest
import sys

files_changed = '''$FILES'''.strip().split('\n')
diff_text = '''$DIFF'''
commits = '''$COMMITS'''

# Build request
request = VerificationRequest(
    original_request=f'''Code changes across {len(files_changed)} file(s):\n{commits}''',
    files_changed=files_changed,
    approach=f'''Changes made via git commits.\n\nDiff output:\n{diff_text}''',
    attempt=1,
    previous_failures=[]
)

print(build_verification_prompt(request))
"
