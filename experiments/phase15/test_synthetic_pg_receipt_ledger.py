"""Integration tests; require a dedicated Phase 15 QA database."""
from concurrent.futures import ThreadPoolExecutor
import os
import unittest
from uuid import uuid4
from unittest.mock import MagicMock

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None

DSN = os.environ.get('NAWA_PHASE15_TEST_DSN')

@unittest.skipUnless(DSN and psycopg, 'Disposable Phase 15 PostgreSQL test not configured')
class SyntheticPostgresReceiptTests(unittest.TestCase):
    def setUp(self):
        from synthetic_pg_receipt_ledger import initialize, register
        from synthetic_worker_receipt import issue_receipt
        self.connect = lambda: psycopg.connect(DSN)
        self.schema = 'nawa_p15_' + uuid4().hex
        initialize(self.connect, self.schema)
        self.key = b'synthetic-test-key-not-for-use!!!'
        self.context = {'tenant':'synthetic-a','document_id':'a'*32,'job_id':'b'*32,
                        'source_sha256':'c'*64,'key_id':'test-v1'}
        self.result = {'extraction_origin':'synthetic_text_worker_v1','total':'1050.00'}
        register(self.connect,self.schema,**self.context)
        self.receipt = issue_receipt(self.key,**self.context,result=self.result)

    def consume(self, **changes):
        from synthetic_pg_receipt_ledger import consume
        args = {'job_id':self.context['job_id'],'tenant':self.context['tenant'],
                'receipt':self.receipt,'result':self.result,'keys':{'test-v1':self.key}}
        args.update(changes)
        return consume(self.connect,self.schema,**args)

    def test_concurrent_receipt_is_consumed_once(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(lambda _: self.consume(), range(2))), [False,True])
        with self.connect() as conn:
            self.assertEqual(conn.execute(sql.SQL('SELECT count(*) FROM {}.events').format(sql.Identifier(self.schema))).fetchone()[0], 1)

    def test_invalid_context_does_not_consume(self):
        self.assertFalse(self.consume(tenant='synthetic-b'))
        self.assertFalse(self.consume(result=dict(self.result,total='1.00')))
        self.assertFalse(self.consume(keys={'test-v1':b'x'*32}))
        self.assertTrue(self.consume())

    def test_event_failure_rolls_back_consumption(self):
        with self.connect() as conn:
            conn.execute(sql.SQL("ALTER TABLE {}.events ADD CONSTRAINT synthetic_failure CHECK (event_type <> 'receipt_consumed')")
                         .format(sql.Identifier(self.schema)))
        with self.assertRaises(psycopg.Error):
            self.consume()
        with self.connect() as conn:
            row = conn.execute(sql.SQL('SELECT state,result_sha256,receipt_mac FROM {}.receipts')
                               .format(sql.Identifier(self.schema))).fetchone()
            self.assertEqual(row, ('pending',None,None))
            self.assertEqual(conn.execute(sql.SQL('SELECT count(*) FROM {}.events').format(sql.Identifier(self.schema))).fetchone()[0], 0)

    def test_non_qa_database_is_rejected_before_schema_creation(self):
        from synthetic_pg_receipt_ledger import initialize
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = ('not_a_qa_database',)
        context = MagicMock()
        context.__enter__.return_value = conn
        with self.assertRaisesRegex(ValueError, 'QA database'):
            initialize(lambda: context, 'nawa_p15_' + uuid4().hex)
        self.assertEqual(conn.execute.call_count, 1)

if __name__ == '__main__':
    unittest.main()
