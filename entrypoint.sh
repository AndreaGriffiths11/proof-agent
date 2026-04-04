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

echo ""

# NOTE: `gh copilot` is an interactive CLI — it does NOT accept stdin pipes
# and has no non-interactive/batch mode. Piping to it will fail or hang in CI.
#
# Approach: We use the GitHub Models API via `gh api` as a non-interactive
# alternative. If GH_COPILOT_MODEL is not set, we fall back to writing the
# prompt to an artifact for manual review.
#
# To use a different model endpoint, set PROOF_AGENT_API_URL and
# PROOF_AGENT_API_MODEL environment variables.

COPILOT_MODEL="${GH_COPILOT_MODEL:-openai/gpt-4o}"
API_URL="${PROOF_AGENT_API_URL:-https://models.github.ai/inference/chat/completions}"

echo "📝 Sending verification prompt via GitHub Models API (model: $COPILOT_MODEL)..."
echo ""

PAYLOAD=$(jq -n --arg model "$COPILOT_MODEL" --arg content "$PROMPT_CONTENT" \
  '{model: $model, messages: [{role: "user", content: $content}]}')

COPILOT_EXIT=0
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer ${INPUT_GITHUB_TOKEN}" \
  -H "Content-Type: application/json" \
  "$API_URL" \
  -d "$PAYLOAD") || COPILOT_EXIT=$?

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$COPILOT_EXIT" -ne 0 ] || [ "$HTTP_CODE" -ge 400 ]; then
    echo "⚠️ API call failed (HTTP $HTTP_CODE, exit $COPILOT_EXIT)"
    echo ""
    echo "Falling back to manual review mode — prompt saved to verification_prompt.txt"
    echo "Review the prompt manually and assign a verdict."
    echo ""
    VERDICT="### PARTIAL\nAPI call failed. Manual review required.\nSee verification_prompt.txt for the full prompt."
    VERDICT=$(printf '%b' "$VERDICT")
else
    VERDICT=$(echo "$BODY" | jq -r '.choices[0].message.content // "No content in response"')
fi

# Save full verdict
echo "$VERDICT" > verdict.txt
echo "$VERDICT"
echo ""

# Parse verdict using the Python package (single source of truth)
VERDICT_TYPE=$(python3 -c "
from proof_agent.verifier import parse_verdict
import sys
result = parse_verdict(sys.stdin.read())
print(result.verdict.value.upper())
" <<< "$VERDICT")

case "$VERDICT_TYPE" in
    PASS)    echo "✅ Verification: PASS" ;;
    FAIL)    echo "❌ Verification: FAIL" ;;
    PARTIAL) echo "⚠️ Verification: PARTIAL" ;;
    *)       VERDICT_TYPE="PARTIAL"; echo "⚠️ Verification: PARTIAL (unexpected parse result)" ;;
esac

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
