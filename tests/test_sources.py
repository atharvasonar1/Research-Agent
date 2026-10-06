"""Exact source selection and bounded correction context, with no network."""
from copy import deepcopy
import unittest

from gtm_research.evidence import Sources, excerpts, model_state
from gtm_research.schema import normalize_text
from helpers import ROOT, SELLERS, fixture_reader, submission


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.reader = fixture_reader()
        self.sources = Sources()
        self.page = self.reader.fetch(ROOT)
        self.sources.add(self.page)

    def test_cache_alias_and_later_fetch_do_not_renumber_ids(self):
        alias = {**self.page, 'requested_url': ROOT + 'alias'}
        self.assertEqual(self.sources.add(alias), 'S1')
        self.assertEqual(self.sources.add(self.reader.fetch(SELLERS)), 'S2')
        self.assertEqual(self.sources.add(self.page), 'S1')
        self.assertEqual(len(self.sources.items), 2)

    def test_selected_span_is_copied_with_unicode_and_provenance(self):
        page = {**self.page, 'text': 'A team® serves Harbor City. A second sentence.'}
        sources = Sources()
        sources.add(page)
        value = submission()
        result, errors = sources.resolve(value, {ROOT: page})
        self.assertEqual(errors, [])
        self.assertEqual(result['claims'][0]['excerpt'], page['text'])
        self.assertEqual(result['claims'][0]['url'], ROOT)
        self.assertEqual(result['claims'][0]['source_id'], 'S1')
        self.assertEqual(value['claims'][0]['excerpt_id'], 'E1')

    def test_forged_source_span_and_retyped_quote_are_rejected(self):
        for field, value in [('source_id', 'S9'), ('excerpt_id', 'E1 . . E2'),
                             ('excerpt_id', 'E99'), ('excerpt', 'A\\u00ae')]:
            with self.subTest(field=field):
                bad = submission()
                bad['claims'][0][field] = value
                resolved, errors = self.sources.resolve(bad, self.reader.pages)
                self.assertIsNone(resolved)
                self.assertTrue(errors)

    def test_span_from_another_source_does_not_resolve(self):
        # E2 exists on S2, not S1: excerpt IDs are scoped to sources.
        self.sources.add({**self.page, 'url': SELLERS, 'text': ('word ' * 300)})
        value = submission()
        value['claims'][0]['excerpt_id'] = 'E2'
        self.assertTrue(self.sources.resolve(value, self.reader.pages)[1])

    def test_resolved_text_still_checked_against_fetched_page(self):
        self.sources.items['S1']['excerpts']['E1'] = 'Not in fetched page'
        self.assertIn('claim:0:excerpt_not_found', self.sources.resolve(submission(), self.reader.pages)[1])

    def test_claim_reference_requirements_remain_after_resolution(self):
        value = submission()
        value['discovery_questions'][0]['premise_claim_refs'] = [999]
        self.assertTrue(self.sources.resolve(value, self.reader.pages)[1])

    def test_partition_preserves_text_and_each_span_is_contiguous(self):
        text = normalize_text(('A team® serves a region. Many useful details follow here. ' * 100))
        spans = excerpts(text)
        self.assertEqual(' '.join(spans.values()), text)
        self.assertTrue(all(span in text and len(span) <= 600 for span in spans.values()))

    def test_only_latest_draft_and_one_source_copy_resent_trace_unchanged(self):
        draft = submission()
        events = [{'step': 1, 'action': {'name': 'fetch_page', 'arguments': {'url': ROOT}},
                   'result': {'ok': True, 'page': self.page}}]
        for step in range(2, 7):
            events.append({'step': step, 'action': {'name': 'submit_brief', 'arguments': draft},
                           'usage': {'input_tokens': 1},
                           'result': {'ok': False, 'errors': ['claim:0:excerpt_not_found']}})
        before = deepcopy(events)
        state = model_state(self.reader, self.sources, events, 2, 'test')
        self.assertEqual(events, before)
        self.assertEqual(sum('arguments' in e['action'] for e in state['events'][1:]), 1)
        self.assertEqual(state['events'][-1]['action']['arguments'], draft)
        self.assertTrue(all('page' not in e['result'] for e in state['events']))
        self.assertEqual(len(state['sources']), 1)
        self.assertEqual(state['events'][-1]['result']['errors'], ['claim:0:excerpt_not_found'])
