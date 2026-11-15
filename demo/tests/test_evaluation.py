"""Phase 7 offline synthetic evaluation and citation-gate regression tests."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from nawa_demo.evaluation import ScriptedProvider, evaluate
from nawa_demo.rag import ask_rag
from nawa_demo.retrieval import BM25Index, read_corpus

BASE = Path(__file__).resolve().parents[1]
CORPUS = BASE / 'samples/retrieval/passages.json'
CASES = BASE / 'samples/evaluation/phase7_cases.json'


class Phase7EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.passages = read_corpus(CORPUS)

    def idx(self, principal='reviewer-a'):
        return BM25Index(self.passages, tenant_id='demo-a', principal_id=principal)

    def test_evaluation_report_passes(self):
        report = evaluate(CORPUS, CASES)
        self.assertTrue(report['all_passed'])
        self.assertEqual(report['failed_cases'], 0)
        self.assertEqual(report['total_cases'], 11)

    def test_report_contains_explicit_limitations(self):
        report = evaluate(CORPUS, CASES)
        self.assertTrue(any('semantic entailment' in x for x in report['limitations']))
        self.assertIn('no live model', report['scope'].lower())

    def test_reproducibility(self):
        self.assertEqual(evaluate(CORPUS, CASES), evaluate(CORPUS, CASES))

    def test_no_unauthorized_citations(self):
        report = evaluate(CORPUS, CASES)
        self.assertTrue(all(row['citation_authorized'] for row in report['cases']))

    def test_abstentions_have_no_answer_or_citations(self):
        for question in ('Falcon Robotics confidential inspection',
                         'Exclusive tenant B satellite Orion',
                         'interplanetary antimatter quantum'):
            with self.subTest(question=question):
                result = ask_rag(self.idx(), question)
                self.assertIsNone(result['answer'])
                self.assertEqual(result['citations'], [])

    def test_forged_citation_attack_rejected(self):
        result = ask_rag(self.idx(), 'Example English Supplies grand total 1050',
                         provider=ScriptedProvider('forged_citation'))
        self.assertEqual(result['status'], 'rejected_ungrounded')

    def test_fabricated_number_attack_rejected(self):
        result = ask_rag(self.idx(), 'Example English Supplies grand total 1050',
                         provider=ScriptedProvider('invented_number'))
        self.assertEqual(result['status'], 'rejected_ungrounded')

    def test_modified_quote_attack_rejected(self):
        result = ask_rag(self.idx(), 'Example English Supplies grand total 1050',
                         provider=ScriptedProvider('altered_quote'))
        self.assertEqual(result['status'], 'rejected_ungrounded')

    def test_injected_instruction_attempt_rejected(self):
        result = ask_rag(self.idx(), 'Example English Supplies grand total 1050',
                         provider=ScriptedProvider('injected_instruction'))
        self.assertEqual(result['status'], 'rejected_ungrounded')

    def test_unknown_attack_behavior_rejected(self):
        with self.assertRaises(ValueError):
            ScriptedProvider('not_supported').generate('question', [{'passage_id': 'p', 'text': 'test'}])

    def test_duplicate_case_ids_rejected(self):
        data = json.loads(CASES.read_text(encoding='utf-8'))
        data.append(dict(data[0]))
        with TemporaryDirectory() as td:
            path = Path(td) / 'cases.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                evaluate(CORPUS, path)

    def test_bad_case_status_rejected(self):
        data = json.loads(CASES.read_text(encoding='utf-8'))
        data[0]['expected_status'] = 'insecure_success'
        with TemporaryDirectory() as td:
            path = Path(td) / 'cases.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Unsupported'):
                evaluate(CORPUS, path)

    def test_bad_expected_passage_format_rejected(self):
        data = json.loads(CASES.read_text(encoding='utf-8'))
        data[0]['expected_passage_id'] = ''
        with TemporaryDirectory() as td:
            path = Path(td) / 'cases.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'passage ID'):
                evaluate(CORPUS, path)

    def test_evaluation_can_detect_wrong_expectation(self):
        data = json.loads(CASES.read_text(encoding='utf-8'))
        data[0]['expected_status'] = 'insufficient_evidence'
        data[0].pop('expected_passage_id')
        with TemporaryDirectory() as td:
            path = Path(td) / 'cases.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            result = evaluate(CORPUS, path)
            self.assertFalse(result['all_passed'])
            self.assertEqual(result['failed_cases'], 1)

    def test_scripted_provider_never_networks(self):
        provider = ScriptedProvider('invented_number')
        result = provider.generate('question', [{'passage_id': 'p', 'text': 'Grand total AED 1050.00'}])
        self.assertEqual(provider.calls, 1)
        self.assertIn('9000.00', result['answer'])


if __name__ == '__main__':
    unittest.main()
