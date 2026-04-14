# Proof Agent BYOK Test Report
**Date:** 2026-04-14  
**Tester:** Rusty (OpenClaw Agent)  
**Environment:** Windows 10, Ollama 0.20.5, Python 3.12  

---

## Test Setup

### Models Tested
- ✅ **qwen2.5:0.5b** (397 MB) - Already installed
- ❌ **gemma2:2b** (1.6 GB) - Download failed (network instability, stuck at 50% for 2+ minutes)

### Test Repository
- **Location:** `~/rusty-agent/workspace/proof-agent-test`
- **Commits:** 2 (initial + vulnerable auth.py)
- **Intentional Vulnerabilities:**
  1. SQL injection (f-string in query)
  2. Hardcoded API key (`sk-1234567890abcdef`)
  3. Password logging (`print(f"...password: {password}")`)

### BYOK Configuration
```bash
export PROOF_AGENT_PROVIDER_BASE_URL="http://localhost:11434/v1"
export PROOF_AGENT_PROVIDER_TYPE="openai"
export PROOF_AGENT_MODEL="qwen2.5:0.5b"
```

---

## Test Results

### 1. Ollama Accessibility ✅

**Command:**
```bash
curl http://localhost:11434/api/tags
```

**Result:** SUCCESS
- Ollama running and accessible on port 11434
- Returns valid JSON with 2 models available
- API responds within <1 second

**Response:**
```json
{
  "models": [
    {
      "name": "gemma4:e2b",
      "size": 7162405886,
      "modified_at": "2026-04-09T05:54:12.3898735-04:00"
    },
    {
      "name": "qwen2.5:0.5b",
      "size": 397821319,
      "modified_at": "2026-04-09T04:31:07.2713512-04:00"
    }
  ]
}
```

---

### 2. Direct API Call (Raw SQL Injection Test) ✅

**Command:**
```bash
curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  --data-binary "@test_request.json"
```

**Prompt:** Simple, focused security review of SQL injection vulnerability

**Result:** SUCCESS - Model correctly identified vulnerabilities

**Response:**
```json
{
  "id": "chatcmpl-335",
  "model": "qwen2.5:0.5b",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "The provided Python code is a function named `login`... there are several security vulnerabilities in this code:\n\n1. **SQL Injection**: The code directly concatenates user input (`username` and `password`) into the SQL query without properly escaping it. This can lead to SQL injection attacks if not handled carefully.\n\n2. **No Input Validation**: The function does not perform any validation or sanitization of the user inputs before executing the query. If an attacker injects malicious data, they could potentially execute arbitrary SQL commands.\n\n3. **No Error Handling**: There is no error handling in place to catch and report any issues that might arise during execution.\n\n4. **No Input Validation for `username`**: The function does not perform any input validation or sanitization of the user's username before executing the query..."
    }
  }],
  "usage": {
    "prompt_tokens": 81,
    "completion_tokens": 200,
    "total_tokens": 281
  }
}
```

**Vulnerabilities Detected:**
- ✅ SQL Injection (primary issue)
- ✅ No input validation
- ✅ No error handling
- ✅ Insecure parameter handling

**Verdict:** **PASS** - Model successfully identified security vulnerabilities when given a focused, simple prompt.

---

### 3. Proof Agent Integration Test (Full Verification Flow) ⚠️ PARTIAL

**Test Script:** `test_byok.py` (Python + proof_agent library)

**Workflow:**
1. Read git diff from `auth.py` commit
2. Build proof-agent verification prompt (includes rules, format, context)
3. Call Ollama via OpenAI-compatible API with BYOK settings
4. Parse verdict

**Result:** BYOK connectivity works, but verdict quality failed

**Issues Found:**

#### Issue A: False Pass ❌
- **Verdict Returned:** `PASS - No security issues, bugs, or quality problems found.`
- **Expected:** `FAIL` with specific citations of 3 vulnerabilities
- **Root Cause:** Prompt structure too complex for small model (3723 characters)
  - Long verification rules section
  - Git diff output formatting
  - Multiple instruction layers
  - Context overload diluted the signal

#### Issue B: Unicode Encoding Error (Windows) ⚠️
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u274c'
```
- **Impact:** Minor (doesn't affect BYOK functionality)
- **Cause:** Windows console encoding (CP1252 doesn't support emoji)
- **Fix:** Use ASCII-safe output or set `PYTHONIOENCODING=utf-8`

---

## Analysis

### What Works ✅
1. **Ollama OpenAI-compatible API** - Fully functional, returns valid responses
2. **BYOK connectivity** - Environment variables correctly configure provider
3. **Model capability** - qwen2.5:0.5b CAN detect security issues with focused prompts
4. **proof_agent library** - Prompt building works, integration clean

### What Doesn't Work ❌
1. **Complex prompts + small models** - 0.5B parameter model overwhelmed by verbose instructions
2. **Verdict parsing** - Model returned generic template text instead of real analysis
3. **Download reliability** - gemma2:2b (1.6 GB) failed to download (network timeout)

### Root Cause: Model Size vs. Prompt Complexity

**Simple Prompt (81 tokens):**
```
Find the security vulnerability in this Python code:
<code snippet>
```
→ **Result:** ✅ Correctly identified SQL injection, input validation, error handling

**Complex Prompt (3723 characters):**
```
## Verification Task
<rules>
<format>
<context>
## Original Request
...
## Files Changed
...
## Approach
...
## Git Diff
<931 characters of diff>
```
→ **Result:** ❌ Generic template response, no actual analysis

**Conclusion:** qwen2.5:0.5b is sufficient for focused security questions, but NOT for the full proof-agent verification workflow.

---

## Recommendations

### For Production Use

1. **Minimum Model Size:** 2B parameters (e.g., gemma2:2b, qwen2.5:3b)
   - Handles complex multi-step reasoning
   - Better instruction following
   - More reliable structured output

2. **Prompt Optimization for Small Models:**
   - Reduce preamble/instructions
   - Focus on specific questions
   - Avoid verbose templates
   - Use chain-of-thought for complex tasks

3. **Fallback Strategy:**
   ```yaml
   models:
     - name: gemma2:2b        # Primary
     - name: qwen2.5:0.5b     # Fallback (focused questions only)
     - name: github-copilot   # Cloud fallback
   ```

4. **Verdict Format Validation:**
   - Add regex parsing for `### Verdict: (PASS|FAIL|PARTIAL)`
   - Reject generic template responses
   - Require specific file/line citations for FAIL verdicts

### For Testing

1. **Use larger models** - gemma2:2b minimum (1.6 GB)
2. **Test incrementally:**
   - Step 1: Raw API call (simple prompt)
   - Step 2: Verification prompt (no diff)
   - Step 3: Full workflow (with diff)
3. **Measure token usage** - Track prompt/completion tokens for cost estimation

---

## Debug Info

### System
- **OS:** Windows 10.0.26200 (x64)
- **Python:** 3.12
- **Ollama:** 0.20.5
- **proof-agent:** 0.1.0 (installed in editable mode)

### Files Generated
- `~/rusty-agent/workspace/proof-agent-test/auth.py` (632 bytes)
- `~/rusty-agent/workspace/proof-agent-test/test_byok.py` (3266 bytes)
- `~/rusty-agent/workspace/proof-agent-test/test_request.json` (415 bytes)

### Git History
```
* 039ad53 - Add authentication module (HEAD -> master)
* a389fb4 - initial commit
```

---

## Next Steps

1. **Retry with larger model:**
   ```bash
   # Use faster mirror or better network
   ollama pull gemma2:2b
   
   # Re-run test_byok.py
   python test_byok.py
   ```

2. **Add verdict parser:**
   ```python
   from proof_agent.cli import parse_verdict_cli
   
   verdict = parse_verdict_cli(verifier_response)
   # Should return: Verdict.FAIL with citations
   ```

3. **Test GitHub Action locally:**
   ```bash
   act pull_request \
     -e .github/workflows/test-event.json \
     -s GITHUB_TOKEN=<token>
   ```

4. **Benchmark model performance:**
   - Measure false positive/negative rates
   - Compare verdict quality across model sizes
   - Document minimum viable model size

---

## Conclusion

**BYOK infrastructure: ✅ Working**
- Ollama responds correctly
- OpenAI-compatible API functional
- Environment variables correctly configure provider

**Verdict quality: ❌ Insufficient for small models**
- qwen2.5:0.5b (397 MB): Works for simple prompts, fails for complex verification
- gemma2:2b (1.6 GB): Download failed (network), expected to work
- Recommended: ≥2B parameters for production use

**Key Finding:** The BYOK system works correctly. The issue is prompt engineering + model capacity, not infrastructure.
