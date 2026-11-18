import unittest
from copy import deepcopy
from dataclasses import replace

from hybrid_review import retrieve_for_review
from resolve_review_evidence import resolve_for_review
from retrieval import Passage


class ResolveReviewEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.passage = Passage('p','family','1','a',2,'Untrusted source line',('analyst',),
                               'synthetic.pdf','text_layer')
        self.snapshot = {'passages':[self.passage], 'lifecycle':{'p':'current'},
                         'provenance':{'p':{'document_id':'source','source_sha256':'a'*64,'page_line':4,
                                            'text_representation':'as_extracted'}}}
        self.load = lambda:self.snapshot
        self.review = retrieve_for_review('source',tenant='a',principal='analyst',
                                          load_snapshot=self.load,embed_fn=lambda texts:[[1.0] for _ in texts])

    def test_returns_untrusted_text_for_human_review(self):
        result = resolve_for_review(self.review,tenant='a',principal='analyst',load_snapshot=self.load)
        self.assertEqual(result['status'],'requires_human_review')
        self.assertEqual(result['evidence'][0]['untrusted_source_text'],'Untrusted source line')
        self.assertNotIn('approval',result)

    def test_rejects_revoked_changed_and_forged_citations(self):
        changed = deepcopy(self.snapshot)
        changed['lifecycle']['p'] = 'revoked'
        self.assertEqual(resolve_for_review(self.review,tenant='a',principal='analyst',
                                            load_snapshot=lambda:changed),{'status':'unavailable'})

        changed = deepcopy(self.snapshot)
        changed['provenance']['p']['page_line'] = 5
        self.assertEqual(resolve_for_review(self.review,tenant='a',principal='analyst',
                                            load_snapshot=lambda:changed),{'status':'unavailable'})

        forged = deepcopy(self.review)
        forged['evidence'][0]['source_sha256'] = 'b'*64
        self.assertEqual(resolve_for_review(forged,tenant='a',principal='analyst',
                                            load_snapshot=self.load),{'status':'unavailable'})
        self.assertEqual(resolve_for_review(self.review,tenant='a',principal='other',
                                            load_snapshot=self.load),{'status':'unavailable'})
        changed = deepcopy(self.snapshot)
        changed['passages'] = [replace(self.passage, text='Changed source line')]
        self.assertEqual(resolve_for_review(self.review,tenant='a',principal='analyst',
                                            load_snapshot=lambda:changed),{'status':'unavailable'})

    def test_normalized_text_is_not_labeled_as_verbatim(self):
        self.snapshot['provenance']['p']['text_representation']='normalized'
        review=retrieve_for_review('source',tenant='a',principal='analyst',
                                   load_snapshot=self.load,embed_fn=lambda texts:[[1.0] for _ in texts])
        result=resolve_for_review(review,tenant='a',principal='analyst',load_snapshot=self.load)
        self.assertEqual(result['evidence'][0]['untrusted_normalized_text'],'Untrusted source line')
        self.assertNotIn('untrusted_source_text',result['evidence'][0])


if __name__ == '__main__':
    unittest.main()

