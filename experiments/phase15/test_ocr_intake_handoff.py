import unittest
from ocr_intake_handoff import make_review_handoff

class OcrHandoffTests(unittest.TestCase):
    def setUp(self):
        self.result = {'status':'human_review_required', 'source_sha256':'a'*64,
                       'engine_sha256':'b'*64, 'model_sha256':{'eng.traineddata':'c'*64},
                       'extracted_text_untrusted':'Synthetic OCR: 100'}

    def handoff(self, **kwargs):
        return make_review_handoff(self.result, source_pdf_sha256='d'*64,
                                   source_page=kwargs.get('page', 1))

    def test_valid_candidate_stays_unpromotable(self):
        result = self.handoff()
        self.assertEqual(result['state'], 'requires_human_review')
        self.assertIs(result['promotable'], False)
        self.assertNotIn('quotation', result)
        self.assertNotIn('Synthetic OCR: 100', str(result))

    def test_rejects_success_or_missing_review_status(self):
        for status in ('approved', 'completed', None):
            self.result['status'] = status
            with self.assertRaises(ValueError): self.handoff()

    def test_rejects_invalid_page_or_digest(self):
        for page in (0, 51, True, '1'):
            with self.assertRaises(ValueError): self.handoff(page=page)
        self.result['engine_sha256'] = 'not-a-hash'
        with self.assertRaises(ValueError): self.handoff()

    def test_rejects_unsupported_model_and_oversized_text(self):
        self.result['model_sha256'] = {'unknown.traineddata':'c'*64}
        with self.assertRaises(ValueError): self.handoff()
        self.result['model_sha256'] = {'eng.traineddata':'c'*64}
        self.result['extracted_text_untrusted'] = 'x' * (256 * 1024 + 1)
        with self.assertRaises(ValueError): self.handoff()

if __name__ == '__main__':
    unittest.main()
