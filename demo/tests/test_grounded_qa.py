"""Phase 5 grounded answer, citation integrity, and permission isolation tests."""
import unittest
from pathlib import Path
from nawa_demo.grounded_qa import ask
from nawa_demo.retrieval import BM25Index, read_corpus

CORPUS = Path(__file__).resolve().parents[1] / 'samples/retrieval/passages.json'


class GroundedQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.passages = read_corpus(CORPUS)

    def idx(self, tenant='demo-a', principal='reviewer-a'):
        return BM25Index(self.passages, tenant_id=tenant, principal_id=principal)

    def test_english_answer_with_citation(self):
        r = ask(self.idx(), 'Example English Supplies grand total 1050')
        self.assertEqual(r['status'], 'answered')
        self.assertIn('Grand total AED 1050.00', r['answer'])
        self.assertEqual(r['citations'][0]['page'], 1)
        self.assertEqual(r['citations'][0]['source'], 'english_supplier.pdf')

    def test_arabic_answer(self):
        r = ask(self.idx(), 'شركة المثال الضريبة ٤٥')
        self.assertEqual(r['status'], 'answered')
        self.assertIn('٤٥', r['answer'])
        self.assertEqual(r['citations'][0]['passage_id'], 'ar-quote-v1-p1')

    def test_policy_evidence(self):
        r = ask(self.idx(), 'human reviewer verify evidence VAT discrepancies')
        self.assertEqual(r['status'], 'answered')
        self.assertEqual(r['citations'][0]['page'], 2)

    def test_no_hallucinated_answer(self):
        r = ask(self.idx(), 'interplanetary antimatter quantum')
        self.assertEqual(r['status'], 'insufficient_evidence')
        self.assertIsNone(r['answer'])
        self.assertEqual(r['citations'], [])

    def test_unauthorized_information_not_exposed(self):
        r = ask(self.idx(), 'Falcon Robotics confidential inspection')
        self.assertEqual(r['status'], 'insufficient_evidence')
        self.assertNotIn('Falcon', str(r['answer']))
        self.assertEqual(r['citations'], [])

    def test_other_tenant_isolation(self):
        r = ask(self.idx(), 'Exclusive tenant B satellite Orion')
        self.assertEqual(r['status'], 'insufficient_evidence')

    def test_admin_can_retrieve_restricted(self):
        r = ask(self.idx(principal='admin-a'), 'Falcon Robotics inspection')
        self.assertEqual(r['status'], 'answered')
        self.assertEqual(r['citations'][0]['source'], 'restricted.pdf')

    def test_wrong_tenant_even_same_principal(self):
        r = ask(self.idx(tenant='demo-a'), 'Exclusive tenant B quotation satellite equipment')
        self.assertEqual(r['status'], 'insufficient_evidence')

    def test_citation_verbatim_and_source(self):
        idx = self.idx()
        r = ask(idx, 'Example English Supplies grand total 1050')
        source = next(p for p in idx.passages if p.passage_id == r['citations'][0]['passage_id'])
        self.assertIn(r['answer'], source.text)
        self.assertEqual(r['citations'][0]['quote'], r['answer'])
        self.assertEqual(r['citations'][0]['version'], source.version)

    def test_empty_question_rejected(self):
        with self.assertRaises(ValueError):
            ask(self.idx(), ' ')

    def test_coverage_validation(self):
        for threshold in (0, 1.5, True):
            with self.subTest(threshold=threshold):
                with self.assertRaises(ValueError):
                    ask(self.idx(), 'supplier', min_coverage=threshold)

    def test_only_stopwords_abstains(self):
        self.assertEqual(ask(self.idx(), 'What is the?')['status'], 'insufficient_evidence')

    def test_repeated_answers_deterministic(self):
        self.assertEqual(ask(self.idx(), 'Example English Supplies grand total 1050'),
                         ask(self.idx(), 'Example English Supplies grand total 1050'))


if __name__ == '__main__':
    unittest.main()
