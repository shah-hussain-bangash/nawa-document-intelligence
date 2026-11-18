import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from make_review_packet import build_packet


class ReviewPacketTests(unittest.TestCase):
    def test_packet_separates_labels_and_does_not_overwrite(self):
        with TemporaryDirectory() as temp:
            output = Path(temp)/'packet'
            counts = build_packet(output)
            self.assertEqual(counts, {'questions':36,'passages':10,'claims':28})
            with (output/'reviewer'/'questions.csv').open(encoding='utf-8-sig',newline='') as stream:
                questions = list(csv.DictReader(stream))
            with (output/'reviewer'/'claims.csv').open(encoding='utf-8-sig',newline='') as stream:
                claims = list(csv.DictReader(stream))
            self.assertTrue(all(not row['reviewer_relevant_passage_ids'] for row in questions))
            self.assertTrue(all(not row['reviewer_verdict'] for row in claims))
            self.assertTrue(all(row['question_id'].startswith('Q') for row in questions))
            key = json.loads((output/'private'/'label-key.json').read_text(encoding='utf-8'))
            self.assertEqual(len(key['questions']),36)
            self.assertEqual(len(key['claims']),28)
            with self.assertRaises(FileExistsError):
                build_packet(output)


if __name__ == '__main__':
    unittest.main()

