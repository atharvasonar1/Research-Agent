"""Run-local source identities and exact, selectable evidence spans."""
from copy import deepcopy

from .schema import SUBMISSION_SCHEMA, normalize_text, schema_errors, validate_brief


def excerpts(text, limit=600):
    """Partition normalized text without dropping content or synthesizing quotes."""
    text = normalize_text(text)
    spans = {}
    start = 0
    while start < len(text):
        end = min(start + limit, len(text))
        if end < len(text):
            sentence = text.rfind('. ', start, end)
            space = text.rfind(' ', start, end)
            if sentence >= start + limit // 2:
                end = sentence + 1
            elif space > start:
                end = space
        spans[f'E{len(spans) + 1}'] = text[start:end]
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
            self.items[source_id] = {'url': page['url'], 'fetched_at': page['fetched_at'],
                                     'excerpts': excerpts(page['text'])}
        return self.by_url[page['url']]

    def resolve(self, submission, pages):
        errors = schema_errors(submission, SUBMISSION_SCHEMA)
        if errors:
            return None, errors
        resolved = deepcopy(submission)
        for index, claim in enumerate(submission['claims']):
            source = self.items.get(claim['source_id'])
            if source is None:
                errors.append(f'claim:{index}:source_not_fetched')
            elif claim['excerpt_id'] not in source['excerpts']:
                errors.append(f'claim:{index}:excerpt_not_found')
            else:
                resolved['claims'][index] = {'claim': claim['claim'], 'url': source['url'],
                    'excerpt': source['excerpts'][claim['excerpt_id']]}
        if errors:
            return None, errors
        # Keep the existing fetched-page/excerpt and claim-reference checks.
        errors = validate_brief(resolved, pages)
        if errors:
            return None, errors
        for claim, selected in zip(resolved['claims'], submission['claims']):
            claim.update(source_id=selected['source_id'], excerpt_id=selected['excerpt_id'])
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
    return {'start_url': reader.root, 'guide_version': guide_version,
            'allowed_urls': sorted(reader.allowed), 'sources': deepcopy(sources.items),
            'events': compact, 'remaining_steps_including_this': remaining_steps}
