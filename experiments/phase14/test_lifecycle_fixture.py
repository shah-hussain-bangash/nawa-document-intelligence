import unittest
from dataclasses import replace

from lifecycle_fixture import eligible, embed_eligible, recheck_results
from retrieval import Passage


def passage(pid, document, tenant='a', principals=('analyst',)):
    return Passage(pid, document, 'v1', tenant, 1, pid, principals, pid, 'synthetic')


class LifecycleFixtureTests(unittest.TestCase):
    def setUp(self):
        self.items = [passage('old', 'quote'), passage('new', 'quote'),
                      passage('deleted', 'removed'), passage('revoked', 'denied'),
                      passage('other-tenant', 'foreign', 'b'),
                      passage('other-user', 'private', principals=('admin',))]
        self.states = {'old':'superseded', 'new':'current', 'deleted':'deleted',
                       'revoked':'revoked', 'other-tenant':'current', 'other-user':'current'}

    def test_before_embedding_and_explicit_authorized_history(self):
        seen = []
        def fake(texts):
            seen.extend(texts)
            return [[1.0] for _ in texts]
        selected, _ = embed_eligible(self.items, tenant='a', principal='analyst',
                                     lifecycle=self.states, embedding_fn=fake)
        self.assertEqual([p.passage_id for p in selected], ['new'])
        self.assertEqual(seen, ['new'])
        with_history = eligible(self.items, tenant='a', principal='analyst',
                                lifecycle=self.states, history_document='quote')
        self.assertEqual([p.passage_id for p in with_history], ['old', 'new'])

    def test_recheck_rejects_newly_revoked_or_deleted_candidate(self):
        for state in ('revoked', 'deleted'):
            changed = {**self.states, 'new':state}
            with self.assertRaises(ValueError):
                recheck_results(self.items, ['new'], tenant='a', principal='analyst',
                                lifecycle=changed)
        with self.assertRaises(ValueError):
            recheck_results(self.items, ['other-tenant'], tenant='a', principal='analyst',
                            lifecycle=self.states)
        access_removed = [replace(p, allowed_principals=('admin',)) if p.passage_id == 'new' else p
                          for p in self.items]
        with self.assertRaises(ValueError):
            recheck_results(access_removed, ['new'], tenant='a', principal='analyst',
                            lifecycle=self.states)

    def test_missing_metadata_and_identity_fail_closed(self):
        with self.assertRaises(ValueError):
            eligible(self.items, tenant='a', principal='analyst', lifecycle={})
        with self.assertRaises(ValueError):
            eligible(self.items, tenant='', principal='analyst', lifecycle=self.states)


if __name__ == '__main__':
    unittest.main()

