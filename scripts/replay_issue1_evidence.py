"""Offline saved-trace diagnosis and byte-size comparison. No credentials/network.

Usage: python scripts/replay_issue1_evidence.py TRACE OUTPUT_JSON
Byte sizes measure serialized model state, not provider token estimates.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

from gtm_research.evidence import Sources, model_state
from gtm_research.model import GUIDE_VERSION
from gtm_research.schema import normalize_text, validate_brief


def inspect(trace):
    sources = Sources()
    reader = SimpleNamespace(root=trace['start_url'], allowed={trace['start_url']})
    pages = {p['url']: p for p in trace['pages']}
    events = []
    rows, mismatches = [], []
    byte_size = lambda v: len(json.dumps(v, ensure_ascii=False).encode('utf-8'))
    for event in trace['events']:
        step = event['step']
        old = {'start_url': reader.root, 'guide_version': trace['metadata']['guide_version'],
               'allowed_urls': sorted(reader.allowed), 'events': deepcopy(events),
               'remaining_steps_including_this': 9-step}
        new = model_state(reader, sources, events, 9-step, GUIDE_VERSION)
        rows.append({'step': step, 'old_state_bytes': byte_size(old), 'new_state_bytes': byte_size(new),
                     'observed_old_input_tokens': event.get('usage', {}).get('input_tokens')})
        result = event.get('result', {})
        if 'page' in result:
            page = result['page']
            sources.add(page)
            reader.allowed.update(page['links'])
            reader.allowed.add(page['url'])
        elif event.get('action', {}).get('name') == 'submit_brief':
            draft = event['action']['arguments']
            errors = validate_brief(draft, pages)
            assert errors == result['errors'], (step, errors, result['errors'])
            assert sources.resolve(draft, pages)[1], 'Old free-text citations must not bypass ID contract'
            for index, claim in enumerate(draft['claims']):
                quote = normalize_text(claim['excerpt'])
                text = normalize_text(pages[claim['url']]['text'])
                if quote not in text:
                    mismatches.append({'step': step, 'claim': index+1,
                        'literal_unicode_escape': '\\u00ae' in quote,
                        'fragment_offsets': [text.find(part) for part in quote.split(' . . ')]})
        events.append(deepcopy(event))
    # A narrow, manually supplied supported selection exercises the same resolver.
    sid = sources.by_url[trace['pages'][0]['url']]
    eid = next(key for key, text in sources.items[sid]['excerpts'].items()
               if 'affiliated with Coldwell Banker Realty' in text)
    corrected = deepcopy(trace['events'][-1]['action']['arguments'])
    corrected['claims'] = [{'claim': 'The site identifies The Jills Zeder Group as affiliated with Coldwell Banker Realty.',
                             'source_id': sid, 'excerpt_id': eid}]
    corrected['fit_rationale'] = {'text': 'This identity warrants further research; operating needs remain unknown.', 'claim_refs': [1]}
    corrected['discovery_questions'] = [{'question': 'Which CRM, if any, do you use?', 'premise_claim_refs': []}]
    resolved, errors = sources.resolve(corrected, pages)
    assert not errors, errors
    assert resolved['claims'][0]['excerpt'] in normalize_text(pages[resolved['claims'][0]['url']]['text'])
    for field, invalid in [('source_id', 'S999'), ('excerpt_id', eid+' . . E999'), ('excerpt', 'fake quote')]:
        bad = deepcopy(corrected)
        bad['claims'][0][field] = invalid
        assert sources.resolve(bad, pages)[1]
    # Counterfactual state sizes above intentionally retain the original latest draft:
    # no optimistic assumption about what the model would write under the new schema.
    return {'rows': rows, 'mismatches': mismatches, 'checks_passed': True,
            'comparison': 'Same saved events; new state compacts history. Latest legacy draft retained conservatively.',
            'corrected_selection': corrected, 'resolved_selection': resolved}


if __name__ == '__main__':
    report = inspect(json.loads(Path(sys.argv[1]).read_text()))
    Path(sys.argv[2]).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: value for key, value in report.items() if key not in ('corrected_selection','resolved_selection')}, indent=2))
