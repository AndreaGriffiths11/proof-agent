#!/bin/bash
set -e

echo "🤖 Proof Agent — Adversarial Verification"
echo "=========================================="
echo ""

# Read verification prompt
if [ ! -f "verification_prompt.txt" ]; then
    echo "❌ Error: verification_prompt.txt not found"
    exit 1
fi

PROMPT_CONTENT=$(cat verification_prompt.txt)

# Check if this is a SKIP case
if echo "$PROMPT_CONTENT" | grep -q "^SKIP:"; then
    echo "⏭️  Verification skipped (threshold not met)"
    echo "$PROMPT_CONTENT"
    echo ""
    
    VERDICT_TYPE="SKIP"
    VERDICT="$PROMPT_CONTENT"
    
    # Set outputs
    echo "verdict=$VERDICT_TYPE" >> $GITHUB_OUTPUT
    echo "summary<<EOF" >> $GITHUB_OUTPUT
    echo "$VERDICT" >> $GITHUB_OUTPUT
    echo "EOF" >> $GITHUB_OUTPUT
    
    # Post as PR comment if requested
    if [ "$INPUT_POST_COMMENT" = "true" ] && [ -n "$PR_NUMBER" ]; then
        echo "💬 Posting skip notice as PR comment..."
        echo "   Repo: $GITHUB_REPOSITORY"
        echo "   PR: $PR_NUMBER"
        
        # Use GitHub REST API directly
        COMMENT_BODY="## 🤖 Proof Agent Verification

⏭️ **SKIPPED**

$VERDICT

---
*Proof Agent requires ≥3 files changed or sensitive files to trigger verification. Use \`--force\` to verify anyway.*

[🔗 View logs]($RUN_URL)"
        
        # Use the token passed as input (COPILOT_TOKEN via github-token input)
        curl -X POST \
          -H "Accept: application/vnd.github+json" \
          -H "Authorization: Bearer ${INPUT_GITHUB_TOKEN}" \
          -H "X-GitHub-Api-Version: 2022-11-28" \
          "https://api.github.com/repos/$GITHUB_REPOSITORY/issues/$PR_NUMBER/comments" \
          -d "{\"body\":$(echo "$COMMENT_BODY" | jq -Rs .)}" \
          && echo "✅ Comment posted!" \
          || echo "⚠️ Could not post PR comment"
    fi
    
    echo "✨ Verification complete (skipped)!"
    exit 0
fi

echo "📝 Sending verification prompt to GitHub Copilot..."
echo ""

# Check that gh copilot is available
if ! command -v gh &>/dev/null; then
    echo "❌ Error: 'gh' CLI is not installed"
    exit 1
fi
if ! gh copilot --help &>/dev/null; then
    echo "❌ Error: 'gh copilot' extension is not available — install with: gh extension install github/gh-copilot"
    exit 1
fi

# Call GitHub Copilot CLI in non-interactive mode
COPILOT_EXIT=0
VERDICT=$(echo "$PROMPT_CONTENT" | gh copilot 2>&1) || COPILOT_EXIT=$?

if [ "$COPILOT_EXIT" -ne 0 ]; then
    echo "⚠️ gh copilot exited with code $COPILOT_EXIT"
    echo "Output: $VERDICT"
    # Exit code 1 is expected for some non-interactive invocations; anything else is unexpected
    if [ "$COPILOT_EXIT" -gt 1 ]; then
        echo "❌ Unexpected gh copilot failure (exit $COPILOT_EXIT)"
        exit 1
    fi
fi

# Save full verdict
echo "$VERDICT" > verdict.txt
echo "$VERDICT"
echo ""

# Parse Copilot's response for structured verdict headings only
if echo "$VERDICT" | grep -q "### PASS"; then
    VERDICT_TYPE="PASS"
    echo "✅ Verification: PASS"
elif echo "$VERDICT" | grep -q "### FAIL"; then
    VERDICT_TYPE="FAIL"
    echo "❌ Verification: FAIL"
elif echo "$VERDICT" | grep -q "### PARTIAL"; then
    VERDICT_TYPE="PARTIAL"
    echo "⚠️ Verification: PARTIAL"
else
    VERDICT_TYPE="PARTIAL"
    echo "⚠️ Verification: PARTIAL (no structured verdict found, defaulting to PARTIAL)"
fi

# Set outputs
echo "verdict=$VERDICT_TYPE" >> $GITHUB_OUTPUT
echo "summary<<EOF" >> $GITHUB_OUTPUT
echo "$VERDICT" >> $GITHUB_OUTPUT
echo "EOF" >> $GITHUB_OUTPUT

# Post as PR comment if requested
if [ "$INPUT_POST_COMMENT" = "true" ] && [ -n "$PR_NUMBER" ]; then
    echo ""
    echo "💬 Posting verification result as PR comment..."
    
    # Get comment mode and max length
    COMMENT_MODE="${INPUT_COMMENT_MODE:-collapse}"
    MAX_LENGTH="${INPUT_MAX_COMMENT_LENGTH:-2000}"
    
    # Format verdict for PR comment based on mode
    case "$COMMENT_MODE" in
        summary)
            # Summary only: just verdict + key findings
            VERDICT_SUMMARY=$(echo "$VERDICT" | head -20)
            VERDICT_FORMATTED="$VERDICT_SUMMARY

<details>
<summary>Full analysis</summary>

\`\`\`
$VERDICT
\`\`\`

[View full output in action logs]($RUN_URL)
</details>"
            ;;
        collapse)
            # Collapse mode: verdict visible, details collapsed
            VERDICT_FIRST_PARA=$(echo "$VERDICT" | head -10)
            VERDICT_FORMATTED="$VERDICT_FIRST_PARA

<details>
<summary>📋 Full verification details</summary>

\`\`\`
$VERDICT
\`\`\`
</details>

[🔗 View full logs]($RUN_URL)"
            ;;
        full)
            # Full mode: show everything (with truncation if needed)
            VERDICT_FORMATTED="$VERDICT"
            ;;
        *)
            VERDICT_FORMATTED="$VERDICT"
            ;;
    esac
    
    # Truncate if too long
    if [ ${#VERDICT_FORMATTED} -gt "$MAX_LENGTH" ]; then
        VERDICT_FORMATTED="${VERDICT_FORMATTED:0:$MAX_LENGTH}

...*[truncated]*

[📋 View full output in action logs]($RUN_URL)"
    fi
    
    # Verdict badge
    case "$VERDICT_TYPE" in
        PASS)
            VERDICT_BADGE="✅ **PASS**"
            ;;
        FAIL)
            VERDICT_BADGE="❌ **FAIL**"
            ;;
        PARTIAL)
            VERDICT_BADGE="⚠️ **PARTIAL**"
            ;;
        SKIP)
            VERDICT_BADGE="⏭️ **SKIPPED**"
            ;;
        *)
            VERDICT_BADGE="❓ **$VERDICT_TYPE**"
            ;;
    esac
    
    # Use GitHub REST API directly
    COMMENT_BODY="## 🤖 Proof Agent Verification

$VERDICT_BADGE

$VERDICT_FORMATTED

---
*Verified using [Proof Agent](https://github.com/AndreaGriffiths11/proof-agent) with GitHub Copilot*"
    
    # Use the token passed as input (COPILOT_TOKEN via github-token input)
    curl -X POST \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer ${INPUT_GITHUB_TOKEN}" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/$GITHUB_REPOSITORY/issues/$PR_NUMBER/comments" \
      -d "{\"body\":$(echo "$COMMENT_BODY" | jq -Rs .)}" \
      && echo "✅ Comment posted!" \
      || echo "⚠️ Could not post PR comment"
fi

# Block merge if FAIL and block-on-fail is true
if [ "$VERDICT_TYPE" = "FAIL" ] && [ "$INPUT_BLOCK_ON_FAIL" = "true" ]; then
    echo ""
    echo "🚫 Blocking merge due to verification failure"
    exit 1
fi

echo ""
echo "✨ Verification complete!"
