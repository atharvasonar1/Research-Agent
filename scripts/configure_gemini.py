"""Run interactively: save a Gemini key without echoing it or using shell history."""

from getpass import getpass
import os
from pathlib import Path
import sys
import tempfile


def main():
    if not sys.stdin.isatty():
        raise SystemExit("Run this script directly in your local terminal; interactive input is required.")
    destination = Path(__file__).resolve().parents[1] / ".env.local"
    if destination.is_symlink():
        raise SystemExit("Refusing to replace a symlink at .env.local.")
    # Read before prompting so filesystem errors cannot include the supplied key.
    existing = destination.read_text(encoding="utf-8") if destination.exists() else ""
    key = getpass("Gemini API key (hidden): ").strip()
    if not key or any(char.isspace() for char in key):
        raise SystemExit("Key must be nonempty and contain no whitespace.")
    replaced = {"GEMINI_API_KEY", "GEMINI_MODEL", "RESEARCH_PROVIDER"}
    lines = [line for line in existing.splitlines() if line.partition("=")[0].strip() not in replaced]
    lines.extend([f"GEMINI_API_KEY={key}", "GEMINI_MODEL=gemini-2.5-flash", "RESEARCH_PROVIDER=gemini"])
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent,
                                         prefix=".env.", delete=False) as stream:
            temp_path = Path(stream.name)
            os.fchmod(stream.fileno(), 0o600)
            stream.write("\n".join(lines) + "\n")
        os.replace(temp_path, destination)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
    print("Saved .env.local with owner-only permissions; key not displayed.")
    print("Model: gemini-2.5-flash. Documented free tier; account access/quota not yet verified.")


if __name__ == "__main__":
    main()
