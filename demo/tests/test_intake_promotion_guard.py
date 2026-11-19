import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4
from nawa_demo.core import extract
from nawa_demo.intake_promotion_guard import require_text_only_result
from nawa_demo.intake_scoped import ScopedIntake

SAMPLES = Path(__file__).resolve().parents[1] / 'samples'

class PromotionGuardTests(unittest.TestCase):
    def setUp(self):
        self.quote = extract(SAMPLES / 'english_quote.txt')

    def test_existing_text_and_text_layer_results_remain_allowed(self):
        self.assertIsNone(require_text_only_result(self.quote))
        pdf = dict(self.quote, input_type='text_layer_pdf', evidence={
            k:dict(v, method='text_layer') for k, v in self.quote['evidence'].items()})
        self.assertIsNone(require_text_only_result(pdf))
        self.assertIsNone(require_text_only_result(dict(pdf, ocr_pages=[])))
        self.assertIsNone(require_text_only_result(dict(self.quote, extraction_origin='synthetic_text_worker_v1')))

    def test_review_and_ocr_markers_are_rejected(self):
        cases = [dict(self.quote, status='human_review_required'),
                 dict(self.quote, state='requires_human_review'),
                 dict(self.quote, promotable=False),
                 dict(self.quote, input_type='ocr_pdf'),
                 dict(self.quote, input_type='mixed_text_and_ocr_pdf'),
                 dict(self.quote, input_type=None),
                 dict(self.quote, extraction_origin='synthetic_ocr_worker_v1'),
                 dict(self.quote, extraction_origin=None),
                 dict(self.quote, ocr_pages=[1]),
                 dict(self.quote, ocr_pages=None),
                 dict(self.quote, evidence={'total':{'method':'ocr'}}),
                 dict(self.quote, evidence={'total':{'ocr_confidence':0.9}}),
                 dict(self.quote, evidence={})]
        for candidate in cases:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError): require_text_only_result(candidate)

    def test_actual_promotion_rejects_before_source_or_database_mutation(self):
        candidate = dict(self.quote, status='human_review_required')
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = ('completed', candidate, 'a'*64)
        context = MagicMock()
        context.__enter__.return_value = conn
        store = MagicMock()
        service = ScopedIntake(lambda: context, store)
        principal = MagicMock(tenant='synthetic-tenant')
        with patch.object(service, '_require'), patch.object(service, '_recheck'):
            with self.assertRaises(ValueError): service.promote(principal, uuid4().hex)
        store.read_verified.assert_not_called()
        self.assertEqual(conn.execute.call_count, 1)

    def test_actual_promotion_accepts_existing_text_result(self):
        conn = MagicMock()
        conn.execute.return_value.fetchone.side_effect = [('completed', self.quote, 'a'*64), None, (0,)]
        context = MagicMock()
        context.__enter__.return_value = conn
        store = MagicMock()
        service = ScopedIntake(lambda: context, store)
        principal = MagicMock(tenant='synthetic-tenant')
        with patch.object(service, '_require'), patch.object(service, '_recheck'):
            result = service.promote(principal, uuid4().hex)
        self.assertTrue(result['created'])
        self.assertEqual(result['quotation']['total'], '1050.00')
        store.read_verified.assert_called_once()

if __name__ == '__main__':
    unittest.main()
