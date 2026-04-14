#!/usr/bin/env python3
"""
Test BYOK (Bring Your Own Key) with Ollama + proof-agent verifier.
"""

import os
import subprocess
from proof_agent.verifier import build_verification_prompt, VerificationRequest

# Set BYOK environment variables
os.environ["PROOF_AGENT_PROVIDER_BASE_URL"] = "http://localhost:11434/v1"
os.environ["PROOF_AGENT_PROVIDER_TYPE"] = "openai"
os.environ["PROOF_AGENT_MODEL"] = "qwen2.5:0.5b"

def get_git_diff():
    """Get the diff for the last commit."""
    result = subprocess.run(
        ["git", "show", "HEAD"],
        capture_output=True,
        text=True,
        cwd=os.getcwd()
    )
    return result.stdout

def main():
    print("=" * 60)
    print("BYOK Test: Proof Agent + Ollama")
    print("=" * 60)
    
    # Get diff
    print("\n[1] Getting git diff...")
    diff = get_git_diff()
    print(f"Diff size: {len(diff)} characters")
    
    # Build verification request
    print("\n[2] Building verification request...")
    request = VerificationRequest(
        original_request="Add secure authentication",
        files_changed=["auth.py"],
        approach="Added SQL-based login system with password hashing and secure storage"
    )
    
    # Generate verification prompt
    print("\n[3] Generating verification prompt...")
    prompt = build_verification_prompt(request)
    
    # Add diff to prompt
    full_prompt = f"""{prompt}

## Git Diff
```diff
{diff}
```

Review the above changes and provide your verdict."""
    
    print(f"Prompt size: {len(full_prompt)} characters")
    print("\n[4] Calling Ollama with BYOK settings...")
    print(f"   Provider: {os.environ['PROOF_AGENT_PROVIDER_TYPE']}")
    print(f"   Base URL: {os.environ['PROOF_AGENT_PROVIDER_BASE_URL']}")
    print(f"   Model: {os.environ['PROOF_AGENT_MODEL']}")
    
    # Call Ollama via OpenAI-compatible API
    try:
        import openai
        client = openai.OpenAI(
            base_url=os.environ["PROOF_AGENT_PROVIDER_BASE_URL"],
            api_key="dummy"  # Ollama doesn't need a real key
        )
        
        response = client.chat.completions.create(
            model=os.environ["PROOF_AGENT_MODEL"],
            messages=[
                {"role": "system", "content": "You are a security-focused code verifier. You find vulnerabilities and provide clear, actionable verdicts."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        verdict_text = response.choices[0].message.content
        print("\n[5] Verifier Response:")
        print("=" * 60)
        print(verdict_text)
        print("=" * 60)
        
        # Check for security issues
        if "SQL injection" in verdict_text or "hardcoded" in verdict_text.lower() or "password" in verdict_text.lower():
            print("\n✅ SUCCESS: Verifier detected security issues!")
            print("BYOK_STATUS=0")
            return 0
        else:
            print("\n❌ PARTIAL: Verifier response unclear")
            print("BYOK_STATUS=1")
            return 1
            
    except Exception as e:
        print(f"\n❌ FAIL: Error calling Ollama: {e}")
        print("BYOK_STATUS=1")
        return 1

if __name__ == "__main__":
    exit(main())
