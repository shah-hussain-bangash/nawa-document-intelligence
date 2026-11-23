import unittest
from dataclasses import replace

from hybrid_review import retrieve_for_review
from retrieval import Passage


def make(pid, document, tenant='a', users=('analyst',)):
    return Passage(pid, document, 'v1', tenant, 1, pid, users, pid+'.txt', 'synthetic')


class HybridReviewTests(unittest.TestCase):
    def setUp(self):
        self.passages = [make('old', 'quote'), make('current', 'quote'),
                         make('private', 'secret', users=('admin',)),
                         make('foreign', 'other', tenant='b')]
        self.snapshot = {'old':'superseded', 'current':'current',
                         'private':'current', 'foreign':'current'}

    def test_filters_before_embedding_and_never_auto_approves(self):
        seen = []
        def embed(texts):
            seen.extend(texts)
            return [[1.0, 0.0] for _ in texts]
        result = retrieve_for_review('current', tenant='a', principal='analyst',
                                     load_snapshot=lambda:{'passages':self.passages,'lifecycle':self.snapshot}, embed_fn=embed)
        self.assertEqual(seen, ['current', 'current'])
        self.assertEqual(result['status'], 'requires_human_review')
        self.assertEqual([p['passage_id'] for p in result['evidence']], ['current'])
        self.assertNotIn('answer', result)
        self.assertNotIn('approval', result)

    def test_revocation_between_search_and_recheck_closes_batch(self):
        snapshots = iter([{'passages':self.passages,'lifecycle':self.snapshot},
                          {'passages':self.passages,'lifecycle':{**self.snapshot, 'current':'revoked'}}])
        result = retrieve_for_review('current', tenant='a', principal='analyst',
                                     load_snapshot=lambda:next(snapshots),
                                     embed_fn=lambda texts:[[1.0] for _ in texts])
        self.assertEqual(result, {'status':'unavailable'})
        changed = [replace(p, allowed_principals=('admin',)) if p.passage_id == 'current' else p
                   for p in self.passages]
        snapshots = iter([{'passages':self.passages,'lifecycle':self.snapshot},
                          {'passages':changed,'lifecycle':self.snapshot}])
        result = retrieve_for_review('current', tenant='a', principal='analyst',
                                     load_snapshot=lambda:next(snapshots),
                                     embed_fn=lambda texts:[[1.0] for _ in texts])
        self.assertEqual(result, {'status':'unavailable'})

    def test_model_failure_and_missing_lifecycle_close_batch(self):
        def failed(_):
            raise OSError('model unavailable')
        result = retrieve_for_review('current', tenant='a', principal='analyst',
                                     load_snapshot=lambda:{'passages':self.passages,'lifecycle':self.snapshot}, embed_fn=failed)
        self.assertEqual(result, {'status':'unavailable'})

    def test_invalid_embedding_does_not_return_evidence(self):
        for value in (float('nan'), float('inf'), True, 10**400):
            with self.subTest(value=value):
                result = retrieve_for_review('current', tenant='a', principal='analyst',
                    load_snapshot=lambda:{'passages':self.passages,'lifecycle':self.snapshot},
                    embed_fn=lambda texts:[[value] for _ in texts])
                self.assertEqual(result, {'status':'unavailable'})
        result = retrieve_for_review('current', tenant='a', principal='analyst',
                                     load_snapshot=lambda:{}, embed_fn=lambda _:[])
        self.assertEqual(result, {'status':'unavailable'})

    def test_changed_source_and_duplicate_ids_close_batch(self):
        for changed_record in (replace(self.passages[1], text='changed content'),
                               replace(self.passages[1], version='v2'),
                               replace(self.passages[1], source='other.txt')):
            changed = [changed_record if p.passage_id == 'current' else p for p in self.passages]
            snapshots = iter([{'passages':self.passages,'lifecycle':self.snapshot},
                              {'passages':changed,'lifecycle':self.snapshot}])
            result = retrieve_for_review('current', tenant='a', principal='analyst',
                                         load_snapshot=lambda:next(snapshots),
                                         embed_fn=lambda texts:[[1.0] for _ in texts])
            self.assertEqual(result, {'status':'unavailable'})
        duplicate = self.passages + [replace(self.passages[1], text='replacement')]
        snapshots = iter([{'passages':self.passages,'lifecycle':self.snapshot},
                          {'passages':duplicate,'lifecycle':self.snapshot}])
        result = retrieve_for_review('current', tenant='a', principal='analyst',
                                     load_snapshot=lambda:next(snapshots),
                                     embed_fn=lambda texts:[[1.0] for _ in texts])
        self.assertEqual(result, {'status':'unavailable'})

    def test_new_conflicting_current_version_closes_batch(self):
        records = [replace(p, version='v2') if p.passage_id == 'current' else p for p in self.passages]
        snapshots = iter([{'passages':records,'lifecycle':self.snapshot},
                          {'passages':records,'lifecycle':{**self.snapshot, 'old':'current'}}])
        result = retrieve_for_review('current', tenant='a', principal='analyst',
                                     load_snapshot=lambda:next(snapshots),
                                     embed_fn=lambda texts:[[1.0] for _ in texts])
        self.assertEqual(result, {'status':'unavailable'})

    def test_unknown_question_also_requires_human_review(self):
        result = retrieve_for_review('unknown', tenant='a', principal='analyst',
                                     load_snapshot=lambda:{'passages':self.passages,'lifecycle':self.snapshot},
                                     embed_fn=lambda texts:[[1.0] for _ in texts])
        self.assertEqual(result['status'], 'requires_human_review')
        self.assertNotIn('answer', result)

    def test_incomplete_or_changed_provenance_is_unavailable(self):
        def snap(provenance):
            return {'passages':self.passages,'lifecycle':self.snapshot,'provenance':provenance}
        complete = {'current':{'document_id':'source','source_sha256':'a'*64,'page_line':1,
                               'text_representation':'as_extracted'}}
        for before,after in (({}, {}), (complete, {})):
            snapshots = iter([snap(before),snap(after)])
            result = retrieve_for_review('current', tenant='a', principal='analyst',
                                         load_snapshot=lambda:next(snapshots),
                                         embed_fn=lambda texts:[[1.0] for _ in texts])
            self.assertEqual(result, {'status':'unavailable'})

    def test_malformed_citation_metadata_is_unavailable(self):
        valid = {'document_id':'source', 'source_sha256':'a'*64, 'page_line':1,
                 'text_representation':'as_extracted'}
        invalid = [('document_id', ''), ('document_id', None), ('source_sha256', 'not-a-hash'),
                   ('source_sha256', 'A'*64), ('page_line', 0), ('page_line', True),
                   ('page_line', '1'), ('text_representation', 'unknown')]
        for field, value in invalid:
            with self.subTest(field=field, value=value):
                provenance = {'current': {**valid, field:value}}
                snapshot = {'passages':self.passages, 'lifecycle':self.snapshot, 'provenance':provenance}
                result = retrieve_for_review('current', tenant='a', principal='analyst',
                                             load_snapshot=lambda:snapshot,
                                             embed_fn=lambda texts:[[1.0] for _ in texts])
                self.assertEqual(result, {'status':'unavailable'})


if __name__ == '__main__':
    unittest.main()
