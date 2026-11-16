"""Phase 9 local dashboard: no network, external model, or real documents."""
import base64
import json
from pathlib import Path
import threading
import unittest
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from nawa_demo.dashboard import DashboardState, make_handler

BASE = Path(__file__).resolve().parents[1]


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.state = DashboardState()

    def test_load_english(self):
        q = self.state.add_sample('english_quote.txt')['quotation']
        self.assertEqual(q['total'], '1050.00')
        self.assertEqual(q['evidence']['total']['line'], 6)

    def test_load_arabic(self):
        q = self.state.add_sample('arabic_quote.txt')['quotation']
        self.assertEqual(q['total'], '945.00')

    def test_sample_not_allowlisted(self):
        with self.assertRaises(ValueError):
            self.state.add_sample('../../.git/config')

    def test_upload_utf8(self):
        content = (BASE / 'samples/english_quote.txt').read_bytes()
        row = self.state.add_upload('demo.txt', base64.b64encode(content).decode())
        self.assertEqual(row['quotation']['total'], '1050.00')

    def test_disallow_traversal(self):
        with self.assertRaises(ValueError):
            self.state.add_upload('../demo.txt', 'YQ==')

    def test_reject_bad_type(self):
        with self.assertRaises(ValueError):
            self.state.add_upload('x.sh', 'YQ==')

    def test_reject_bad_encoding(self):
        with self.assertRaises(ValueError):
            self.state.add_upload('x.txt', '%%%')

    def test_compare(self):
        a = self.state.add_sample('english_quote.txt')['id']
        b = self.state.add_sample('arabic_quote.txt')['id']
        result = self.state.compare([a,b])
        self.assertEqual(result['lowest_valid_total'], 'شركة المثال للتوريدات')

    def test_compare_excludes_invalid(self):
        a = self.state.add_sample('incorrect_vat_quote.txt')['id']
        b = self.state.add_sample('english_quote.txt')['id']
        result = self.state.compare([a,b])
        self.assertEqual(result['lowest_valid_total'], 'Example English Supplies')

    def test_reject_duplicate_compare(self):
        a = self.state.add_sample('english_quote.txt')['id']
        with self.assertRaises(ValueError):
            self.state.compare([a,a])

    def test_review_approve(self):
        a = self.state.add_sample('english_quote.txt')['id']
        review = self.state.review_start(a)
        self.assertEqual(review['revision'], 1)
        result = self.state.review_decision({'id':a,'actor':'reviewer-1','decision':'approve',
                                             'reason':'Synthetic evidence checked','expected_revision':1})
        self.assertEqual(result['status'],'approved')
        self.assertEqual(len(result['history']),2)

    def test_invalid_approval_blocked(self):
        a = self.state.add_sample('incorrect_vat_quote.txt')['id']
        self.state.review_start(a)
        with self.assertRaises(ValueError):
            self.state.review_decision({'id':a,'actor':'reviewer-1','decision':'approve',
                                         'reason':'Test','expected_revision':1})

    def test_stale_revision(self):
        a=self.state.add_sample('english_quote.txt')['id']
        self.state.review_start(a)
        with self.assertRaises(ValueError):
            self.state.review_decision({'id':a,'actor':'reviewer-1','decision':'approve',
                                         'reason':'Test','expected_revision':0})

    def test_review_correction_rechecks(self):
        a=self.state.add_sample('english_quote.txt')['id']
        self.state.review_start(a)
        result=self.state.review_correction({'id':a,'actor':'reviewer-1','field':'total','value':'900.00',
                                             'reason':'Synthetic mismatch','source':'english_quote.txt',
                                             'line':6,'quote':'Grand Total: 1050.00','expected_revision':1})
        self.assertFalse(result['checks']['total_matches_components'])

    def test_no_unknown_review(self):
        with self.assertRaises(ValueError):
            self.state.review_show('unknown')


class LocalHTTPTests(unittest.TestCase):
    def setUp(self):
        self.state=DashboardState()
        self.server=HTTPServer(('127.0.0.1',0), make_handler(self.state))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.root=f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_get_dashboard(self):
        with urlopen(self.root+'/') as response:
            body=response.read().decode()
            self.assertIn('Document review, made traceable',body)
            self.assertIn('frame-ancestors',response.headers['Content-Security-Policy'])

    def test_get_assets(self):
        for path in ('/style.css','/app.js'):
            with self.subTest(path=path), urlopen(self.root+path) as response:
                self.assertEqual(response.status,200)

    def test_quotation_list_reflects_loaded_items(self):
        self.state.add_sample('arabic_quote.txt')
        with urlopen(self.root+'/api/quotations') as response:
            result = json.load(response)
        self.assertEqual(result['storage'], 'memory')
        self.assertEqual(result['quotations'][0]['quotation']['total'], '945.00')

    def test_storage_failure_returns_safe_error(self):
        def unavailable():
            raise RuntimeError('sensitive connection details')
        self.state.list_items = unavailable
        with self.assertRaises(HTTPError) as caught:
            urlopen(self.root+'/api/quotations')
        self.assertEqual(caught.exception.code, 503)
        self.assertNotIn('sensitive', caught.exception.read().decode())

    def test_readiness_tracks_storage_failure(self):
        with urlopen(self.root+'/api/ready') as response:
            self.assertEqual(json.load(response)['status'], 'ready')
        def unavailable():
            raise RuntimeError('private details')
        self.state.ready = unavailable
        with self.assertRaises(HTTPError) as caught:
            urlopen(self.root+'/api/ready')
        self.assertEqual(caught.exception.code, 503)
        self.assertNotIn('private', caught.exception.read().decode())

    def test_reject_cross_origin(self):
        payload=json.dumps({'name':'english_quote.txt'}).encode()
        request=Request(self.root+'/api/load-sample',payload,headers={
            'Origin':'https://evil.example','Content-Type':'application/json'})
        with self.assertRaises(HTTPError) as e:
            urlopen(request)
        self.assertEqual(e.exception.code,400)
        self.assertEqual(len(self.state.items),0)

    def test_http_load(self):
        payload=json.dumps({'name':'arabic_quote.txt'}).encode()
        request=Request(self.root+'/api/load-sample',payload,headers={'Content-Type':'application/json'})
        with urlopen(request) as response:
            result=json.load(response)
        self.assertEqual(result['quotation']['total'],'945.00')


if __name__ == '__main__':
    unittest.main()
