from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from synthetic_receipt_ledger import initialize, register, consume
from synthetic_worker_receipt import issue_receipt

class SyntheticReceiptLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'synthetic.db'
        initialize(self.path)
        self.key = b'synthetic-test-key-not-for-use!!!'
        self.context = {'tenant':'synthetic-a', 'document_id':'a'*32, 'job_id':'b'*32,
                        'source_sha256':'c'*64, 'key_id':'test-v1'}
        self.result = {'extraction_origin':'synthetic_text_worker_v1', 'total':'1050.00'}
        register(self.path, **self.context)
        self.receipt = issue_receipt(self.key, **self.context, result=self.result)

    def consume(self, **overrides):
        args = {'job_id':self.context['job_id'], 'tenant':self.context['tenant'],
                'receipt':self.receipt, 'result':self.result, 'keys':{'test-v1':self.key}}
        args.update(overrides)
        return consume(self.path, **args)

    def test_accepts_once_and_rejects_replay(self):
        self.assertTrue(self.consume())
        self.assertFalse(self.consume())

    def test_bad_result_or_wrong_tenant_does_not_consume(self):
        self.assertFalse(self.consume(tenant='synthetic-b'))
        self.assertFalse(self.consume(result=dict(self.result, total='1.00')))
        self.assertFalse(self.consume(keys={'test-v1':b'x'*32}))
        self.assertTrue(self.consume())

    def test_concurrent_replay_accepts_at_most_once(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.consume(), range(2)))
        self.assertEqual(sorted(results), [False, True])

    def test_database_does_not_store_the_test_key_or_raw_result(self):
        self.assertTrue(self.consume())
        with closing(sqlite3.connect(self.path)) as conn:
            row = conn.execute('SELECT * FROM synthetic_receipts').fetchone()
        self.assertNotIn(self.key.decode('ascii'), str(row))
        self.assertNotIn('1050.00', str(row))

if __name__ == '__main__':
    unittest.main()
