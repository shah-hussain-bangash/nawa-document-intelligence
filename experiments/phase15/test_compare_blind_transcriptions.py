import copy
import json
from pathlib import Path
import tempfile
import unittest

import compare_blind_transcriptions as compare
import blind_synthetic_review as review


class CompareBlindTranscriptionsTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent
        self.source = self.root / 'arabic-new-synthetic-pages'
        self.manifest = json.loads((self.source / 'manifest.json').read_text(encoding='utf-8'))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.review = review.create_packet(self.source, Path(self.temp.name) / 'review')

    def test_blank_packet_stays_unreviewed(self):
        result = compare.compare_review(self.review, self.manifest)
        self.assertEqual(result['status'], 'human_review_required')
        self.assertIs(result['promotable'], False)
        self.assertTrue(all(value == 'not_transcribed' for case in result['cases']
                            for value in case['fields'].values()))

    def test_matching_wrong_unclear_and_ambiguous_are_distinct(self):
        answers = self.review['cases'][0]['transcriptions']
        answers.update({'supplier':self.manifest['cases'][0]['fields']['supplier'],
                        'currency':'USD', 'subtotal':'unclear', 'vat_rate':'٥',
                        'vat_amount':'٦٠،٠٠', 'total':''})
        fields = compare.compare_review(self.review, self.manifest)['cases'][0]['fields']
        self.assertEqual(fields, {'supplier':'matches_fixture', 'currency':'differs_from_fixture',
            'subtotal':'reviewer_marked_unclear', 'vat_rate':'matches_fixture',
            'vat_amount':'numeric_format_uncomparable', 'total':'not_transcribed'})

    def test_rejects_tampered_identity_and_duplicate_case(self):
        changed = copy.deepcopy(self.review)
        changed['cases'][0]['image_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            compare.compare_review(changed, self.manifest)
        changed = copy.deepcopy(self.review)
        changed['cases'][1] = copy.deepcopy(changed['cases'][0])
        with self.assertRaises(ValueError):
            compare.compare_review(changed, self.manifest)

    def test_rejects_unknown_fields_and_duplicate_json_keys(self):
        changed = copy.deepcopy(self.review)
        changed['cases'][0]['transcriptions']['other'] = 'x'
        with self.assertRaises(ValueError):
            compare.compare_review(changed, self.manifest)
        path = Path(self.temp.name) / 'duplicate.json'
        path.write_text('{"case":1,"case":2}', encoding='utf-8')
        with self.assertRaises(ValueError):
            compare.read_json(path)


if __name__ == '__main__':
    unittest.main()
