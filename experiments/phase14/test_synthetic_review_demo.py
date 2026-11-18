import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from synthetic_review_demo import run_demo


class SyntheticReviewDemoTests(unittest.TestCase):
    def test_review_only_and_changed_sample_rejected(self):
        with TemporaryDirectory() as temp:
            demo=Path(temp)
            sample=demo/'samples'/'pdf'/'english_supplier.pdf'
            sample.parent.mkdir(parents=True)
            content=b'synthetic test fixture'
            sample.write_bytes(content)
            evidence={'evidence':{'total':{'source_text':'Grand total: AED 100',
                                           'method':'text_layer','page':1,'page_line':1}}}
            extract=lambda content,demo:evidence
            with patch('synthetic_review_demo.SAMPLE_SHA256',{hashlib.sha256(content).hexdigest()}):
                result=run_demo(demo,embedding_fn=lambda texts:[[1.0] for _ in texts],extraction_fn=extract)
                self.assertEqual(result['status'],'requires_human_review')
                self.assertEqual(result['evidence'][0]['untrusted_source_text'],'Grand total: AED 100')
                self.assertNotIn('answer',result)
                def change(texts):
                    sample.write_bytes(b'changed')
                    return [[1.0] for _ in texts]
                self.assertEqual(run_demo(demo,embedding_fn=change,extraction_fn=extract),
                                 {'status':'unavailable'})


if __name__=='__main__':
    unittest.main()

