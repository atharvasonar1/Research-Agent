"""Bounded batch verification for the label-free support development set."""

import json
from pathlib import Path
from random import uniform
from time import monotonic, sleep
from uuid import uuid4

from .model import ModelError, RetryableModelError
from .support import (
    VERIFIER_VERSION,
    development_predictions,
    development_verifier_payload,
)


def run_development_verifier(verifier, data, output_dir, timeout=30, sleep_fn=sleep,
                             jitter_fn=uniform):
    """Run one verifier request, allowing only one retry for Gemini HTTP 503."""
    payload, mapping, input_hash = development_verifier_payload(data)
    destination = Path(output_dir) / uuid4().hex
    destination.mkdir(parents=True, exist_ok=False)
    attempts = []
    predictions = []
    started_operation = monotonic()
    status = "failed"
    reason = "verification_failed"

    for attempt_number in (1, 2):
        started = monotonic()
        base = {
            "attempt": attempt_number,
            "provider": getattr(verifier, "provider", None),
            "model": getattr(verifier, "model", None),
            "prompt_version": VERIFIER_VERSION,
            "input_hash": input_hash,
        }
        try:
            raw = verifier.verify(payload, timeout)
            latency = round(monotonic() - started, 4)
            usage = raw.pop("usage", {}) if isinstance(raw, dict) else {}
            mapped, errors = development_predictions(raw, mapping)
            attempt = {
                **base, "latency_seconds": latency,
                **{key: value for key, value in usage.items()
                   if isinstance(value, (int, float))},
                "provider_failure": False,
                "incomplete_response": bool(errors),
                "status": "completed" if not errors else "invalid_verdict",
                "verdict": raw,
            }
            if errors:
                attempt["errors"] = errors
                reason = "invalid_or_incomplete_verdict"
            else:
                predictions = mapped
                status = "completed"
                reason = "complete_unique_verdicts"
            attempts.append(attempt)
            break
        except RetryableModelError:
            attempt = {
                **base, "status": "provider_failure", "error": "gemini_http_503",
                "http_status": 503, "latency_seconds": round(monotonic() - started, 4),
                "provider_failure": True, "incomplete_response": False,
            }
            attempts.append(attempt)
            if attempt_number == 1:
                delay = jitter_fn(0.5, 1.0)
                attempt["retry"] = {"scheduled": True, "delay_seconds": round(delay, 6)}
                sleep_fn(delay)
                continue
            reason = "verification_provider_unavailable"
            break
        except ModelError as exc:
            error = str(exc)
            incomplete = error in {"verifier_incomplete_response", "verifier_invalid_response"}
            attempts.append({
                **base,
                "status": "incomplete_response" if incomplete else "provider_failure",
                "error": error,
                "latency_seconds": round(monotonic() - started, 4),
                "provider_failure": not incomplete,
                "incomplete_response": incomplete,
            })
            reason = error
            break
        except Exception:
            attempts.append({
                **base, "status": "provider_failure", "error": "verifier_error",
                "latency_seconds": round(monotonic() - started, 4),
                "provider_failure": True, "incomplete_response": False,
            })
            reason = "verifier_error"
            break

    manifest = {
        "status": status,
        "reason": reason,
        "provider": getattr(verifier, "provider", None),
        "model": getattr(verifier, "model", None),
        "prompt_version": VERIFIER_VERSION,
        "input_hash": input_hash,
        "case_count": len(data["cases"]),
        "fact_count": len(mapping["facts"]),
        "question_count": len(mapping["questions"]),
        "case_id_mapping": mapping,
        "request_limit": 2,
        "retry_policy": "one retry only after HTTP 503",
        "duration_seconds": round(monotonic() - started_operation, 4),
        "attempts": attempts,
    }
    (destination / "verifier-input.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (destination / "verifier-predictions.json").write_text(
        json.dumps(predictions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (destination / "verifier-runs.json").write_text(
        json.dumps(attempts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (destination / "verification.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"status": status, "reason": reason, "output_dir": str(destination)}
