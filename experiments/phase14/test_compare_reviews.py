import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from compare_reviews import compare
from make_review_packet import build_packet


def edit(path, changes):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    changes(rows)
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class CompareReviewTests(unittest.TestCase):
    def test_partial_reviews_and_two_reviewer_disagreement(self):
        with TemporaryDirectory() as temp:
            one, two = Path(temp)/'one', Path(temp)/'two'
            build_packet(one)
            build_packet(two)
            edit(one/'reviewer'/'claims.csv',lambda rows:rows[0].update(reviewer_verdict='SUPPORTED'))
            edit(two/'reviewer'/'claims.csv',lambda rows:rows[0].update(reviewer_verdict='UNSUPPORTED'))
            result = compare(one/'private'/'label-key.json',[one/'reviewer',two/'reviewer'])
            self.assertEqual(result['reviewers'][0]['packet_integrity'],'matched')
            self.assertEqual(result['between_reviewers']['claims']['compared'],1)
            self.assertEqual(len(result['between_reviewers']['claims']['disagreement_ids']),1)
            self.assertEqual(result['between_reviewers']['claims']['not_compared'],27)
            self.assertEqual(result['between_reviewers']['questions']['compared'],0)

    def test_rejects_changed_evidence_and_invalid_judgment(self):
        with TemporaryDirectory() as temp:
            output=Path(temp)/'packet'
            build_packet(output)
            folder=output/'reviewer'
            key=output/'private'/'label-key.json'
            edit(folder/'claims.csv',lambda rows:rows[0].update(evidence='changed'))
            with self.assertRaises(ValueError):
                compare(key,[folder])
        with TemporaryDirectory() as temp:
            output=Path(temp)/'packet'
            build_packet(output)
            folder=output/'reviewer'
            edit(folder/'questions.csv',lambda rows:rows[0].update(reviewer_relevant_passage_ids='P999'))
            with self.assertRaises(ValueError):
                compare(output/'private'/'label-key.json',[folder])


if __name__ == '__main__':
    unittest.main()

