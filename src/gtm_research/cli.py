"""Command-line interface for a single-domain research run."""

import argparse
from importlib.metadata import version
import json
import math


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def positive_float(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be finite and positive")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evidence-backed, bounded one-domain account research.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {version('gtm-account-research')}")
    subparsers = parser.add_subparsers(dest="command")
    research = subparsers.add_parser("research", help="Research one public team website")
    research.add_argument("domain", help="Domain or starting HTTP(S) URL; exact host only")
    research.add_argument("--provider", choices=("openai", "gemini"), help="Model provider (default: RESEARCH_PROVIDER or openai)")
    research.add_argument("--env-file", help="Explicit local configuration file; never executed as shell code")
    research.add_argument("--model", help="Model ID (or provider-specific OPENAI_MODEL/GEMINI_MODEL)")
    research.add_argument("--output-dir", default="runs")
    research.add_argument("--max-steps", type=positive_int, default=8)
    research.add_argument("--max-seconds", type=positive_float, default=120)
    research.add_argument("--model-timeout", type=positive_float, default=30)
    research.add_argument("--page-timeout", type=positive_float, default=10)
    research.add_argument("--max-page-bytes", type=positive_int, default=250_000)
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    from .config import load_config
    try:
        config = load_config(args.env_file)
    except (OSError, UnicodeError):
        parser.error("could not read env file")
    except ValueError as exc:
        parser.error(str(exc))
    provider = args.provider or config.get("RESEARCH_PROVIDER", "openai")
    if provider not in ("openai", "gemini"):
        parser.error("RESEARCH_PROVIDER must be openai or gemini")
    prefix = "GEMINI" if provider == "gemini" else "OPENAI"
    args.model = args.model or config.get(f"{prefix}_MODEL")
    if not args.model:
        parser.error(f"provide --model or {prefix}_MODEL")
    api_key = config.get(f"{prefix}_API_KEY", "")
    if not api_key.strip():
        parser.error(f"set {prefix}_API_KEY; credentials are never accepted as CLI arguments")
    from .agent import run_research
    from .model import OpenAIModel
    from .reader import ToolError, WebsiteReader
    try:
        reader = WebsiteReader(args.domain, timeout=args.page_timeout, max_bytes=args.max_page_bytes)
    except (ToolError, ValueError) as exc:
        parser.error(str(exc))
    from .gemini import GeminiModel
    try:
        model = GeminiModel(args.model, api_key) if provider == "gemini" else OpenAIModel(args.model, api_key)
    except ValueError:
        parser.error("invalid provider model configuration")
    try:
        result = run_research(
            model, reader, args.output_dir, args.max_steps, args.max_seconds,
            args.model_timeout, secrets=tuple(config.get(key, "") for key in ("OPENAI_API_KEY", "GEMINI_API_KEY")),
        )
    except OSError:
        print("Could not write local run artifacts; check the output directory.")
        return 1
    finally:
        model.close()
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
