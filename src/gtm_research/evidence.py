"""Run-local source identities and exact, selectable evidence spans."""
from bisect import bisect_right
from copy import deepcopy
import re

from .schema import (
    MAX_COMBINED_EVIDENCE_CHARS,
    MAX_EVIDENCE_SPAN_CHARS,
    SUBMISSION_SCHEMA,
    normalize_text,
    schema_errors,
    validate_brief,
)


_CLOSERS = '\"\'”’)]}'
_ABBREVIATIONS = {
    "co", "corp", "dr", "e.g", "etc", "fig", "i.e", "inc", "jr", "ltd",
    "mr", "mrs", "ms", "no", "prof", "sr", "st", "vs",
}


def _abbreviation_at(text, period):
    if period and period + 1 < len(text) and text[period - 1].isdigit() and text[period + 1].isdigit():
        return True
    match = re.search(r"([A-Za-z][A-Za-z.]*)$", text[:period])
    if not match:
        return False
    token = match.group(1)
    lowered = token.lower()
    return lowered in _ABBREVIATIONS or len(token) == 1 or token.count(".") >= 1


def _sentence_ends(text):
    ends = []
    for index, character in enumerate(text):
        if character not in ".?!":
            continue
        if character == "." and _abbreviation_at(text, index):
            continue
        end = index + 1
        while end < len(text) and text[end] in _CLOSERS:
            end += 1
        if end == len(text) or text[end] == " ":
            ends.append(end)
    return ends


def excerpts(text, limit=MAX_EVIDENCE_SPAN_CHARS):
    """Partition normalized text into exact sentence-oriented spans with offsets."""
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("limit must be a positive integer")
    text = normalize_text(text)
    spans = {}
    sentence_ends = _sentence_ends(text)
    start = 0
    while start < len(text):
        hard_end = min(start + limit, len(text))
        boundary_index = bisect_right(sentence_ends, hard_end) - 1
        boundary = sentence_ends[boundary_index] if boundary_index >= 0 else None
        if boundary is not None and boundary > start:
            end = boundary
        elif hard_end == len(text):
            end = hard_end
        else:
            space = text.rfind(" ", start + 1, hard_end + 1)
            end = space if space > start else hard_end
        spans[f'E{len(spans) + 1}'] = {
            "text": text[start:end], "start": start, "end": end,
        }
        start = end
        if start < len(text) and text[start] == ' ':
            start += 1
    return spans


class Sources:
    """IDs are stable within a run; aliases/cache hits share the final URL's ID."""
    def __init__(self):
        self.items = {}
        self.by_url = {}

    def add(self, page):
        if page['url'] not in self.by_url:
            source_id = f'S{len(self.items) + 1}'
            self.by_url[page['url']] = source_id
            normalized = normalize_text(page['text'])
            self.items[source_id] = {
                'url': page['url'], 'fetched_at': page['fetched_at'],
                'normalized_text': normalized, 'evidence': excerpts(normalized),
            }
        return self.by_url[page['url']]

    def resolve(self, submission, pages):
        errors = schema_errors(submission, SUBMISSION_SCHEMA)
        if errors:
            return None, errors
        resolved = deepcopy(submission)
        source_orders = {source_id: order for order, source_id in enumerate(self.items, 1)}
        for index, claim in enumerate(submission['claims']):
            canonical = []
            seen = set()
            previous = None
            combined_chars = 0
            for ref_index, selected in enumerate(claim['evidence_refs']):
                label = f'claim:{index}:evidence_ref:{ref_index}'
                pair = (selected['source_id'], selected['evidence_id'])
                if pair in seen:
                    errors.append(f'{label}:duplicate')
                    continue
                seen.add(pair)
                source = self.items.get(selected['source_id'])
                if source is None:
                    errors.append(f'{label}:source_not_fetched')
                    continue
                span = source['evidence'].get(selected['evidence_id'])
                if span is None:
                    errors.append(f'{label}:evidence_not_found')
                    continue
                source_order = source_orders[selected['source_id']]
                order = (source_order, span['start'], span['end'])
                if previous is not None and order <= previous:
                    errors.append(f'{label}:not_in_canonical_order')
                    continue
                previous = order
                combined_chars += len(span['text'])
                canonical.append({
                    'source_id': selected['source_id'],
                    'evidence_id': selected['evidence_id'],
                    'url': source['url'],
                    'fetched_at': source['fetched_at'],
                    'start': span['start'], 'end': span['end'], 'text': span['text'],
                })
            if combined_chars > MAX_COMBINED_EVIDENCE_CHARS:
                errors.append(f'claim:{index}:combined_evidence_too_large')
            resolved['claims'][index] = {'claim': claim['claim'], 'evidence_refs': canonical}
        if errors:
            return None, errors
        # Keep fetched-page, exact-offset, and claim-reference checks together.
        errors = validate_brief(resolved, pages)
        if errors:
            return None, errors
        return resolved, []


def model_state(reader, sources, events, remaining_steps, guide_version):
    """Send each source once and only the latest draft; retain full local trace."""
    compact = deepcopy(events)
    submissions = [i for i, event in enumerate(compact)
                   if event.get('action', {}).get('name') == 'submit_brief']
    latest = submissions[-1] if submissions else None
    for i, event in enumerate(compact):
        event.pop('usage', None)
        event.pop('context', None)
        result = event.get('result', {})
        if 'page' in result:
            page = result.pop('page')
            result['source_id'] = sources.by_url[page['url']]
        if i in submissions and i != latest:
            event['action'].pop('arguments', None)
    state_sources = deepcopy(sources.items)
    for source in state_sources.values():
        source.pop('normalized_text', None)
    return {'start_url': reader.root, 'guide_version': guide_version,
            'allowed_urls': sorted(reader.allowed), 'sources': state_sources,
            'events': compact, 'remaining_steps_including_this': remaining_steps}
