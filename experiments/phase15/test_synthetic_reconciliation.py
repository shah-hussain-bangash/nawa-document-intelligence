import unittest
from synthetic_reconciliation import classify_snapshots

class SyntheticReconciliationTests(unittest.TestCase):
    def test_all_valid_state_combinations_never_take_action(self):
        cases = [({'state':'pending','result_sha256':None},{'state':'pending','result_sha256':None},'both_pending'),
                 ({'state':'consumed','result_sha256':'a'*64},{'state':'pending','result_sha256':None},'manual_reconciliation_required'),
                 ({'state':'consumed','result_sha256':'a'*64},{'state':'completed','result_sha256':'a'*64},'observed_hashes_match'),
                 ({'state':'consumed','result_sha256':'a'*64},{'state':'completed','result_sha256':'b'*64},'inconsistent_observations'),
                 ({'state':'pending','result_sha256':None},{'state':'completed','result_sha256':'a'*64},'inconsistent_observations')]
        for ledger,app,status in cases:
            with self.subTest(status=status):
                result = classify_snapshots(ledger,app)
                self.assertEqual(result['status'],status)
                self.assertEqual(result['automatic_action'],'none')
                self.assertTrue(result['human_review_required'])

    def test_missing_or_malformed_observations_are_not_success(self):
        self.assertEqual(classify_snapshots(None, {'state':'pending'})['status'], 'missing_observation')
        self.assertEqual(classify_snapshots({'state':'consumed','result_sha256':'bad'},
                                           {'state':'pending','result_sha256':None})['status'], 'invalid_observation')
        self.assertEqual(classify_snapshots({'state':'pending','result_sha256':'a'*64},
                                           {'state':'pending','result_sha256':None})['status'], 'invalid_observation')

if __name__ == '__main__':
    unittest.main()
