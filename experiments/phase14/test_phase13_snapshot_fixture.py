import unittest
from copy import deepcopy

from hybrid_review import retrieve_for_review
from phase13_snapshot_fixture import fixture_snapshot


def record(doc, family, version, state='completed', tenant='a'):
    return {'document_id':doc*32, 'family_id':family*32, 'version':version,
            'tenant_id':tenant, 'job_state':state, 'filename':'synthetic.pdf',
            'sha256':'f'*64, 'source_verified':True,
            'result':{'evidence':{'total':{'source_text':f'Total AED {version}00',
                                          'method':'text_layer', 'page':2, 'page_line':4}}}}


class Phase13FixtureSnapshotTests(unittest.TestCase):
    def test_latest_completed_source_and_fixture_pdf_citation_are_selected(self):
        rows = [record('1','a',1), record('2','a',2), record('3','b',1,tenant='b')]
        snapshot = fixture_snapshot(rows, tenant='a', principal='analyst', membership_active=True)
        self.assertEqual([p.passage_id for p in snapshot['passages']], ['2'*32+':total'])
        self.assertEqual(snapshot['passages'][0].page, 2)
        self.assertEqual(snapshot['provenance']['2'*32+':total']['page_line'], 4)
        result = retrieve_for_review('total', tenant='a', principal='analyst',
                    load_snapshot=lambda:snapshot, embed_fn=lambda texts:[[1.0] for _ in texts])
        self.assertEqual(result['status'], 'requires_human_review')

    def test_changed_source_digest_or_line_is_rejected_on_recheck(self):
        original = record('1','a',1)
        for key, value in (('sha256', 'e'*64), ('page_line', 5)):
            changed = deepcopy(original)
            if key == 'page_line':
                changed['result']['evidence']['total']['page_line'] = value
            else:
                changed[key] = value
            snapshots = iter([fixture_snapshot([original], tenant='a', principal='analyst', membership_active=True),
                              fixture_snapshot([changed], tenant='a', principal='analyst', membership_active=True)])
            result = retrieve_for_review('total', tenant='a', principal='analyst',
                         load_snapshot=lambda:next(snapshots), embed_fn=lambda texts:[[1.0] for _ in texts])
            self.assertEqual(result, {'status':'unavailable'})

    def test_pending_new_version_does_not_fall_back(self):
        rows = [record('1','a',1), record('2','a',2,state='processing')]
        snapshot = fixture_snapshot(rows, tenant='a', principal='analyst', membership_active=True)
        self.assertEqual(snapshot['passages'], [])

    def test_rejects_unverified_ambiguous_or_missing_page_evidence(self):
        base = record('1','a',1)
        for broken in (dict(base, source_verified=False),
                       dict(base, filename='../source.pdf')):
            with self.assertRaises(ValueError):
                fixture_snapshot([broken], tenant='a', principal='analyst', membership_active=True)
        missing_page = deepcopy(base)
        del missing_page['result']['evidence']['total']['page']
        with self.assertRaises(ValueError):
            fixture_snapshot([missing_page], tenant='a', principal='analyst', membership_active=True)
        with self.assertRaises(ValueError):
            fixture_snapshot([base, record('2','a',1)], tenant='a', principal='analyst', membership_active=True)
        with self.assertRaises(PermissionError):
            fixture_snapshot([base], tenant='a', principal='analyst', membership_active=False)


if __name__ == '__main__':
    unittest.main()

