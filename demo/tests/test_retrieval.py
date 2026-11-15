"""Phase 4 synthetic retrieval, evidence, and isolation regression tests."""
import json
from pathlib import Path
import unittest

from nawa_demo.retrieval import Passage, BM25Index, read_corpus, tokenize, pdf_page_passages
from nawa_demo.retrieval_cli import evaluate

BASE=Path(__file__).resolve().parents[1]
CORPUS=BASE/'samples/retrieval/passages.json'
CASES=BASE/'samples/retrieval/evaluation.json'

class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.passages=read_corpus(CORPUS)

    def test_normalizes_arabic_indic_digits(self):
        self.assertEqual(tokenize('٩٤٥ Example'),['945','example'])

    def test_english_retrieval_with_page_evidence(self):
        idx=BM25Index(self.passages,tenant_id='demo-a',principal_id='reviewer-a')
        hits=idx.search('English Supplies 1050')
        self.assertEqual(hits[0]['passage_id'],'en-quote-v1-p1')
        self.assertEqual((hits[0]['page'],hits[0]['source']),(1,'english_supplier.pdf'))

    def test_arabic_retrieval(self):
        hits=BM25Index(self.passages,tenant_id='demo-a',principal_id='reviewer-a').search('شركة المثال الضريبة ٤٥')
        self.assertEqual(hits[0]['passage_id'],'ar-quote-v1-p1')

    def test_restricted_text_never_returned(self):
        hits=BM25Index(self.passages,tenant_id='demo-a',principal_id='reviewer-a').search('Falcon Robotics confidential inspection')
        self.assertEqual(hits,[])

    def test_tenant_isolation_even_if_same_principal(self):
        hits=BM25Index(self.passages,tenant_id='demo-a',principal_id='reviewer-a').search('Exclusive tenant B satellite Orion')
        self.assertEqual(hits,[])

    def test_missing_access_context_denied(self):
        with self.assertRaisesRegex(ValueError,'fail closed'):
            BM25Index(self.passages,tenant_id='demo-a',principal_id='')

    def test_invalid_corpus_acl_rejected(self):
        row={'passage_id':'x','document_id':'d','version':'v1','tenant_id':'t','page':1,'text':'secret','allowed_principals':[],'source':'x.pdf'}
        with self.assertRaisesRegex(ValueError,'ACL'):
            Passage.from_dict(row)

    def test_no_matching_terms_returns_empty(self):
        idx=BM25Index(self.passages,tenant_id='demo-a',principal_id='reviewer-a')
        self.assertEqual(idx.search('interplanetary antimatter quantum'),[])

    def test_repeatable_ranking(self):
        idx=BM25Index(self.passages,tenant_id='demo-a',principal_id='reviewer-a')
        self.assertEqual(idx.search('VAT reviewer'),idx.search('VAT reviewer'))

    def test_recall_evaluation(self):
        report=evaluate(CORPUS,CASES)
        self.assertEqual(report['case_count'],3)
        self.assertEqual(report['score'],1.0)

    def test_evaluation_rejects_unauthorized_ground_truth(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td:
            data=[{'query':'Falcon','tenant_id':'demo-a','principal_id':'reviewer-a','relevant_passage_ids':['restricted-v1-p1']}]
            f=Path(td)/'bad.json';f.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'unauthorized'):
                evaluate(CORPUS,f)

    def test_pdf_page_level_ingest(self):
        import pymupdf
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td:
            pdf=Path(td)/'sample.pdf'
            doc=pymupdf.open()
            doc.new_page()
            page=doc.new_page()
            page.insert_text((72,72),'Example Page Two Supplies')
            doc.save(pdf)
            doc.close()
            passages=pdf_page_passages(pdf,document_id='p2',version='v1',tenant_id='demo-a',allowed_principals=['reviewer-a'])
            self.assertEqual(len(passages),1)
            self.assertEqual(passages[0].page,2)
            result=BM25Index(passages,tenant_id='demo-a',principal_id='reviewer-a').search('Example Page Two Supplies')
            self.assertEqual(result[0]['page'],2)

if __name__=='__main__':
    unittest.main()
