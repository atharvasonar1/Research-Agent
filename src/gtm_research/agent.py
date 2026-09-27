"""Bounded model/tool loop, validation, and local run artifacts."""

from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from time import monotonic, sleep
from random import uniform
from uuid import uuid4

from .bounds import bounded_call
from .model import GUIDE_VERSION, ModelError, RetryableModelError
from .reader import ToolError
from .schema import FETCH_SCHEMA, schema_errors
from .evidence import Sources, model_state


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
    lines = [f"# {brief['company_name']}", "", "## Website-reported facts", "",
             "These are website statements, not independently verified facts.", ""]
    for index, claim in enumerate(brief["claims"], 1):
        fact = claim['claim']
        lines.extend([f"### C{index}", f"- {fact['subject']} — {fact['relation']}: {fact['value']}",
                      f"  Source: {claim['url']}", f"  Excerpt: {claim['excerpt']}"])
    lines.extend(["", "## Model sales inferences — not website facts", "",
                  f"Provisional research priority (model judgment): {brief['fit_label']}", ""])
    for index, item in enumerate(brief['sales_inferences'], 1):
        refs = ", ".join(f"[C{ref}](#c{ref})" for ref in item['claim_refs'])
        lines.extend([f"### I{index} — Model inference", item['text'],
                      f"Based on: {refs}", f"Limitation / needs validation: {item['limitation']}"])
    lines.extend(["", "## Unknowns", ""])
    lines.extend(f"- {item}" for item in brief["unknowns"])
    lines.extend(["", "## Discovery questions", ""])
    for item in brief["discovery_questions"]:
        refs = ", ".join(f"[C{ref}](#c{ref})" for ref in item["premise_claim_refs"])
        lines.extend([f"- {item['question']}", f"  Premise evidence: {refs or 'No factual premise declared; review neutrality.'}"])
    lines.extend(["", "Excerpt presence was checked; semantic support still needs human review.", ""])
    return "\n".join(lines)


def run_research(model, reader, output_dir="runs", max_steps=8, max_seconds=120,
                 model_timeout=30, secrets=(), max_model_retries=3):
    if not isinstance(max_steps, int) or isinstance(max_steps, bool) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    if any(not math.isfinite(value) or value <= 0 for value in (max_seconds, model_timeout)):
        raise ValueError("time limits must be finite and positive")
    if not isinstance(max_model_retries, int) or isinstance(max_model_retries, bool) or not 0 <= max_model_retries <= 10:
        raise ValueError("max_model_retries must be an integer from 0 to 10")
    # Create a unique run directory before spending any model budget. Failed runs
    # cannot inherit an old successful brief from a reused directory.
    run_dir = Path(output_dir) / uuid4().hex
    run_dir.mkdir(parents=True, exist_ok=False)
    started_at = datetime.now(timezone.utc).isoformat()
    start = monotonic()
    deadline = start + max_seconds
    events = []
    sources = Sources()
    errors = []
    brief = None
    status = "budget_exhausted"
    reason = "step_limit"
    model_calls = tool_calls = retries_scheduled = 0
    for step in range(1, max_steps + 1):
        remaining = deadline - monotonic()
        if remaining <= 0:
            reason = "time_limit"
            break
        state = model_state(reader, sources, events, max_steps - step + 1, GUIDE_VERSION)
        context = {"state_utf8_bytes": len(json.dumps(state, ensure_ascii=False).encode("utf-8"))}
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
        except RetryableModelError:
            # Each retry occupies the next normal loop step/model-call slot.
            errors.append("gemini_http_503")
            retry = {"scheduled": False}
            event = {"step": step, "model_error": "gemini_http_503", "http_status": 503, "retry": retry}
            events.append(event)
            if step >= max_steps:
                status, reason = "budget_exhausted", "model_call_budget_exhausted_after_503"
            elif retries_scheduled >= max_model_retries:
                status, reason = "failed", "gemini_503_retry_limit"
            else:
                # Equal jitter avoids immediate bursts: [0.5, 1], [1, 2],
                # [2, 4], then capped at [4, 8] seconds for explicit larger limits.
                ceiling = min(8.0, 2.0 ** retries_scheduled)
                delay = uniform(ceiling / 2, ceiling)
                remaining = deadline - monotonic()
                if delay >= remaining:
                    status, reason = "budget_exhausted", "time_limit_before_retry"
                else:
                    retries_scheduled += 1
                    retry.update(scheduled=True, number=retries_scheduled,
                                 delay_seconds=round(delay, 6), next_step=step + 1)
                    before_sleep = monotonic()
                    sleep(delay)
                    retry["elapsed_sleep_seconds"] = round(monotonic() - before_sleep, 6)
                    if monotonic() >= deadline:
                        status, reason = "budget_exhausted", "time_limit"
                        retry["stop_reason"] = reason
                        break
                    continue
            retry["stop_reason"] = reason
            errors.append(reason)
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
                 "usage": action.usage, "context": context}
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
                    sources.add(page)
                    result = {"ok": True, "page": page}
                except ToolError as exc:
                    result = {"ok": False, "errors": [str(exc)]}
                except Exception:
                    result = {"ok": False, "errors": ["tool_error"]}
        elif action.name == "submit_brief":
            resolved, problems = sources.resolve(action.arguments, reader.pages)
            result = {"ok": not problems, "errors": problems}
            if not problems:
                brief = resolved
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
        "retries_scheduled": retries_scheduled,
        "model": getattr(model, "model", "fake"),
        "provider": getattr(model, "provider", "fake"),
        "limits": {"max_model_retries": max_model_retries, "retry_max_delay_seconds": 8, "max_steps": max_steps, "max_seconds": max_seconds,
                   "model_timeout": model_timeout, "page_timeout": reader.timeout,
                   "max_page_bytes": reader.max_bytes, "max_redirects": reader.max_redirects},
        "cost_usd": None,
    }
    report = redact({"status": status, "reason": reason, "metadata": metadata}, secrets)
    trace = redact({**report, "start_url": reader.root, "events": events,
                    "pages": list(pages.values()), "sources": sources.items}, secrets)
    (run_dir / "trace.json").write_text(json.dumps(trace, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (run_dir / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if brief is not None:
        brief = redact({**brief, "metadata": metadata}, secrets)
        (run_dir / "brief.json").write_text(json.dumps(brief, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (run_dir / "brief.md").write_text(readable_brief(brief), encoding="utf-8")
    return {**report, "run_dir": str(run_dir)}
