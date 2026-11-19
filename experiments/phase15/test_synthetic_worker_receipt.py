import unittest
from synthetic_worker_receipt import issue_receipt, verify_receipt

class SyntheticWorkerReceiptTests(unittest.TestCase):
    def setUp(self):
        self.key = b'synthetic-test-key-not-for-use!!!'
        self.args = {'tenant':'synthetic-a', 'document_id':'a'*32, 'job_id':'b'*32,
                     'source_sha256':'c'*64, 'result':{'extraction_origin':'synthetic_text_worker_v1',
                                                     'total':'1050.00'}, 'key_id':'test-v1'}
        self.receipt = issue_receipt(self.key, **self.args)

    def test_valid_receipt_and_stable_key_order(self):
        args = dict(self.args, result={'total':'1050.00','extraction_origin':'synthetic_text_worker_v1'})
        self.assertTrue(verify_receipt(self.receipt, self.key, **args))

    def test_tampering_and_cross_tenant_or_job_replay_are_rejected(self):
        variants = [dict(self.args, tenant='synthetic-b'), dict(self.args, document_id='d'*32),
                    dict(self.args, job_id='e'*32), dict(self.args, source_sha256='f'*64),
                    dict(self.args, key_id='test-v2'),
                    dict(self.args, result={'extraction_origin':'synthetic_text_worker_v1','total':'1.00'})]
        for args in variants:
            with self.subTest(args=args): self.assertFalse(verify_receipt(self.receipt, self.key, **args))

    def test_wrong_key_or_bad_receipt_is_rejected(self):
        self.assertFalse(verify_receipt(self.receipt, b'x'*32, **self.args))
        self.assertFalse(verify_receipt({'payload':{}, 'mac_sha256':'0'*64}, self.key, **self.args))
        self.assertFalse(verify_receipt(self.receipt, b'short', **self.args))
        altered = {'payload':dict(self.receipt['payload'], version=True), 'mac_sha256':self.receipt['mac_sha256']}
        self.assertFalse(verify_receipt(altered, self.key, **self.args))

    def test_invalid_origin_and_large_result_are_rejected(self):
        bad = dict(self.args, result={'extraction_origin':'synthetic_ocr_worker_v1'})
        with self.assertRaises(ValueError): issue_receipt(self.key, **bad)
        bad = dict(self.args, result={'extraction_origin':'synthetic_text_worker_v1','body':'x'*(2*1024*1024)})
        with self.assertRaises(ValueError): issue_receipt(self.key, **bad)

if __name__ == '__main__':
    unittest.main()
