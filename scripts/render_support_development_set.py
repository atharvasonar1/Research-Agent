"""Validate and render the issue #10 development set without model/network calls."""

import argparse
from collections import Counter
import json
from pathlib import Path


FACT_GRADES = {"supported", "partial", "unsupported"}
QUESTION_GRADES = {"neutral", "premise_supported", "partial", "unsupported"}
ORIGINS = {"observed_agent_failure", "supported_control", "deliberately_constructed_challenge"}


def validate_dataset(data):
    errors = []
    if data.get("schema_version") != "support-development-set-v1":
        errors.append("schema_version")
    snapshots = {item.get("snapshot_id"): item for item in data.get("snapshots", [])}
    if None in snapshots or len(snapshots) != len(data.get("snapshots", [])):
        errors.append("snapshot_ids")
    seen = set()
    for index, case in enumerate(data.get("cases", [])):
        label = f"case:{index}"
        case_id = case.get("case_id")
        if not case_id or case_id in seen:
            errors.append(f"{label}:case_id")
        seen.add(case_id)
        kind = case.get("kind")
        allowed = FACT_GRADES if kind == "fact" else QUESTION_GRADES if kind == "question" else set()
        if case.get("proposed_grade") not in allowed:
            errors.append(f"{label}:grade")
        if case.get("label_status") not in {"proposed_unreviewed", "human_approved"}:
            errors.append(f"{label}:label_status")
        if case.get("case_origin") not in ORIGINS:
            errors.append(f"{label}:origin")
        if kind == "fact":
            if not case.get("counts_toward_fact_requirement") or not isinstance(case.get("candidate_claim"), dict):
                errors.append(f"{label}:fact_shape")
            if "candidate_question" in case:
                errors.append(f"{label}:mixed_kind")
        elif kind == "question":
            if case.get("counts_toward_fact_requirement") or not case.get("candidate_question"):
                errors.append(f"{label}:question_shape")
            if "candidate_claim" in case:
                errors.append(f"{label}:mixed_kind")
        for field in ("company", "domain", "explanation", "reviewer_provenance", "origin_reference"):
            if field not in case:
                errors.append(f"{label}:missing:{field}")
        if case.get("proposed_grade") in {"partial", "unsupported"} and not case.get("unsupported_clause", "").strip():
            errors.append(f"{label}:unsupported_clause")
        for ref_index, ref in enumerate(case.get("evidence_refs", [])):
            ref_label = f"{label}:evidence:{ref_index}"
            snapshot = snapshots.get(ref.get("snapshot_id"))
            if snapshot is None:
                errors.append(f"{ref_label}:snapshot")
                continue
            if ref.get("url") != snapshot.get("url") or ref.get("fetched_at") != snapshot.get("fetched_at"):
                errors.append(f"{ref_label}:provenance")
            text = ref.get("text")
            if not isinstance(text, str) or not text:
                errors.append(f"{ref_label}:text")
            elif ref.get("end") - ref.get("start") != len(text):
                errors.append(f"{ref_label}:offset_length")
    return errors


def summary(data):
    facts = [item for item in data["cases"] if item["kind"] == "fact"]
    questions = [item for item in data["cases"] if item["kind"] == "question"]
    grades = Counter(item["proposed_grade"] for item in facts)
    companies = {item["domain"] for item in facts}
    approved = [item for item in facts if item["label_status"] == "human_approved"]
    target = data["target"]
    return {
        "fact_cases": len(facts), "question_cases": len(questions),
        "real_companies": len(companies), "supported": grades["supported"],
        "partial": grades["partial"], "unsupported": grades["unsupported"],
        "partial_or_unsupported": grades["partial"] + grades["unsupported"],
        "human_approved_fact_labels": len(approved),
        "proposed_shape_gate_met": (len(facts) >= target["fact_cases"]
                                    and len(companies) >= target["real_companies"]
                                    and grades["supported"] >= target["supported_minimum"]
                                    and grades["partial"] + grades["unsupported"] >= target["partial_or_unsupported_minimum"]),
        "ready_for_reference_evaluation": (len(approved) >= target["fact_cases"]
                                           and len({item["domain"] for item in approved}) >= target["real_companies"]),
    }


def verifier_cases(data):
    """Strip all proposed/reference labels and review notes before model use."""
    result = []
    for case in data["cases"]:
        item = {
            "case_id": case["case_id"], "kind": case["kind"],
            "evidence_refs": case["evidence_refs"],
        }
        item["candidate_claim" if case["kind"] == "fact" else "candidate_question"] = (
            case["candidate_claim"] if case["kind"] == "fact" else case["candidate_question"]
        )
        result.append(item)
    return {"schema_version": "support-verifier-development-input-v1", "cases": result}


def claim_text(case):
    if case["kind"] == "question":
        return case["candidate_question"]
    claim = case["candidate_claim"]
    return f"{claim['subject']} — {claim['relation']}: {claim['value']}"


def render(data):
    stats = summary(data)
    lines = [
        "# Factual-support checker development set", "",
        "> Development data only. This is not a holdout or a general accuracy benchmark. All current grades are proposals until a human reviewer approves them.", "",
        "## Readiness", "",
        f"- Fact cases: {stats['fact_cases']} across {stats['real_companies']} real companies.",
        f"- Proposed grades: {stats['supported']} supported, {stats['partial']} partial, {stats['unsupported']} unsupported.",
        f"- Discovery-question cases: {stats['question_cases']} (excluded from the fact-case count).",
        f"- Human-approved fact labels: {stats['human_approved_fact_labels']}.",
        f"- Ready for reference evaluation: **{'yes' if stats['ready_for_reference_evaluation'] else 'no'}**.",
        "- Exact gap: the proposed case-count/class-balance targets are met, but only two real companies are represented and no taxonomy labels have human approval.", "",
        "## Evidence inventory", "",
    ]
    for item in data["snapshots"]:
        lines.append(f"- `{item['snapshot_id']}` — {item['company']}, {item['url']}, fetched {item['fetched_at']}; {item['observed_bytes']:,} bytes; complete reader snapshot: {str(item['complete_reader_snapshot']).lower()}.")
    lines.extend(["", "### Excluded evidence", ""])
    for item in data["excluded_snapshot_inventory"]:
        lines.append(f"- {item['company']} ({item['domain']}): {item['reason']}")
    lines.extend(["", "## Review history", ""])
    for item in data["review_history"]:
        lines.append(f"- **{item['company']}:** {item['history']}")
    lines.extend(["", "## Bounded third-company capture plan", ""])
    lines.extend(f"{i}. {item}" for i, item in enumerate(data["bounded_third_company_capture_plan"], 1))
    for kind, heading in (("fact", "Fact cases"), ("question", "Discovery-question cases")):
        lines.extend(["", f"## {heading}", ""])
        for case in (item for item in data["cases"] if item["kind"] == kind):
            lines.extend([
                f"### {case['case_id']} — {case['company']}", "",
                f"- Candidate: {claim_text(case)}",
                f"- Proposed grade: **{case['proposed_grade']}**",
                f"- Unsupported clause: {case['unsupported_clause'] or 'None proposed'}",
                f"- Explanation: {case['explanation']}",
                f"- Status: `{case['label_status']}`; authority: `{case['reviewer_provenance']['label_authority']}`.",
                f"- Origin: `{case['case_origin']}` — {case['origin_reference'] or 'new control derived from saved evidence'}",
            ])
            for ref in case["evidence_refs"]:
                lines.extend([
                    f"- Evidence `{ref['snapshot_id']}/{ref['source_id']}/{ref['evidence_id']}` — {ref['url']} — fetched {ref['fetched_at']} — offsets [{ref['start']}, {ref['end']}):",
                    "", f"  > {ref['text']}", "",
                ])
    return "\n".join(lines).rstrip() + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset")
    parser.add_argument("--output", required=True)
    parser.add_argument("--verifier-input", help="Optional label-free JSON export; no model call is made")
    args = parser.parse_args(argv)
    data = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    errors = validate_dataset(data)
    if errors:
        raise SystemExit("Invalid development set: " + ", ".join(errors[:20]))
    Path(args.output).write_text(render(data), encoding="utf-8")
    if args.verifier_input:
        Path(args.verifier_input).write_text(json.dumps(verifier_cases(data), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary(data), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
