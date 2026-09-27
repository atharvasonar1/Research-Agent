"""Minimal command-line entry point; research is planned for Phase 1."""

import argparse
from importlib.metadata import version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="GTM account research: repository foundation only; research is not implemented."
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {version('gtm-account-research')}"
    )
    parser.parse_args(argv)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
