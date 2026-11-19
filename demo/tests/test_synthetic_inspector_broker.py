import unittest
from unittest.mock import Mock
from nawa_demo.authorization import Principal
from nawa_demo.session_draft import SessionStore
from nawa_demo.synthetic_inspector_broker import SyntheticInspectorBroker

class SyntheticInspectorBrokerTests(unittest.TestCase):
    def setUp(self):
        self.members = {('subject-a','tenant-a'):Principal('subject-a','tenant-a','viewer'),
                        ('subject-b','tenant-b'):Principal('subject-b','tenant-b','viewer')}
        self.sessions = SessionStore(lambda subject,tenant:self.members.get((subject,tenant)))
        self.a = self.sessions.issue('subject-a','tenant-a')['session']
        self.b = self.sessions.issue('subject-b','tenant-b')['session']
        self.ledger_a, self.app_a = Mock(), Mock()
        self.ledger_b, self.app_b = Mock(), Mock()
        self.routes = {'tenant-a':{'ledger_connect':self.ledger_a,'app_connect':self.app_a,'schema':'schema-a'},
                       'tenant-b':{'ledger_connect':self.ledger_b,'app_connect':self.app_b,'schema':'schema-b'}}
        self.inspector = Mock(return_value={'status':'synthetic'})
        self.broker = SyntheticInspectorBroker(self.sessions,self.routes,self.inspector)

    def test_session_selects_server_route_not_a_client_tenant(self):
        self.broker.inspect(self.a, 'a'*32)
        self.inspector.assert_called_once_with(self.ledger_a,self.app_a,schema='schema-a',job_id='a'*32,tenant='tenant-a')
        with self.assertRaises(TypeError):
            self.broker.inspect(self.a, 'a'*32, tenant='tenant-b')

    def test_revoked_membership_blocks_before_inspection(self):
        self.members[('subject-a','tenant-a')] = None
        with self.assertRaises(PermissionError): self.broker.inspect(self.a, 'a'*32)
        self.inspector.assert_not_called()

    def test_unknown_session_or_route_fails_closed(self):
        with self.assertRaises(PermissionError): self.broker.inspect('unknown', 'a'*32)
        broker = SyntheticInspectorBroker(self.sessions,{},self.inspector)
        with self.assertRaises(PermissionError): broker.inspect(self.b, 'a'*32)
        self.inspector.assert_not_called()

    def test_invalid_job_does_not_call_inspector(self):
        with self.assertRaises(ValueError): self.broker.inspect(self.a, 'not-a-job')
        self.inspector.assert_not_called()

    def test_route_copy_does_not_follow_later_mapping_changes(self):
        self.routes['tenant-a']['schema'] = 'changed'
        self.broker.inspect(self.a, 'a'*32)
        self.assertEqual(self.inspector.call_args.kwargs['schema'], 'schema-a')

    def test_inspector_failure_does_not_expose_details(self):
        self.inspector.side_effect = OSError('private synthetic connection detail')
        with self.assertRaises(RuntimeError) as caught:
            self.broker.inspect(self.a, 'a'*32)
        self.assertNotIn('private synthetic connection detail', str(caught.exception))

if __name__ == '__main__':
    unittest.main()
