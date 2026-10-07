"""Command-line interface for a single-domain research run."""

import argparse
from importlib.metadata import version
import json
import math
from pathlib import Path
from uuid import uuid4


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def model_call_limit(value):
    number = positive_int(value)
    if number > 8:
        raise argparse.ArgumentTypeError("must be at most 8")
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
    research.add_argument("--verifier-provider", choices=("openai", "gemini"), help="Verifier provider (default: VERIFIER_PROVIDER or generator provider)")
    research.add_argument("--verifier-model", help="Verifier model ID (default: VERIFIER_MODEL or generator model)")
    research.add_argument("--output-dir", default="runs")
    research.add_argument("--max-steps", type=model_call_limit, default=8)
    research.add_argument("--max-seconds", type=positive_float, default=120)
    research.add_argument("--model-timeout", type=positive_float, default=30)
    research.add_argument("--page-timeout", type=positive_float, default=10)
    research.add_argument("--max-page-bytes", type=positive_int, default=250_000)
    saved = subparsers.add_parser("verify-saved", help="Verify a saved candidate trace without fetching a website")
    saved.add_argument("trace", help="Path to a trace.json containing candidate_brief")
    saved.add_argument("--provider", choices=("openai", "gemini"), help="Verifier provider")
    saved.add_argument("--env-file", help="Explicit local configuration file")
    saved.add_argument("--model", help="Verifier model ID")
    saved.add_argument("--output-dir", default="runs/support-check")
    saved.add_argument("--timeout", type=positive_float, default=30)
    evaluate = subparsers.add_parser("evaluate-support", help="Score verifier predictions against human labels")
    evaluate.add_argument("labels", help="Human-labeled JSON array")
    evaluate.add_argument("predictions", help="Verifier prediction JSON array")
    evaluate.add_argument("--runs", help="Optional JSON array with tokens, latency_seconds, and provider_failure")
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    from .config import load_config
    try:
        config = load_config(getattr(args, "env_file", None))
    except (OSError, UnicodeError):
        parser.error("could not read env file")
    except ValueError as exc:
        parser.error(str(exc))
    if args.command == "evaluate-support":
        try:
            labels = json.loads(Path(args.labels).read_text(encoding="utf-8"))
            predictions = json.loads(Path(args.predictions).read_text(encoding="utf-8"))
            runs = json.loads(Path(args.runs).read_text(encoding="utf-8")) if args.runs else []
            if not isinstance(labels, list) or not isinstance(predictions, list) or not isinstance(runs, list):
                raise ValueError
            from .support import evaluate_human_labels
            metrics = evaluate_human_labels(labels, predictions, runs)
        except (OSError, UnicodeError, ValueError, KeyError, TypeError):
            parser.error("labels and predictions must be valid JSON arrays with the documented fields")
        print(json.dumps(metrics, indent=2))
        return 0 if metrics["provisional_gates_evaluable"] else 1

    if args.command == "verify-saved":
        provider = args.provider or config.get("VERIFIER_PROVIDER") or config.get("RESEARCH_PROVIDER", "openai")
        prefix = "GEMINI" if provider == "gemini" else "OPENAI"
        model_name = args.model or config.get("VERIFIER_MODEL") or config.get(f"{prefix}_MODEL")
        if not model_name:
            parser.error(f"provide --model, VERIFIER_MODEL, or {prefix}_MODEL")
        api_key = config.get(f"{prefix}_API_KEY", "")
        if not api_key.strip():
            parser.error(f"set {prefix}_API_KEY; credentials are never accepted as CLI arguments")
        try:
            trace = json.loads(Path(args.trace).read_text(encoding="utf-8"))
            candidate = trace["candidate_brief"]
        except (OSError, UnicodeError, ValueError, KeyError, TypeError):
            parser.error("trace must be readable JSON containing candidate_brief")
        from .gemini import GeminiSupportVerifier
        from .model import ModelError, OpenAISupportVerifier, RetryableModelError
        from .support import accept_verified_candidate, candidate_for_verification, validate_saved_candidate
        saved_errors = validate_saved_candidate(candidate, trace)
        if saved_errors:
            parser.error("saved candidate failed canonical evidence validation: " + saved_errors[0])
        verifier = (GeminiSupportVerifier(model_name, api_key) if provider == "gemini"
                    else OpenAISupportVerifier(model_name, api_key))
        attempts = []
        final = None
        try:
            for attempt in (1, 2):
                try:
                    verdict = verifier.verify(candidate_for_verification(candidate), args.timeout)
                    usage = verdict.pop("usage", {})
                    final, outcome = accept_verified_candidate(candidate, verdict)
                    attempts.append({"attempt": attempt, "status": "accepted" if final else "rejected",
                                     "usage": usage, "verdict": verdict, "outcome": outcome})
                    break
                except RetryableModelError:
                    attempts.append({"attempt": attempt, "status": "provider_failure", "error": "gemini_http_503"})
                    if attempt == 2:
                        break
                except ModelError as exc:
                    attempts.append({"attempt": attempt, "status": "provider_failure", "error": str(exc)})
                    break
        finally:
            verifier.close()
        destination = Path(args.output_dir) / uuid4().hex
        destination.mkdir(parents=True, exist_ok=False)
        (destination / "verification.json").write_text(json.dumps({"attempts": attempts}, indent=2) + "\n")
        if final:
            (destination / "verified-brief.json").write_text(json.dumps(final, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({"status": "completed" if final else "failed", "output_dir": str(destination)}, indent=2))
        return 0 if final else 1

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
    from .model import OpenAIModel, OpenAISupportVerifier
    from .reader import ToolError, WebsiteReader
    try:
        reader = WebsiteReader(args.domain, timeout=args.page_timeout, max_bytes=args.max_page_bytes)
    except (ToolError, ValueError) as exc:
        parser.error(str(exc))
    from .gemini import GeminiModel, GeminiSupportVerifier
    try:
        model = GeminiModel(args.model, api_key) if provider == "gemini" else OpenAIModel(args.model, api_key)
        verifier_provider = args.verifier_provider or config.get("VERIFIER_PROVIDER") or provider
        verifier_prefix = "GEMINI" if verifier_provider == "gemini" else "OPENAI"
        verifier_model = (args.verifier_model or config.get("VERIFIER_MODEL")
                          or (args.model if verifier_provider == provider else config.get(f"{verifier_prefix}_MODEL")))
        if not verifier_model:
            parser.error(f"provide --verifier-model, VERIFIER_MODEL, or {verifier_prefix}_MODEL")
        verifier_key = config.get(f"{verifier_prefix}_API_KEY", "")
        if not verifier_key.strip():
            parser.error(f"set {verifier_prefix}_API_KEY for the verifier")
        verifier = (GeminiSupportVerifier(verifier_model, verifier_key) if verifier_provider == "gemini"
                    else OpenAISupportVerifier(verifier_model, verifier_key))
    except ValueError:
        parser.error("invalid provider model configuration")
    try:
        result = run_research(
            model, reader, args.output_dir, args.max_steps, args.max_seconds,
            args.model_timeout, secrets=tuple(config.get(key, "") for key in ("OPENAI_API_KEY", "GEMINI_API_KEY")),
            verifier=verifier,
        )
    except OSError:
        print("Could not write local run artifacts; check the output directory.")
        return 1
    finally:
        model.close()
        verifier.close()
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
