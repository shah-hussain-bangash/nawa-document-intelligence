import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from compare_reviews import compare
from make_new_eval_packet import build_packet


class NewEvaluationPacketTests(unittest.TestCase):
    def test_packet_is_blinded_and_compatible_with_review_comparison(self):
        with TemporaryDirectory() as temp:
            packet=Path(temp)/'packet'
            self.assertEqual(build_packet(packet),{'questions':20,'passages':11,'claims':0})
            with (packet/'reviewer'/'questions.csv').open(encoding='utf-8-sig',newline='') as stream:
                rows=list(csv.DictReader(stream))
            self.assertTrue(all(not row['reviewer_relevant_passage_ids'] for row in rows))
            result=compare(packet/'private'/'label-key.json',[packet/'reviewer'])
            self.assertEqual(result['reviewers'][0]['packet_integrity'],'matched')
            self.assertEqual(result['reviewers'][0]['questions_vs_reference']['compared'],0)
            self.assertEqual(result['reviewers'][0]['questions_vs_reference']['not_compared'],20)
            with self.assertRaises(FileExistsError):
                build_packet(packet)


if __name__=='__main__':
    unittest.main()

