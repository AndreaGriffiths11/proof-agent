# GitHub Models Access Setup

Proof Agent requires GitHub Models API access to run adversarial verification. Due to permission restrictions, you need to create a Personal Access Token (PAT) with `models:read` scope.

## Step 1: Create Personal Access Token

1. Go to **GitHub Settings > Personal Access Tokens > Fine-grained tokens**
2. Click **Generate new token**
3. Configure the token:
   - **Repository access**: Select specific repository (e.g., `your-org/your-repo`)
   - **Permissions**:
     - `Contents`: Read
     - `Pull requests`: Write  
     - `Models`: Read — **This is critical for GitHub Models API**
4. **Generate token** and copy it

## Step 2: Add Token as Repository Secret

1. Go to your repository **Settings > Secrets and variables > Actions**
2. Click **New repository secret**
3. Name: `GH_MODELS_TOKEN`
4. Value: Paste your PAT from Step 1
5. Click **Add secret**

## Step 3: Update Workflow

```yaml
name: Proof Agent Verification

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
      
      - name: Verify PR with Proof Agent
        uses: AndreaGriffiths11/proof-agent@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          models-token: ${{ secrets.GH_MODELS_TOKEN }}  # ← Add this line
```

## Why This Is Needed

The default `secrets.GITHUB_TOKEN` doesn't include `models:read` scope, even when declared in workflow permissions. GitHub Models requires explicit `models:read` permission via a dedicated PAT.

## Troubleshooting

If you get 403 Forbidden errors:
1. Verify your PAT has `models:read` permission
2. Check that the PAT has access to your specific repository
3. Ensure the secret is named correctly in your workflow
