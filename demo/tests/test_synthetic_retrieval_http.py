"""Opt-in HTTP tests with synthetic in-memory identities and passages."""
import json
import threading
import unittest
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from nawa_demo.authorization import Principal
from nawa_demo.dashboard import DashboardState
from nawa_demo.protected_api import make_protected_handler
from nawa_demo.retrieval import Passage
from nawa_demo.session_draft import SessionStore
from nawa_demo.synthetic_live_retrieval import SyntheticLiveRetrieval


class SyntheticRetrievalHttpTests(unittest.TestCase):
    def setUp(self):
        self.members = {('alice','a'):Principal('alice','a','analyst'),
                        ('bob','a'):Principal('bob','a','viewer'),
                        ('eve','b'):Principal('eve','b','viewer')}
        self.docs = [Passage.from_dict({'passage_id':'a-v1','document_id':'doc-a','version':'1',
            'tenant_id':'a','page':1,'text':'alpha shared','allowed_principals':['alice'],'source':'a.txt'}),
            Passage.from_dict({'passage_id':'b-v1','document_id':'doc-b','version':'1',
            'tenant_id':'b','page':1,'text':'beta shared','allowed_principals':['eve'],'source':'b.txt'})]
        lookup = lambda s,t:self.members.get((s,t))
        self.sessions = SessionStore(lookup)
        self.tokens = {key:self.sessions.issue(*key)['session'] for key in self.members}
        self.retrieval = SyntheticLiveRetrieval(lookup, lambda p:list(self.docs))
        handler = make_protected_handler(None, self.sessions, DashboardState(), synthetic_retrieval=self.retrieval)
        self.server = HTTPServer(('127.0.0.1', 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:%s' % self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)

    def request(self, path, token=None, headers=None):
        values = dict(headers or {})
        if token:
            values['Cookie'] = 'nawa_session=' + token
        try:
            with urlopen(Request(self.url + path, headers=values), timeout=5) as response:
                return response.status, json.load(response), response.headers.get('Cache-Control')
        except HTTPError as error:
            with error:
                return error.code, json.load(error), error.headers.get('Cache-Control')

    def test_session_scopes_search_and_source(self):
        search = '/api/synthetic-evidence/search?' + urlencode({'q':'shared'})
        self.assertEqual(self.request(search)[0], 403)
        status, result, cache = self.request(search, self.tokens[('alice','a')],
                                              {'X-Tenant':'b', 'X-Role':'reviewer'})
        self.assertEqual((status, cache), (200, 'no-store'))
        self.assertEqual([p['document_id'] for p in result['passages']], ['doc-a'])
        self.assertNotIn('tenant_id', result['passages'][0])
        self.assertNotIn('allowed_principals', result['passages'][0])
        self.assertEqual(self.request(search, self.tokens[('bob','a')])[1]['passages'], [])
        self.assertEqual(self.request(search, self.tokens[('eve','b')])[1]['passages'][0]['document_id'], 'doc-b')
        own = '/api/synthetic-evidence/source?' + urlencode({'id':'a-v1'})
        self.assertEqual(self.request(own, self.tokens[('alice','a')])[1]['passage']['text'], 'alpha shared')
        self.assertEqual(self.request(own, self.tokens[('bob','a')])[0], 503)
        self.assertEqual(self.request(own, self.tokens[('eve','b')])[0], 503)
        self.docs.pop(0)
        self.assertEqual(self.request(own, self.tokens[('alice','a')])[0], 503)

    def test_invalid_parameters_and_membership_revocation(self):
        token = self.tokens[('alice','a')]
        self.assertEqual(self.request('/api/synthetic-evidence/search?q=x&q=y', token)[0], 400)
        self.assertEqual(self.request('/api/synthetic-evidence/search?q=x&tenant=b', token)[0], 400)
        self.members.pop(('alice','a'))
        self.assertEqual(self.request('/api/synthetic-evidence/search?q=shared', token)[0], 403)


if __name__ == '__main__':
    unittest.main()
