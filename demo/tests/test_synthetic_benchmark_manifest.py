"""Synthetic metadata checks; no benchmark quality or source authority claim."""
from copy import deepcopy
import unittest

from nawa_demo.synthetic_benchmark_manifest import inspect_manifest


def fixture():
    return {'schema_version':1, 'documents':[
        {'id':'doc1','template_id':'layout1','language':'en','format':'digital_pdf',
         'split':'development','label_status':'draft','source_type':'synthetic'},
        {'id':'doc2','template_id':'layout2','language':'ar','format':'scanned_pdf',
         'split':'holdout','label_status':'reviewed','source_type':'synthetic'}],
        'queries':[{'id':'query1','language':'ar','split':'holdout','principal_fixture':'reviewer_a',
                    'answerable':True,'expected_document_ids':['doc2']},
                   {'id':'query2','language':'en','split':'holdout','principal_fixture':'reviewer_b',
                    'answerable':False,'expected_document_ids':[]}]}


class SyntheticBenchmarkManifestTests(unittest.TestCase):
    def test_reports_synthetic_counts_without_quality_claim(self):
        result = inspect_manifest(fixture())
        self.assertEqual(result['status'], 'metadata_valid')
        self.assertEqual(result['documents_by_language_and_format']['ar']['scanned_pdf'], 1)
        self.assertEqual(result['documents_by_split']['holdout'], 1)
        self.assertEqual(result['holdout_queries_by_language']['ar'], 1)
        self.assertEqual(result['draft_labels'], 1)
        self.assertIn('not verified', result['note'])

    def test_rejects_declared_template_leakage_and_duplicate_documents(self):
        data = fixture()
        data['documents'][1]['template_id'] = 'layout1'
        with self.assertRaises(ValueError):
            inspect_manifest(data)
        data = fixture()
        data['documents'].append(deepcopy(data['documents'][0]))
        with self.assertRaises(ValueError):
            inspect_manifest(data)

    def test_rejects_inconsistent_answerability_and_cross_split_source(self):
        for update in ({'answerable':False}, {'expected_document_ids':['doc1']},
                       {'expected_document_ids':['missing']}, {'answerable':'true'}):
            with self.subTest(update=update):
                data = fixture()
                data['queries'][0].update(update)
                with self.assertRaises(ValueError):
                    inspect_manifest(data)

    def test_rejects_unrecognized_or_non_synthetic_metadata(self):
        for update in ({'source_type':'real'}, {'label_status':'approved'}, {'language':[]},
                       {'id':'../outside'}, {'extra':'untrusted'}):
            with self.subTest(update=update):
                data = fixture()
                data['documents'][0].update(update)
                with self.assertRaises(ValueError):
                    inspect_manifest(data)


if __name__ == '__main__':
    unittest.main()
