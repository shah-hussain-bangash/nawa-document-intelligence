"""Characterize in-flight work during recovery; this is not a safety pass."""
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from nawa_demo.authorization import Principal
from nawa_demo.dashboard import DashboardState
from nawa_demo.protected_api import make_protected_handler
from nawa_demo.session_draft import SessionStore


class RecoveryInFlightTests(unittest.TestCase):
    def test_authorized_request_can_finish_after_local_pause(self):
        entered = threading.Event()
        release = threading.Event()
        principal = Principal('synthetic-user', 'synthetic-tenant', 'analyst')
        sessions = SessionStore(lambda *_: principal)
        token = sessions.issue(principal.subject, principal.tenant)['session']

        class BlockingScoped:
            def list_items(self, actor):
                entered.set()
                if not release.wait(5):
                    raise TimeoutError('test request was not released')
                return [{'id': 'synthetic'}]

        server = ThreadingHTTPServer(('127.0.0.1', 0),
                                     make_protected_handler(BlockingScoped(), sessions, DashboardState()))
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        url = 'http://127.0.0.1:%s/api/quotations' % server.server_port
        result = []

        def request():
            try:
                with urlopen(Request(url, headers={'Cookie': 'nawa_session=' + token}), timeout=5) as response:
                    result.append((response.status, json.load(response)))
            except Exception as error:
                result.append(error)

        worker = threading.Thread(target=request, daemon=True)
        try:
            worker.start()
            self.assertTrue(entered.wait(5), 'synthetic request did not reach service')
            sessions.begin_recovery()
            with self.assertRaises(HTTPError) as rejected:
                urlopen(Request(url, headers={'Cookie': 'nawa_session=' + token}), timeout=5)
            self.assertEqual(rejected.exception.code, 403)
            rejected.exception.close()
            release.set()
            worker.join(5)
            self.assertFalse(worker.is_alive())
            self.assertEqual(result, [(200, {'quotations': [{'id': 'synthetic'}], 'storage': 'postgres'})])
        finally:
            release.set()
            worker.join(5)
            server.shutdown()
            server.server_close()
            server_thread.join(5)


if __name__ == '__main__':
    unittest.main()
