"""Command-line interface for proof-agent tools."""

import sys
from .verifier import parse_verdict


def parse_verdict_cli():
    """Parse verdict from stdin and output verdict type.
    
    Reads verifier response from stdin, parses it, and prints
    the verdict type (PASS, FAIL, or PARTIAL) to stdout.
    
    Usage:
        echo "$VERDICT" | proof-agent-parse-verdict
    """
    try:
        response = sys.stdin.read()
        result = parse_verdict(response)
        print(result.verdict.value.upper())
        sys.exit(0)
    except Exception as e:
        print(f"PARTIAL", file=sys.stdout)  # Safe fallback
        print(f"Error parsing verdict: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point (for future subcommands)."""
    if len(sys.argv) > 1 and sys.argv[1] == "parse-verdict":
        parse_verdict_cli()
    else:
        print("Usage: proof-agent parse-verdict", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
