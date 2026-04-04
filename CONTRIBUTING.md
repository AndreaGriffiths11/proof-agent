# Contributing to Proof Agent

Thank you for your interest in contributing! This document explains how to set up your development environment, run tests, and submit changes.

---

## Code of Conduct

Be respectful, collaborative, and constructive. We're here to build better tools for AI safety and verification.

---

## Development Setup

### 1. Fork and clone

```bash
git clone https://github.com/YOUR_USERNAME/proof-agent.git
cd proof-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install in editable mode

```bash
pip install -e .
pip install -r requirements-dev.txt  # (coming soon: includes pytest, ruff, mypy)
```

---

## Project Structure

```
proof-agent/
├── proof_agent/          # Python package
│   ├── __init__.py       # Package exports
│   ├── config.py         # Configuration loading
│   └── verifier.py       # Core verification logic
├── scripts/              # Shell scripts
│   ├── verify.sh         # Git-based verification
│   └── fact-check.sh     # URL/package validation
├── tests/                # Unit tests (to be added)
├── examples/             # Example workflows (to be added)
├── LICENSE               # MIT License
├── README.md             # Main documentation
├── SKILL.md              # AgentSkill specification
└── pyproject.toml        # Package metadata
```

---

## Running Tests

(Coming soon — test suite in progress)

```bash
pytest tests/
```

---

## Code Style

We use:
- **Ruff** for linting and formatting
- **mypy** for type checking

Before committing:

```bash
ruff check .
ruff format .
mypy proof_agent/
```

---

## Submitting Changes

### 1. Create a branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make your changes

- Write clear, focused commits
- Add tests for new features
- Update documentation (README.md, docstrings)

### 3. Test your changes

```bash
pytest tests/
ruff check .
mypy proof_agent/
```

### 4. Push and create a PR

```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub with:
- **Description:** What does this change do?
- **Motivation:** Why is it needed?
- **Testing:** How did you verify it works?

---

## Contribution Ideas

### High Priority

- [ ] Add unit tests (pytest suite)
- [ ] Add type hints (full mypy coverage)
- [ ] Add example workflows (LangChain, LangGraph, OpenClaw)
- [ ] Add CI/CD (GitHub Actions for tests + linting)

### Medium Priority

- [ ] Add more fact-checking rules (Docker image tags, PyPI versions)
- [ ] Add support for custom verifier prompts (templates)
- [ ] Add metrics/logging (verification success rate, false positives)

### Low Priority

- [ ] Add web dashboard (view verification history)
- [ ] Add integration with LangSmith/LangFuse (observability)
- [ ] Add support for other version control systems (Mercurial, SVN)

---

## Questions?

- Open a [GitHub Discussion](https://github.com/AndreaGriffiths11/proof-agent/discussions)
- Ping [@acolombiadev](https://x.com/acolombiadev) on X/Twitter

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
