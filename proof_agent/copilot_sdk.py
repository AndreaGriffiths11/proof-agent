"""GitHub Copilot SDK verifier for Proof Agent."""

import asyncio
import os
import sys


SYSTEM_PROMPT = """You are an independent code verifier.

Analyze the provided code changes and give a detailed security and correctness
assessment. Static review only: do not execute commands, read extra files, edit
files, or call tools. Cite specific files, line numbers, and snippets when
assigning a verdict.

End with exactly one structured verdict heading: ### PASS, ### FAIL, or
### PARTIAL.
"""


def _model() -> str:
    """Return the Copilot SDK model to use for verification."""
    return os.getenv("PROOF_AGENT_COPILOT_MODEL") or os.getenv("PROOF_AGENT_MODEL") or "auto"


def _deny_tool_use(_request, _invocation):
    """Keep Proof Agent verification static by denying all tool requests."""
    from copilot.session import PermissionDecisionReject

    return PermissionDecisionReject(
        "Proof Agent verification is static review only; tool use is disabled."
    )


def _github_token(env: dict[str, str] | None = None) -> str | None:
    """Return the token used for Copilot SDK verification, if configured."""
    env = dict(os.environ) if env is None else env
    return (
        env.get("COPILOT_GITHUB_TOKEN")
        or env.get("GITHUB_TOKEN")
        or env.get("GH_TOKEN")
    ) or None


def _use_logged_in_user(env: dict[str, str]) -> bool:
    """Select explicit token auth or an interactive Copilot CLI login."""
    if _github_token(env):
        return False
    if (
        env.get("PROOF_AGENT_USE_CLI_LOGIN") == "1"
        or env.get("CI", "").lower() != "true"
    ):
        return True
    raise RuntimeError(
        "Copilot SDK verification requires COPILOT_GITHUB_TOKEN, GITHUB_TOKEN, "
        "or GH_TOKEN in CI. To explicitly use a Copilot CLI login, set "
        "PROOF_AGENT_USE_CLI_LOGIN=1."
    )


def _runtime_env() -> dict[str, str]:
    """Build the environment passed to the Copilot SDK runtime."""
    env = dict(os.environ)
    for name in ("COPILOT_GITHUB_TOKEN", "GITHUB_TOKEN", "GH_TOKEN"):
        if not env.get(name):
            env.pop(name, None)
    token = _github_token(env)
    if token:
        env["COPILOT_GITHUB_TOKEN"] = token
    # Intentional discarded return: this raises for tokenless CI without opt-in.
    _use_logged_in_user(env)
    return env


async def verify(prompt: str) -> str:
    """Send a verification prompt through the GitHub Copilot SDK."""
    from copilot import CopilotClient, RuntimeConnection

    env = _runtime_env()
    token = _github_token(env)
    client = CopilotClient(
        connection=RuntimeConnection.for_stdio(),
        env=env,
        use_logged_in_user=token is None,
    )
    await client.start()
    try:
        session_options = {
            "on_permission_request": _deny_tool_use,
            "model": _model(),
        }
        if token:
            session_options["github_token"] = token
        session = await client.create_session(**session_options)
        try:
            response = await session.send_and_wait(f"{SYSTEM_PROMPT}\n\n{prompt}")
            content = getattr(getattr(response, "data", None), "content", None)
            if not content:
                raise RuntimeError("Copilot SDK returned no verification content")
            return content
        finally:
            await session.disconnect()
    finally:
        await client.stop()


def main():
    """CLI entry point for Copilot SDK verification."""
    prompt = sys.stdin.read().strip()
    if not prompt:
        print("### PARTIAL\nNo verification prompt provided", file=sys.stderr)
        sys.exit(1)
    if prompt.startswith("SKIP:"):
        print(prompt)
        return

    try:
        print(asyncio.run(verify(prompt)))
    except Exception as e:
        print(f"### PARTIAL\nCopilot SDK verification error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
