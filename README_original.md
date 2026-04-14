# Proof Agent v2.0 — BYOK Support 🔑

**Adversarial verification for AI-generated code with Bring Your Own Key support**

## What's New in v2.0

✨ **BYOK (Bring Your Own Key)** — Use your own model providers:
- **Anthropic Claude** (direct API)
- **Azure OpenAI** (enterprise accounts)
- **Local models** (Ollama, vLLM)
- **IBM Foundry** (enterprise AI)
- **Any OpenAI-compatible endpoint**

✨ **Dual model support** — Use different models for worker vs verifier
✨ **Cost optimization** — Route to cheaper providers 
✨ **Backward compatible** — GitHub Models still work by default

## Quick Start

### Default (GitHub Models)
```yaml
- name: Proof Agent Verification
  uses: AndreaGriffiths11/proof-agent@v2.0
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

### BYOK Examples

#### Anthropic Claude
```yaml
- name: Proof Agent Verification  
  uses: AndreaGriffiths11/proof-agent@v2.0
  env:
    PROOF_AGENT_PROVIDER_BASE_URL: https://api.anthropic.com
    PROOF_AGENT_PROVIDER_TYPE: anthropic
    PROOF_AGENT_PROVIDER_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    PROOF_AGENT_MODEL: claude-sonnet-4-20250514
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

#### Azure OpenAI
```yaml
- name: Proof Agent Verification
  uses: AndreaGriffiths11/proof-agent@v2.0
  env:
    PROOF_AGENT_PROVIDER_TYPE: azure
    PROOF_AGENT_PROVIDER_BASE_URL: https://mycompany.openai.azure.com
    PROOF_AGENT_PROVIDER_API_KEY: ${{ secrets.AZURE_OPENAI_KEY }}
    PROOF_AGENT_MODEL: gpt-4-turbo
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

#### Local Ollama
```yaml
- name: Proof Agent Verification
  uses: AndreaGriffiths11/proof-agent@v2.0
  env:
    PROOF_AGENT_PROVIDER_BASE_URL: http://localhost:11434/v1
    PROOF_AGENT_MODEL: deepseek-coder-v2:16b
    # No API key needed for local
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

#### IBM Foundry
```yaml
- name: Proof Agent Verification
  uses: AndreaGriffiths11/proof-agent@v2.0  
  env:
    PROOF_AGENT_PROVIDER_BASE_URL: https://us-south.ml.cloud.ibm.com/ml/v1
    PROOF_AGENT_PROVIDER_TYPE: foundry
    PROOF_AGENT_PROVIDER_API_KEY: ${{ secrets.FOUNDRY_API_KEY }}
    PROOF_AGENT_MODEL: meta-llama/llama-3-70b-instruct
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

#### Dual Model Setup
```yaml
- name: Proof Agent Verification
  uses: AndreaGriffiths11/proof-agent@v2.0
  env:
    PROOF_AGENT_PROVIDER_BASE_URL: https://api.anthropic.com
    PROOF_AGENT_PROVIDER_TYPE: anthropic
    PROOF_AGENT_PROVIDER_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    PROOF_AGENT_MODEL: claude-haiku-4-20250514              # Fast for worker
    PROOF_AGENT_VERIFIER_MODEL: claude-sonnet-4-20250514   # Thorough for verifier
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Environment Variables

### Core BYOK Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `PROOF_AGENT_PROVIDER_BASE_URL` | Provider API endpoint (enables BYOK) | *(none)* |
| `PROOF_AGENT_PROVIDER_TYPE` | Provider type: `openai`, `anthropic`, `azure`, `foundry` | `openai` |
| `PROOF_AGENT_PROVIDER_API_KEY` | API key for authentication | *(none)* |
| `PROOF_AGENT_MODEL` | Model name for verification | *(required for BYOK)* |
| `PROOF_AGENT_VERIFIER_MODEL` | Different model for verifier (optional) | *(same as model)* |

### Advanced Options
| Variable | Description | Default |
|----------|-------------|---------|
| `PROOF_AGENT_PROVIDER_BEARER_TOKEN` | Bearer token (takes precedence over API key) | *(none)* |
| `PROOF_AGENT_PROVIDER_AZURE_API_VERSION` | Azure API version | `2024-02-15-preview` |

## Supported Providers

### ✅ OpenAI Compatible
- **OpenAI** — `https://api.openai.com/v1`
- **Ollama** — `http://localhost:11434/v1`
- **vLLM** — `http://your-vllm-server/v1`
- **Any OpenAI-compatible API**

### ✅ Anthropic
- **Direct API** — `https://api.anthropic.com`
- **Claude models**: `claude-sonnet-4-20250514`, `claude-haiku-4-20250514`, etc.

### ✅ Azure OpenAI
- **Enterprise endpoints** — `https://yourresource.openai.azure.com`
- **Deployment names** supported via model configuration
- **API versions** auto-handled

### ✅ IBM Foundry  
- **Watsonx models** — `https://us-south.ml.cloud.ibm.com/ml/v1`
- **Llama, Mistral, CodeLlama** models supported

## Cost Optimization

### Tiered Verification Strategy
```bash
# Use cheap models for initial screening
export PROOF_AGENT_MODEL="claude-haiku-4-20250514"      # $0.25/1M tokens

# Use expensive models only for critical PRs  
export PROOF_AGENT_VERIFIER_MODEL="claude-opus-4.6"    # $15/1M tokens (when needed)
```

### Provider Comparison
| Provider | Speed | Cost | Use Case |
|----------|-------|------|----------|
| **GitHub Models** | Fast | Free* | Default, good for most cases |
| **Claude Haiku** | Fastest | Lowest | Bulk verification, cost-sensitive |
| **Claude Sonnet** | Medium | Medium | Balanced performance/cost |
| **GPT-4 Turbo** | Fast | Medium | Enterprise with Azure credits |
| **Local Ollama** | Variable | Free | Privacy-sensitive, offline |

*Subject to GitHub Copilot quotas

## Migration Guide

### From v1.x to v2.0

**✅ No breaking changes** — existing workflows continue to work unchanged.

**✅ Optional adoption** — Add BYOK when you need it:

1. **Keep current setup** (GitHub Models)
2. **Test with your provider** in a dev branch  
3. **Switch production** when ready

### Adding BYOK to Existing Workflows

```yaml
# Before (v1.x - still works)
- uses: AndreaGriffiths11/proof-agent@v1.0
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}

# After (v2.0 - add BYOK)  
- uses: AndreaGriffiths11/proof-agent@v2.0
  env:
    PROOF_AGENT_PROVIDER_BASE_URL: https://api.anthropic.com
    PROOF_AGENT_PROVIDER_TYPE: anthropic
    PROOF_AGENT_PROVIDER_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    PROOF_AGENT_MODEL: claude-sonnet-4-20250514
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Benefits

### 🏢 **Enterprise**
- **Compliance**: Keep data within your infrastructure
- **Cost control**: Use your existing AI budgets and quotas  
- **Governance**: Standardize on approved models only
- **Performance**: Fine-tuned models optimized for your codebase

### 👩‍💻 **Individual Developers**  
- **Cost savings**: Use your own API credits vs quotas
- **Model choice**: Pick the best model for your needs
- **Experimentation**: Test cutting-edge models easily

### 🔒 **Privacy & Security**
- **Local inference**: Use Ollama for sensitive codebases
- **Data residency**: Azure regions for regulatory compliance  
- **Air-gapped**: Self-hosted models for maximum security

## Local Development

```bash
# Clone and install  
git clone https://github.com/AndreaGriffiths11/proof-agent.git
cd proof-agent
pip install -e .

# Test BYOK locally
export PROOF_AGENT_PROVIDER_BASE_URL=http://localhost:11434/v1
export PROOF_AGENT_MODEL=deepseek-coder-v2:16b

# Generate and test verification
./scripts/verify.sh | proof-agent-verify-byok
```

## Troubleshooting

### Common Issues

**❌ "BYOK verification failed"**
- Check `PROOF_AGENT_PROVIDER_BASE_URL` is set and reachable  
- Verify `PROOF_AGENT_MODEL` matches provider's available models
- Check API key permissions and quotas

**❌ "No verification prompt provided"**  
- Ensure `verification_prompt.txt` exists
- Check file permissions in GitHub Actions environment

**❌ Azure deployment not found**
- Use deployment name as `PROOF_AGENT_MODEL` 
- Verify Azure API version compatibility

### Debug Mode

```yaml
- name: Debug Proof Agent
  uses: AndreaGriffiths11/proof-agent@v2.0
  env:
    PROOF_AGENT_PROVIDER_BASE_URL: ${{ secrets.DEBUG_ENDPOINT }}
    PROOF_AGENT_MODEL: debug-model
    ACTIONS_RUNNER_DEBUG: true  # Enable verbose logging
```

---

## About

**Proof Agent** ensures AI-generated code is verified by an independent AI agent before merging. The worker writes code, the verifier finds problems.

**Key principle**: *Self-verification isn't verification.*

Created by [Andrea Griffiths](https://github.com/AndreaGriffiths11) • [Report Issues](https://github.com/AndreaGriffiths11/proof-agent/issues) • [Marketplace](https://github.com/marketplace/actions/proof-agent-verify)