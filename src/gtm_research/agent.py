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
from .schema import FETCH_SCHEMA, RESEARCH_TOPICS, schema_errors, validate_brief
from .evidence import Sources, model_state
from .support import accept_verified_candidate, candidate_for_verification


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
    lines = [f"# {brief['company_name']}", "", "## Qualification", "",
             "**Not assessed.** This research brief does not assign fit, buying intent, or sales priority.",
             "", "## Website-reported facts", "",
             "These are website statements, not independently verified facts.", ""]
    for index, claim in enumerate(brief["claims"], 1):
        fact = claim['claim']
        identity = " — Declared identity fact" if index == brief["identity_claim_ref"] else ""
        lines.extend([f"### C{index}{identity}", f"- {fact['subject']} — {fact['relation']}: {fact['value']}"])
        for ref_index, evidence in enumerate(claim['evidence_refs'], 1):
            lines.extend([
                f"  Evidence {ref_index} [{evidence['source_id']}/{evidence['evidence_id']}]: {evidence['url']}",
                f"  Fetched: {evidence['fetched_at']}",
                f"  Normalized offsets: [{evidence['start']}, {evidence['end']})",
                f"  Excerpt: {evidence['text']}",
            ])
    lines.extend(["", "## Unknowns", ""])
    lines.extend(f"- {item}" for item in brief["unknowns"])
    lines.extend(["", "## Discovery questions", ""])
    if brief["discovery_questions"]:
        for item in brief["discovery_questions"]:
            refs = ", ".join(f"[C{ref}](#c{ref})" for ref in item["premise_claim_refs"])
            lines.extend([f"- {item['question']}", f"  Premise evidence: {refs or 'No factual premise declared; review neutrality.'}"])
    else:
        lines.append("No discovery questions were generated.")
    lines.extend(["", "## Research coverage", ""])
    coverage_by_topic = {item["topic_id"]: item for item in brief["coverage"]}
    for topic_id, description in RESEARCH_TOPICS.items():
        item = coverage_by_topic[topic_id]
        lines.append(f"### {topic_id.replace('_', ' ').title()} — {item['status'].title()}")
        lines.append(f"- {item['summary']}")
        if item["fact_refs"]:
            lines.append("  Accepted facts: " + ", ".join(f"C{ref}" for ref in item["fact_refs"]))
        lines.append(f"  Trusted topic: {description}")
    lines.extend(["", "## Unresolved research topics", ""])
    unresolved = [item for item in brief["coverage"] if item["status"] == "unresolved"]
    if unresolved:
        lines.extend(f"- {item['topic_id']}: {item['summary']}" for item in unresolved)
    else:
        lines.append("No trusted topics were marked unresolved.")
    lines.extend(["", "## Relevant page candidates", ""])
    if brief["relevant_candidates"]:
        for candidate in brief["relevant_candidates"]:
            topics = ", ".join(candidate["topic_ids"])
            lines.append(
                f"- {candidate['url']} — {candidate['disposition'].title()} "
                f"({topics}): {candidate['reason']}"
            )
    else:
        lines.append("No discovered pages were declared relevant beyond the pages already assessed.")
    lines.extend(["", "## Remaining relevant candidates", ""])
    pending = [item for item in brief["relevant_candidates"] if item["disposition"] == "pending"]
    if pending:
        lines.extend(f"- {item['url']}: {item['reason']}" for item in pending)
    else:
        lines.append("No relevant candidates remain pending.")
    lines.extend([
        "", "## Stopping decision", "",
        f"- Code: {brief['stopping']['code']}",
        f"- Summary: {brief['stopping']['summary']}",
    ])
    lines.extend(["", "Evidence provenance and normalized offsets were checked; semantic support still needs human review.", ""])
    return "\n".join(lines)


def _run_candidate_research(model, reader, output_dir="runs", max_steps=6, max_seconds=120,
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
    consecutive_no_progress = 0
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
                    if exc.outcome is not None:
                        result["reader_outcome"] = exc.outcome
                except Exception:
                    result = {"ok": False, "errors": ["tool_error"]}
        elif action.name == "submit_brief":
            resolved, problems = sources.resolve(action.arguments, reader.pages, reader)
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
        if action.name == "fetch_page":
            if result.get("ok"):
                consecutive_no_progress = 0
            elif "reader_outcome" in result:
                consecutive_no_progress += 1
                if consecutive_no_progress >= 2 and not reader.untried_allowed_urls():
                    status = "failed"
                    reason = "no_research_progress" if sources.items else "no_researchable_sources"
                    result["stop_reason"] = reason
                    errors.append(reason)
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
        "reader_failures": sum(item["status"] == "failed" for item in reader.outcomes),
        "reader_cache_hits": sum(item["cached"] for item in reader.outcomes),
    }
    report = redact({"status": status, "reason": reason, "metadata": metadata}, secrets)
    discovered_urls = [{
        "url": url,
        "visited": url in reader.pages,
        "reader_errors": sorted({
            item["error"] for item in reader.outcomes
            if item["status"] == "failed"
            and url in (item.get("requested_url"), item.get("final_url"))
        }),
    } for url in sorted(reader.allowed)]
    trace_payload = {**report, "start_url": reader.root, "events": events,
                     "pages": list(pages.values()), "sources": sources.items,
                     "reader_outcomes": reader.outcomes,
                     "discovered_urls": discovered_urls}
    if brief is not None:
        trace_payload["coverage_checkpoint"] = {
            "coverage": brief["coverage"],
            "relevant_candidates": brief["relevant_candidates"],
            "stopping": brief["stopping"],
        }
    trace = redact(trace_payload, secrets)
    (run_dir / "trace.json").write_text(json.dumps(trace, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (run_dir / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if brief is not None:
        brief = redact({**brief, "metadata": metadata}, secrets)
        (run_dir / "brief.json").write_text(json.dumps(brief, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (run_dir / "brief.md").write_text(readable_brief(brief), encoding="utf-8")
    return {**report, "run_dir": str(run_dir)}


def _usage_total(events):
    totals = {}
    for event in events:
        for key, value in event.get("usage", {}).items():
            if isinstance(value, (int, float)):
                totals[key] = totals.get(key, 0) + value
    return totals


def run_research(model, reader, output_dir="runs", max_steps=8, max_seconds=120,
                 model_timeout=30, secrets=(), max_model_retries=3, verifier=None):
    """Research for at most six calls, then immediately verify within eight total."""
    if not isinstance(max_steps, int) or isinstance(max_steps, bool) or not 1 <= max_steps <= 8:
        raise ValueError("max_steps must be an integer from 1 to 8")
    research_limit = min(6, max_steps)
    result = _run_candidate_research(
        model, reader, output_dir, research_limit, max_seconds, model_timeout,
        secrets, max_model_retries,
    )
    run_dir = Path(result["run_dir"])
    trace_path = run_dir / "trace.json"
    result_path = run_dir / "result.json"
    brief_path = run_dir / "brief.json"
    markdown_path = run_dir / "brief.md"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    elapsed = result["metadata"]["duration_seconds"]
    candidate = None
    if brief_path.exists():
        candidate = json.loads(brief_path.read_text(encoding="utf-8"))
        candidate.pop("metadata", None)
        trace["candidate_brief"] = candidate
        trace["candidate_coverage_checkpoint"] = trace.pop("coverage_checkpoint", None)
        brief_path.unlink()
        markdown_path.unlink(missing_ok=True)
    if candidate is None:
        trace["verification"] = {"status": "not_started", "reason": "no_valid_candidate"}
        trace_path.write_text(json.dumps(redact(trace, secrets), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return result

    checker = verifier if verifier is not None else (model if hasattr(model, "verify") else None)
    metadata = result["metadata"]
    metadata["research_model_calls"] = metadata["model_calls"]
    metadata["research_usage"] = _usage_total(trace["events"])
    metadata["verification_calls"] = 0
    metadata["verification_usage"] = {}
    metadata["verifier_model"] = getattr(checker, "model", None) if checker else None
    metadata["verifier_provider"] = getattr(checker, "provider", None) if checker else None
    metadata["limits"].update({"max_steps": max_steps, "research_calls": research_limit,
                               "verification_attempts": 2, "total_model_calls": max_steps})
    verification = {"status": "failed", "attempts": [],
                    "input": candidate_for_verification(candidate)}
    verification_started = monotonic()
    verification_budget = max_seconds - elapsed
    final = None
    failure_reason = None
    if checker is None:
        failure_reason = "verification_not_configured"
    else:
        for attempt in (1, 2):
            if metadata["model_calls"] >= max_steps:
                failure_reason = "model_call_budget_exhausted_before_verification"
                break
            remaining = verification_budget - (monotonic() - verification_started)
            if remaining <= 0:
                failure_reason = "time_limit_before_verification"
                break
            metadata["model_calls"] += 1
            metadata["verification_calls"] += 1
            event = {"attempt": attempt}
            started = monotonic()
            try:
                raw = bounded_call(
                    lambda: checker.verify(verification["input"], min(model_timeout, remaining)),
                    min(model_timeout, remaining),
                )
                event["duration_seconds"] = round(monotonic() - started, 4)
                usage = raw.pop("usage", {}) if isinstance(raw, dict) else {}
                event["usage"] = usage
                accepted, outcome = accept_verified_candidate(candidate, raw)
                event["verdict"] = raw
                if accepted is None:
                    event["status"] = "rejected"
                    event["errors"] = outcome["errors"]
                    failure_reason = ("verification_invalid" if any(
                        item.startswith("verifier") for item in outcome["errors"]
                    ) else "semantic_rejection")
                else:
                    page_map = {page["url"]: page for page in trace["pages"]}
                    final_errors = validate_brief(accepted, page_map, reader)
                    if final_errors:
                        event["status"] = "invalid_final"
                        event["errors"] = final_errors
                        failure_reason = "verification_invalid_final"
                    else:
                        final = accepted
                        event["status"] = "accepted"
                        verification["outcome"] = outcome
                verification["attempts"].append(event)
                break
            except TimeoutError:
                event.update(status="provider_failure", error="verifier_timeout",
                             duration_seconds=round(monotonic() - started, 4))
                verification["attempts"].append(event)
                failure_reason = "verifier_timeout"
                break
            except RetryableModelError:
                event.update(status="provider_failure", error="gemini_http_503", http_status=503,
                             duration_seconds=round(monotonic() - started, 4))
                verification["attempts"].append(event)
                if attempt == 1 and metadata["model_calls"] < max_steps:
                    delay = uniform(0.5, 1.0)
                    remaining = verification_budget - (monotonic() - verification_started)
                    if delay >= remaining:
                        event["retry"] = {"scheduled": False, "stop_reason": "time_limit_before_verification_retry"}
                        failure_reason = "time_limit_before_verification_retry"
                        break
                    event["retry"] = {"scheduled": True, "delay_seconds": round(delay, 6), "next_attempt": 2}
                    before_sleep = monotonic()
                    sleep(delay)
                    event["retry"]["elapsed_sleep_seconds"] = round(monotonic() - before_sleep, 6)
                    continue
                failure_reason = "verification_provider_unavailable"
                break
            except ModelError as exc:
                event.update(status="provider_failure", error=str(exc),
                             duration_seconds=round(monotonic() - started, 4))
                verification["attempts"].append(event)
                failure_reason = str(exc)
                break
            except Exception:
                event.update(status="provider_failure", error="verifier_error",
                             duration_seconds=round(monotonic() - started, 4))
                verification["attempts"].append(event)
                failure_reason = "verifier_error"
                break

    metadata["verification_usage"] = _usage_total(verification["attempts"])
    metadata["verification_latency_seconds"] = round(sum(
        item.get("duration_seconds", 0) for item in verification["attempts"]
    ), 4)
    metadata["verification_provider_failures"] = sum(
        item.get("status") == "provider_failure" for item in verification["attempts"]
    )
    metadata["duration_seconds"] = round(elapsed + monotonic() - verification_started, 4)
    metadata["total_usage"] = {
        key: metadata["research_usage"].get(key, 0) + metadata["verification_usage"].get(key, 0)
        for key in set(metadata["research_usage"]) | set(metadata["verification_usage"])
    }
    if final is None:
        result.update(status="failed", reason=failure_reason)
        metadata["errors"].append(failure_reason)
        verification.update(status="failed", reason=failure_reason)
    else:
        result.update(status="completed", reason="verified_submission")
        verification.update(status="accepted", reason="verifier_approved_and_code_filtered")
        final = redact({**final, "metadata": metadata}, secrets)
        brief_path.write_text(json.dumps(final, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(readable_brief(final), encoding="utf-8")
        trace["coverage_checkpoint"] = {
            "coverage": final["coverage"], "relevant_candidates": final["relevant_candidates"],
            "stopping": final["stopping"],
        }
    trace.update(status=result["status"], reason=result["reason"], metadata=metadata,
                 verification=verification)
    report = redact({"status": result["status"], "reason": result["reason"],
                     "metadata": metadata}, secrets)
    trace_path.write_text(json.dumps(redact(trace, secrets), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    result_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return {**report, "run_dir": str(run_dir)}
