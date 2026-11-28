import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from arabic_text_review_demo import run_demo


class ArabicTextReviewTests(unittest.TestCase):
    def test_source_line_and_changed_fixture(self):
        with TemporaryDirectory() as directory:
            demo=Path(directory)
            sample=demo/'samples'/'arabic_quote.txt'
            sample.parent.mkdir()
            content='الإجمالي: ٩٤٥'.encode('utf-8')
            sample.write_bytes(content)
            fake={'evidence':{'total':{'line':1,'source_text':'الإجمالي: ٩٤٥'}}}
            with patch('arabic_text_review_demo.SAMPLE_SHA256',{hashlib.sha256(content).hexdigest()}):
                result=run_demo(demo,embedding_fn=lambda texts:[[1.0] for _ in texts],
                                extraction_fn=lambda content,demo:fake)
                self.assertEqual(result['status'],'requires_human_review')
                self.assertEqual(result['evidence'][0]['line'],1)
                self.assertEqual(result['evidence'][0]['untrusted_source_text'],'الإجمالي: ٩٤٥')
                self.assertNotIn('page',result['evidence'][0])
                def change(texts):
                    sample.write_bytes(b'changed')
                    return [[1.0] for _ in texts]
                self.assertEqual(run_demo(demo,embedding_fn=change,
                                          extraction_fn=lambda content,demo:fake),{'status':'unavailable'})


if __name__=='__main__':
    unittest.main()

