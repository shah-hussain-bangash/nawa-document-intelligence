import unittest

from new_eval_probe import evaluate
from retrieval import Passage


class NewEvaluationTests(unittest.TestCase):
    def test_evaluates_answerable_and_unknown_without_embedding_unauthorized_text(self):
        passages=[Passage('a','a','v1','demo-a',1,'chair',('analyst-a',),'a','synthetic'),
                  Passage('b','b','v1','demo-b',1,'secret',('analyst-a',),'b','synthetic')]
        cases=[{'id':'q1','language':'en','kind':'answerable','query':'chair','relevant':['a']},
               {'id':'q2','language':'en','kind':'unanswerable','query':'unknown','relevant':[]}]
        seen=[]
        def fake(texts):
            seen.extend(texts)
            return [[1.0] for _ in texts]
        result=evaluate(passages,cases,fake)
        self.assertNotIn('secret',seen)
        self.assertEqual(result['methods']['hybrid']['recall_at_5'],1.0)
        self.assertEqual(result['methods']['vector']['unanswerable_with_candidates'],1)
        with self.assertRaises(ValueError):
            evaluate(passages,[{**cases[0],'relevant':['b']}],fake)


if __name__=='__main__':
    unittest.main()

