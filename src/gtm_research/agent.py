"""Bounded model/tool loop, validation, and local run artifacts."""

from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from time import monotonic
from uuid import uuid4

from .bounds import bounded_call
from .model import GUIDE_VERSION, ModelError
from .reader import ToolError
from .schema import FETCH_SCHEMA, schema_errors, validate_brief


def redact(value, secrets):
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        return value
    if isinstance(value, list):
        return [redact(item, secrets) for item in value]
    if isinstance(value, dict):
        return {redact(key, secrets): redact(item, secrets) for key, item in value.items()}
    return value


def readable_brief(brief):
    lines = [f"# {brief['company_name']}", "", f"Research priority: {brief['fit_label']}",
             "", brief["fit_rationale"], "", "## Sourced claims", ""]
    for claim in brief["claims"]:
        lines.extend([f"- {claim['claim']}", f"  Source: {claim['url']}",
                      f"  Excerpt: {claim['excerpt']}"])
    for heading, field in (("Unknowns", "unknowns"), ("Discovery questions", "discovery_questions")):
        lines.extend(["", f"## {heading}", ""])
        lines.extend(f"- {item}" for item in brief[field])
    lines.extend(["", "Excerpt presence was checked; semantic support still needs human review.", ""])
    return "\n".join(lines)


def run_research(model, reader, output_dir="runs", max_steps=8, max_seconds=120,
                 model_timeout=30, secrets=()):
    if not isinstance(max_steps, int) or isinstance(max_steps, bool) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    if any(not math.isfinite(value) or value <= 0 for value in (max_seconds, model_timeout)):
        raise ValueError("time limits must be finite and positive")
    # Create a unique run directory before spending any model budget. Failed runs
    # cannot inherit an old successful brief from a reused directory.
    run_dir = Path(output_dir) / uuid4().hex
    run_dir.mkdir(parents=True, exist_ok=False)
    started_at = datetime.now(timezone.utc).isoformat()
    start = monotonic()
    deadline = start + max_seconds
    events = []
    errors = []
    brief = None
    status = "budget_exhausted"
    reason = "step_limit"
    model_calls = tool_calls = 0
    for step in range(1, max_steps + 1):
        remaining = deadline - monotonic()
        if remaining <= 0:
            reason = "time_limit"
            break
        state = {
            "start_url": reader.root, "guide_version": GUIDE_VERSION,
            "allowed_urls": sorted(reader.allowed), "events": deepcopy(events),
            "remaining_steps_including_this": max_steps - step + 1,
        }
        model_calls += 1
        try:
            wait = min(model_timeout, remaining)
            action = bounded_call(lambda: model.decide(state, wait), wait)
        except TimeoutError:
            if monotonic() >= deadline:
                status, reason = "budget_exhausted", "time_limit"
            else:
                status, reason = "failed", "model_timeout"
            errors.append(reason)
            events.append({"step": step, "model_error": reason})
            break
        except ModelError as exc:
            status, reason = "failed", str(exc)
            errors.append(reason)
            events.append({"step": step, "model_error": reason})
            break
        except Exception:
            status, reason = "failed", "model_error"
            errors.append(reason)
            events.append({"step": step, "model_error": reason})
            break
        event = {"step": step, "action": {"name": action.name, "arguments": action.arguments},
                 "usage": action.usage}
        if monotonic() >= deadline:
            reason = "time_limit"
            event["result"] = {"ok": False, "errors": ["time_limit"]}
            events.append(event)
            errors.append("time_limit")
            break
        tool_calls += 1
        if action.name == "fetch_page":
            problems = schema_errors(action.arguments, FETCH_SCHEMA)
            if problems:
                result = {"ok": False, "errors": problems}
            else:
                try:
                    page = reader.fetch(action.arguments["url"], timeout=deadline - monotonic())
                    result = {"ok": True, "page": page}
                except ToolError as exc:
                    result = {"ok": False, "errors": [str(exc)]}
                except Exception:
                    result = {"ok": False, "errors": ["tool_error"]}
        elif action.name == "submit_brief":
            problems = validate_brief(action.arguments, reader.pages)
            result = {"ok": not problems, "errors": problems}
            if not problems:
                brief = deepcopy(action.arguments)
                status, reason = "completed", "validated_submission"
        else:
            result = {"ok": False, "errors": ["unknown_tool"]}
        event["result"] = result
        events.append(event)
        errors.extend(result.get("errors", []))
        if brief is not None:
            break
    if brief is None and status == "budget_exhausted" and monotonic() >= deadline:
        reason = "time_limit"
    pages = {page["url"]: page for page in reader.pages.values()}
    metadata = {
        "started_at": started_at, "duration_seconds": round(monotonic() - start, 4),
        "pages": len(pages), "model_calls": model_calls, "tool_calls": tool_calls,
        "errors": errors, "guide_version": GUIDE_VERSION,
        "model": getattr(model, "model", "fake"),
        "limits": {"max_steps": max_steps, "max_seconds": max_seconds,
                   "model_timeout": model_timeout, "page_timeout": reader.timeout,
                   "max_page_bytes": reader.max_bytes, "max_redirects": reader.max_redirects},
        "cost_usd": None,
    }
    report = redact({"status": status, "reason": reason, "metadata": metadata}, secrets)
    trace = redact({**report, "start_url": reader.root, "events": events,
                    "pages": list(pages.values())}, secrets)
    (run_dir / "trace.json").write_text(json.dumps(trace, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (run_dir / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if brief is not None:
        brief = redact({**brief, "metadata": metadata}, secrets)
        (run_dir / "brief.json").write_text(json.dumps(brief, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (run_dir / "brief.md").write_text(readable_brief(brief), encoding="utf-8")
    return {**report, "run_dir": str(run_dir)}
